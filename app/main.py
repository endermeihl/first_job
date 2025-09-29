from fastapi import FastAPI
from . import models
from .database import engine
from .routers import items

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="My Awesome API",
    description="This is a very fancy project, with auto docs for the API and everything",
    version="1.0.1",
)

app.include_router(items.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"Hello": "World"}
