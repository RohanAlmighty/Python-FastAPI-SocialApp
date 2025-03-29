from .auth import get_current_user
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from fastapi import Depends, APIRouter, Request, Form

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from starlette import status
from pytz import timezone, UTC

import sys

sys.path.append("..")

IST = timezone("Asia/Kolkata")

router = APIRouter(
    prefix="/posts", tags=["posts"], responses={404: {"description": "not found"}}
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
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_self = db.query(models.Users).filter(models.Users.id == user.get("id")).all()
    posts_self = (
        db.query(models.Posts).filter(models.Posts.owner_id == user.get("id")).order_by(models.Posts.updated_at.desc()).all()
    )

    user_follows = (
        db.query(models.Socials).filter(models.Socials.user_id == user.get("id")).all()
    )

    user_follows_details = list()
    user_follows_posts = list()

    for users_followed in user_follows:
        user_follows_details.append(
            db.query(models.Users)
            .filter(models.Users.id == users_followed.follows_id)
            .all()
        )
        user_follows_posts.append(
            db.query(models.Posts)
            .filter(models.Posts.owner_id == users_followed.follows_id)
            .all()
        )

    try:
        for post in posts_self:
            if post.updated_at.tzinfo is None:
                post.updated_at = UTC.localize(post.updated_at)
            post.updated_at = post.updated_at.astimezone(IST).strftime("%I:%M %p %d %b %Y")
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "user_self": user_self,
                "posts_self": posts_self,
                "user_follows": user_follows,
                "user_follows_details": user_follows_details,
                "user_follows_posts": user_follows_posts,
                "user": user,
            },
        )
    except UnboundLocalError:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "user_self": user_self,
                "posts_self": posts_self,
                "user": user,
            },
        )


@router.get("/create-post", response_class=HTMLResponse)
async def create_new_post(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "create-post.html", {"request": request, "user": user}
    )


@router.post("/create-post", response_class=HTMLResponse)
async def create_post(
    request: Request,
    post_body: str = Form(...),
    db: Session = Depends(get_db),
):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    posts_model = models.Posts()
    posts_model.post_body = post_body
    posts_model.owner_id = user.get("id")

    db.add(posts_model)
    db.commit()

    return RedirectResponse(url="/posts", status_code=status.HTTP_302_FOUND)


@router.get("/edit-post/{post_id}", response_class=HTMLResponse)
async def edit_post(request: Request, post_id: int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    if post.owner_id != user["id"]:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    return templates.TemplateResponse(
        "edit-post.html", {"request": request, "post": post, "user": user}
    )


@router.post("/edit-post/{post_id}", response_class=HTMLResponse)
async def edit_post_commit(
    request: Request,
    post_id: int,
    post_body: str = Form(...),
    db: Session = Depends(get_db),
):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    posts_model = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    posts_model.post_body = post_body

    db.add(posts_model)
    db.commit()

    return RedirectResponse(url="/posts", status_code=status.HTTP_302_FOUND)


@router.get("/delete-post/{post_id}")
async def delete_post_commit(
    request: Request, post_id: int, db: Session = Depends(get_db)
):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    posts_model = (
        db.query(models.Posts)
        .filter(models.Posts.id == post_id)
        .filter(models.Posts.owner_id == user.get("id"))
        .first()
    )

    if posts_model is None:
        return RedirectResponse(
            url="/auth/page-not-found", status_code=status.HTTP_302_FOUND
        )

    db.query(models.Posts).filter(models.Posts.id == post_id).delete()
    db.commit()

    return RedirectResponse(url="/posts", status_code=status.HTTP_302_FOUND)
