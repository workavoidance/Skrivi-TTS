"""One-time local copy into permanent storage. No network calls or deletions."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import Library, catalog, read_json

def main():
    library = Library()
    downloads = Path.home() / 'Downloads'
    old_piper = downloads / 'Norwegian_TTS_Model_Shootout_v5' / 'Norwegian_TTS_Model_Shootout_v5' / 'models' / 'piper'
    candidates = {'voxcpm-q4': Path(os.environ['LOCALAPPDATA']) / 'VoxCPM2ReaderPOC' / 'models',
                  'piper-nvcc': old_piper, 'piper-talesyntese': old_piper}
    for config_path in downloads.glob('Norwegian_TTS_Shootout_*/local-paths.json'):
        config = read_json(config_path)
        if config.get('lab_root'):
            candidates['chatterbox-q4'] = Path(config['lab_root']) / 'models' / 'chatterbox-q4'
    for model in catalog():
        if library.ready(model):
            print('Already installed:', model['name'], flush=True)
        elif (source := candidates.get(model['id'])) and source.exists():
            library.install(model, lambda value: print(value, flush=True), source=source)
            print('Imported:', model['name'], flush=True)
        else:
            print('Not found locally:', model['name'], flush=True)

if __name__ == '__main__':
    main()
