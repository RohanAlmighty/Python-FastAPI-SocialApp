from .auth import get_current_user
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
    prefix="/users", tags=["users"], responses={404: {"description": "not found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/{username}", response_class=HTMLResponse)
async def view_user_profile(
    request: Request, username: str, db: Session = Depends(get_db)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    user_follows = (
        db.query(models.Socials)
        .filter(models.Socials.user_id == user.get("id"))
        .filter(models.Socials.follows_id == user_profile.id)
        .first()
    )

    if user_follows is None:
        user_follows_flag = False
    else:
        user_follows_flag = True

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "user_profile": user_profile,
            "user_follows_flag": user_follows_flag,
        },
    )


@router.post("/follow/{username}", response_class=HTMLResponse)
async def follow_user(request: Request, username: str, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    socials_model = models.Socials()
    socials_model.user_id = user.get("id")
    socials_model.follows_id = user_profile.id

    db.add(socials_model)
    db.commit()

    return RedirectResponse(url=f"/users/{username}", status_code=status.HTTP_302_FOUND)


@router.post("/unfollow/{username}", response_class=HTMLResponse)
async def unfollow_user(request: Request, username: str, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.username == username).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    user_follows = (
        db.query(models.Socials)
        .filter(models.Socials.user_id == user.get("id"))
        .filter(models.Socials.follows_id == user_profile.id)
        .first()
    )

    db.delete(user_follows)
    db.commit()

    return RedirectResponse(url=f"/users/{username}", status_code=status.HTTP_302_FOUND)
