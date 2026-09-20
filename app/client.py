"""Owned persistent worker with cancellable response waiting."""
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from core import ROOT, DATA, runtime_executable

class Client:
    def __init__(self):
        self.process = None
        self.runtime_profile = None
        self.responses = queue.Queue()

    def stop(self):
        process, self.process = self.process, None
        if process and process.poll() is None:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
            process.wait(timeout=15)

    def start(self, engine=None):
        profile = 'kokoro-engine-v1' if engine == 'kokoro' else 'python-engine-v1'
        if self.process and self.process.poll() is None:
            if self.runtime_profile == profile:
                return
            self.stop()
        self.runtime_profile = profile
        self.responses = queue.Queue()
        runtime = runtime_executable(profile, 'KokoroWorker.exe' if engine == 'kokoro' else 'SkriviWorker.exe')
        if runtime.exists():
            command = [str(runtime), str(ROOT / 'engines' / 'worker.py')]
        elif not getattr(sys, 'frozen', False):
            command = [sys.executable, str(ROOT / 'engines' / 'worker.py')]
        else:
            raise RuntimeError('Engine runtime is missing. Run the full installer once; your models are preserved.')
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        self.process = process
        responses = self.responses
        def read():
            try:
                for line in process.stdout:
                    responses.put(json.loads(line))
            except Exception:
                responses.put({'ok': False, 'error': 'The engine returned an invalid response.'})
            finally:
                responses.put({'ok': False, 'error': 'Engine stopped before completing the audio.'})
        threading.Thread(target=read, daemon=True).start()

    def generate(self, request, cancel, progress=None):
        profile = 'kokoro-engine-v1' if request['model']['engine']=='kokoro' else 'python-engine-v1'
        if progress and not (self.process and self.process.poll() is None and self.runtime_profile==profile):progress('starting')
        if progress:request=dict(request,progress_events=True)
        self.start(request['model']['engine'])
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        started = time.monotonic()
        while True:
            if cancel.is_set():
                self.stop()
                raise InterruptedError('Stopped')
            if time.monotonic() - started > 1800:
                self.stop()
                raise TimeoutError('Generation exceeded 30 minutes; the model was unloaded.')
            try:
                response = self.responses.get(timeout=0.1)
            except queue.Empty:
                continue
            if 'event' in response:
                if progress:progress(response['event'])
                continue
            if not response['ok']:
                raise RuntimeError(response['error'])
            return response['result']
