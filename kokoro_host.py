"""Separate frozen Kokoro dependencies; weights stay in the permanent library."""
import runpy
import sys
from pathlib import Path
import numpy, onnxruntime, soundfile, psutil
import kokoro_onnx
from misaki import en, espeak
import en_core_web_sm
import spacy
import wave, contextlib, hashlib, json, subprocess, threading, queue, urllib.request
if __name__=='__main__':
    script=Path(sys.argv[1]).resolve()
    sys.path.insert(0,str(script.parent))
    sys.argv=sys.argv[1:]
    runpy.run_path(str(script),run_name='__main__')
