"""Generate Windows product metadata from the application version."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'app/core.py').read_text(encoding="utf-8"))
version = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign) and any(
                   isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets))
parts = tuple(map(int, version.split("."))) + (0,)
assert len(parts) == 4
strings = {"CompanyName": "Skrivi", "FileDescription": 'Skrivi Lytt',
           "ProductName": 'Skrivi Lytt', "FileVersion": version,
           "ProductVersion": version, "OriginalFilename": 'SkriviTTS.exe'}
entries = ",".join(f"StringStruct({key!r}, {value!r})" for key, value in strings.items())
value = f"VSVersionInfo(ffi=FixedFileInfo(filevers={parts!r}, prodvers={parts!r}, mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0,0)), kids=[StringFileInfo([StringTable('040904B0',[{entries}])]), VarFileInfo([VarStruct('Translation',[1033,1200])])])"
(ROOT / "build").mkdir(exist_ok=True)
(ROOT / "build/version-info.txt").write_text(value, encoding="utf-8")
