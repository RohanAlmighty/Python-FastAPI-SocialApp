from .auth import get_current_user
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from fastapi import Depends, APIRouter, Request, Form

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from starlette import status

import sys

sys.path.append("..")


router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "not found"}},
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def search_page(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "user-search.html", {"request": request, "user": user}
    )


@router.post("/", response_class=HTMLResponse)
async def search_user(
    request: Request,
    search: str = Form(...),
    db: Session = Depends(get_db),
):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    search = search.lower()
    search_result = (
        db.query(models.Users)
        .filter(
            or_(
                func.lower(models.Users.username).contains(search),
                func.lower(models.Users.first_name).contains(search),
                func.lower(models.Users.last_name).contains(search),
            )
        )
        .all()
    )

    return templates.TemplateResponse(
        "user-search.html",
        {"request": request, "user": user, "search_result": search_result},
    )
