"""Explicit, metadata-only update check. Never called on startup."""
import json,re,urllib.request
URL='https://api.github.com/repos/workavoidance/Skrivi-TTS/releases/latest'
def latest(current):
 request=urllib.request.Request(URL,headers={'Accept':'application/vnd.github+json','User-Agent':'Skrivi-TTS'})
 with urllib.request.urlopen(request,timeout=15) as response:
  data=json.loads(response.read(1024*1024))
 version=data.get('tag_name','').removeprefix('v')
 if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('The release service returned an unexpected version.')
 newer=tuple(map(int,version.split('.')))>tuple(map(int,current.split('.')))
 return version,newer
