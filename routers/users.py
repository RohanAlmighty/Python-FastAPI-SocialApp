from .auth import get_current_user, verify_password, get_password_hash
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
    user_follows_count = (
        db.query(models.Socials)
        .filter(models.Socials.user_id == user_profile.id)
        .count()
    )
    user_follower_count = (
        db.query(models.Socials)
        .filter(models.Socials.follows_id == user_profile.id)
        .count()
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
            "user_follows_count": user_follows_count,
            "user_follower_count": user_follower_count,
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


@router.get("/password/edit", response_class=HTMLResponse)
async def edit_password(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "edit-user-password.html", {"request": request, "user": user}
    )


@router.post("/password/edit", response_class=HTMLResponse)
async def user_password_commit(
    request: Request,
    password: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_data = db.query(models.Users).filter(models.Users.id == user.get("id")).first()

    msg = "Wrong password"

    if user_data is not None:
        if verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_password_hash(password2)

            db.add(user_data)
            db.commit()
            msg = "Password updated"

    return templates.TemplateResponse(
        "edit-user-password.html", {"request": request, "user": user, "msg": msg}
    )


@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    return templates.TemplateResponse(
        "edit-user-profile.html",
        {"request": request, "user": user, "user_profile": user_profile},
    )


@router.post("/profile/edit", response_class=HTMLResponse)
async def edit_profile_commit(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    firstname: str = Form(...),
    lastname: str = Form(...),
    bio: str = Form(...),
    db: Session = Depends(get_db),
):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    # validation1 = db.query(models.Users).filter(models.Users.email == email).first()
    # validation2 = (
    #     db.query(models.Users).filter(models.Users.username == username).first()
    # )

    # if validation1 is not None or validation2 is not None:
    #     msg = "Email or Username already exists"
    #     return templates.TemplateResponse(
    #         "edit-user-profile.html",
    #         {"request": request, "msg": msg, "user_profile": user_profile},
    #     )

    # user_profile.username = username
    # user_profile.email = email
    user_profile.first_name = firstname
    user_profile.last_name = lastname
    user_profile.bio = bio

    db.add(user_profile)
    db.commit()

    return RedirectResponse(url=f"/users/{username}", status_code=status.HTTP_302_FOUND)


@router.get("/profile/my-profile", response_class=HTMLResponse)
async def my_profile(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_profile = (
        db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    )
    if user_profile is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    return RedirectResponse(
        url=f"/users/{user_profile.username}", status_code=status.HTTP_302_FOUND
    )
