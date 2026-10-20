"""JPG thumbnail generation, isolated from the GUI process."""
import base64, os, tempfile
from pathlib import Path

def render_cover(path,cache,maximum=450):
    import pymupdf
    cache=Path(cache)
    try:
        if not cache.exists():
            with pymupdf.open(path) as doc:
                page=doc[0];scale=min(maximum*2/3/max(1,page.rect.width),maximum/max(1,page.rect.height))
                pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False,colorspace=pymupdf.csRGB)
                jpg=pix.tobytes('jpeg',jpg_quality=95 if maximum>450 else 85)
            cache.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(dir=cache.parent,suffix='.tmp')
            try:
                with os.fdopen(fd,'wb') as f:f.write(jpg)
                os.replace(tmp,cache)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
        return 'data:image/jpeg;base64,'+base64.b64encode(cache.read_bytes()).decode()
    except Exception:return ''
