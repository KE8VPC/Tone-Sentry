"""Convert the approved artwork to application icon formats (requires Pillow)."""
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]
with Image.open(root/'assets/icon-original.png') as original:
    icon=original.convert('RGBA')
    icon.save(root/'tonepage/resources/app-icon.ico',format='ICO',sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
    icon.resize((256,256),Image.Resampling.LANCZOS).save(root/'tonepage/resources/app-icon.png')
