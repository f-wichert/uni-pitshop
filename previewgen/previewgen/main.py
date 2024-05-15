import os
import shutil
import tempfile

from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse

from . import util

app = FastAPI()


@app.get("/")
def root() -> str:
    return "OK"


@app.post("/render")
def render(file: UploadFile) -> StreamingResponse:
    ext = os.path.splitext(file.filename)[1]
    try:
        with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp.seek(0)
            rendered = util.render_file(tmp.name)

        return StreamingResponse(rendered, media_type="image/png")
    finally:
        file.file.close()
