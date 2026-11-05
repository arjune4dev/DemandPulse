import hmac
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse


DATA_DIR = Path(os.environ.get("DEMANDPULSE_DATA_DIR", "/var/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_FILES = {"train.csv", "store.csv"}
MAX_FILE_BYTES = 250 * 1024 * 1024

app = FastAPI(
    title="DemandPulse Private Data Store",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def authorize_data_service(supplied_token):
    expected_token = os.environ.get("DATA_SERVICE_TOKEN", "")
    if not expected_token or not hmac.compare_digest(
        supplied_token or "", expected_token
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


def dataset_path(filename):
    if filename not in ALLOWED_FILES:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    return DATA_DIR / filename


@app.get("/health")
def health():
    return {"status": "healthy", "service": "DemandPulse private data store"}


@app.get("/files/{filename}")
def get_dataset(filename: str, x_data_token: str = Header(default="")):
    authorize_data_service(x_data_token)
    path = dataset_path(filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Dataset file not uploaded")
    return FileResponse(path, media_type="text/csv", filename=filename)


@app.put("/files/{filename}")
async def put_dataset(
    filename: str,
    request: Request,
    x_data_token: str = Header(default=""),
):
    authorize_data_service(x_data_token)
    path = dataset_path(filename)
    temporary_path = path.with_suffix(path.suffix + ".uploading")
    total_bytes = 0

    try:
        with temporary_path.open("wb") as target:
            async for chunk in request.stream():
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Dataset file exceeds the 250 MB upload limit",
                    )
                target.write(chunk)

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return {"status": "saved", "filename": filename, "bytes": total_bytes}
