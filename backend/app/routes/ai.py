import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.deps import get_current_user
from app.models import User
from app.services import ai_service
from app.utils.uploads import validate_image_bytes

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def ai_status(_: User = Depends(get_current_user)):
    return ai_service.status()


@router.post("/analyze")
async def analyze(image: UploadFile = File(...), _: User = Depends(get_current_user)):
    """Preview the AI result for a photo without creating a report."""
    data, suffix = await validate_image_bytes(image)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(data)
        result = await run_in_threadpool(ai_service.analyze_image, str(path))
    st = ai_service.status()
    if result is None:
        return {**st, "detected": False, "result": None}
    return {**st, "detected": True, "result": result.to_dict()}
