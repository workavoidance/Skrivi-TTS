import io,json,sys,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from client import Client
from updates import latest

class ReleaseTests(unittest.TestCase):
 def test_progress_events_do_not_replace_final_response(self):
  c=Client();c.process=Mock();c.process.poll.return_value=None;c.process.stdin=io.StringIO();c.runtime_profile='python-engine-v1'
  for response in ({'event':'loading'},{'event':'generating'},{'ok':True,'result':{'audio_seconds':1}}):c.responses.put(response)
  events=[]
  with patch.object(c,'start'):
   result=c.generate({'model':{'engine':'piper'}},threading.Event(),events.append)
  self.assertEqual(events,['loading','generating']);self.assertEqual(result['audio_seconds'],1)
  self.assertTrue(json.loads(c.process.stdin.getvalue())['progress_events'])
 def test_legacy_client_response_still_works(self):
  c=Client();c.process=Mock();c.process.poll.return_value=None;c.process.stdin=io.StringIO();c.responses.put({'ok':True,'result':42})
  with patch.object(c,'start'):self.assertEqual(c.generate({'model':{'engine':'piper'}},threading.Event()),42)
  self.assertNotIn('progress_events',json.loads(c.process.stdin.getvalue()))
 def test_cancel_stops_progress_wait(self):
  c=Client();c.process=Mock();c.process.stdin=io.StringIO();event=threading.Event();event.set()
  with patch.object(c,'start'),patch.object(c,'stop') as stop:
   with self.assertRaises(InterruptedError):c.generate({'model':{'engine':'piper'}},event)
   stop.assert_called_once()
 def test_update_check_only_reads_metadata(self):
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=b'[{"tag_name":"v0.5.0","prerelease":true}]'
  with patch('urllib.request.urlopen',return_value=response) as call:
   self.assertEqual(latest('0.4.0'),('0.5.0',True));self.assertEqual(call.call_count,1)
 def test_store_has_no_microphone_capability(self):
  text=(ROOT/'store/AppxManifest.xml').read_text(encoding='utf-8')
  self.assertNotIn('microphone',text);self.assertIn('runFullTrust',text);self.assertIn('Enabled="false"',text)
if __name__=='__main__':unittest.main()
