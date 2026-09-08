"""Frozen dependency host; versioned application engine code remains replaceable."""
import runpy
import sys
from pathlib import Path
# Explicit imports make the reusable frozen dependency runtime self-contained.
import numpy
import onnxruntime
import tokenizers
import piper
import soundfile
import psutil
import wave
import contextlib
import hashlib
import json
import subprocess
import threading
import queue
import urllib.request
if __name__ == '__main__':
    script = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(script.parent))
    sys.argv = sys.argv[1:]
    runpy.run_path(str(script), run_name='__main__')
