from fastapi import FastAPI

import models
from database import engine
from routers import auth, posts, users, search
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/posts", status_code=status.HTTP_302_FOUND)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(search.router)
