from fastapi import APIRouter

from app.version import VERSION

router = APIRouter(prefix="/api")


@router.get("/version")
def version():
    return {"version": VERSION}
