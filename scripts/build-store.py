"""Build Store MSIX from the signed payload; do not invent a submission identity."""
import argparse,json,shutil,subprocess,sys,os,re,html
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from core import VERSION
p=argparse.ArgumentParser();p.add_argument('--identity',type=Path);p.add_argument('--validation-only',action='store_true');p.add_argument('--build',type=int,default=1);p.add_argument('--makeappx',type=Path,help='Optional SDK MakeAppx path');args=p.parse_args()
if args.identity:
 identity=json.loads(args.identity.read_text(encoding='utf-8'))
 if not re.fullmatch(r'[A-Za-z0-9.-]{3,50}',identity['name']) or not identity['publisher'].startswith('CN=') or not identity['publisher_display_name'].strip():raise ValueError('Invalid Store product identity')
 if any('COPY ' in str(v) for v in identity.values()):raise ValueError('Provide the real reserved TTS product identity')
elif args.validation_only:
 identity=dict(name='SkriviTTS.Unassociated',publisher='CN=Skrivi TTS Local Validation',publisher_display_name='Skrivi TTS - UNASSOCIATED')
else:raise SystemExit('Reserve the TTS Store listing and provide --identity. Use --validation-only solely for an unassociated packaging check.')
if not 1<=args.build<=65535:raise ValueError('Store build must be 1..65535')
stage=root/'build/store-payload'
if stage.exists():raise SystemExit('Store staging exists; use a fresh directory.')
source=root/'build/release-payload'
for name in ('app','models','runtimes'):shutil.copytree(source/name,stage/name)
(stage/'app/store-build.json').write_text(json.dumps(dict(store=True,associated=not args.validation_only)),encoding='utf-8')
version=f"{int(VERSION.split('.')[0])+1}.{VERSION.split('.')[1]}.{args.build}.0"
s=(root/'store/AppxManifest.xml').read_text(encoding='utf-8')
for key,value in {'__NAME__':identity['name'],'__PUBLISHER__':identity['publisher'],'__DISPLAY__':identity['publisher_display_name'],'__VERSION__':version}.items():s=s.replace(key,html.escape(value,quote=True))
(stage/'AppxManifest.xml').write_text(s,encoding='utf-8')
from PySide6.QtWidgets import QApplication
from branding import speech_icon
app=QApplication([]);assets=stage/'Assets';assets.mkdir()
for name,size in [('StoreLogo',50),('Square44x44Logo',44),('Square150x150Logo',150)]:
 if not speech_icon().pixmap(size,size).save(str(assets/(name+'.png'))):raise RuntimeError('Store logo failed')
kits=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Windows Kits/10/bin'
tools=[args.makeappx.resolve()] if args.makeappx else sorted(kits.glob('*/x64/makeappx.exe'))
if not tools:raise SystemExit('Windows SDK MakeAppx is required')
out=root/'dist/store';out.mkdir(parents=True,exist_ok=True)
name='Skrivi-Lytt-'+VERSION+'-windows-x64'+('-UNASSOCIATED-validation' if args.validation_only else '')+'.msix'
subprocess.run([str(tools[-1]),'pack','/d',str(stage),'/p',str(out/name),'/o'],check=True)
(out/'PACKAGE-STATUS.txt').write_text(('NOT FOR UPLOAD: reserve the separate TTS listing, provide its identity, and rebuild.\n' if args.validation_only else 'Store-associated package. Upload through Partner Center; the Store signs the MSIX.\n')+'Built package version: '+version+'\nCertification has not been run.\n',encoding='utf-8')
print(out/name)
