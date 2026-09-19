"""Offline, one-request OCR worker. Image bytes and recognised text use pipes only."""
import io,json,sys
from pathlib import Path
from PIL import Image,ImageOps
import tesserocr

def main():
    root=Path(sys.argv[1])
    for lang in ('nor','eng'):
        if not (root/(lang+'.traineddata')).is_file():raise RuntimeError('OCR language files are missing. Reinstall the OCR update.')
    payload=sys.stdin.buffer.read(32*1024*1024+1)
    if len(payload)>32*1024*1024:raise ValueError('Select a smaller region.')
    im=Image.open(io.BytesIO(payload));im.load()
    if im.width*im.height>20000000:raise ValueError('Select a smaller region.')
    im=im.convert('RGB')
    # Normalise dark documents, without changing spelling or inferred words.
    gray=ImageOps.grayscale(im)
    if gray.resize((1,1)).getpixel((0,0))<110:im=ImageOps.invert(im)
    im=ImageOps.expand(im,border=16,fill='white')
    with tesserocr.PyTessBaseAPI(path=str(root),lang='nor+eng',psm=6) as api:
        api.SetImage(im)
        text=api.GetUTF8Text().strip()
    sys.stdout.buffer.write(json.dumps({'text':text},ensure_ascii=False).encode('utf-8'))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        sys.stdout.buffer.write(json.dumps({'error':str(exc)}).encode('utf-8'));sys.exit(1)
