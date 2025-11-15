from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from . import models
from .database import engine
from .routers import items, tasks, videos, auth, favorites
from .config import settings
import os

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="功能完整的小红书视频下载工具,支持单视频下载、批量下载、收藏夹管理等功能",
    version=settings.APP_VERSION,
)

# 注册路由
app.include_router(tasks.router)
app.include_router(videos.router)
app.include_router(auth.router)
app.include_router(favorites.router)
app.include_router(items.router)  # 保留示例路由

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def read_root():
    """首页 - Web管理界面"""
    html_file = os.path.join(os.path.dirname(__file__), "static", "index.html")

    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        <html>
            <head>
                <title>小红书视频下载工具</title>
            </head>
            <body>
                <h1>小红书视频下载工具</h1>
                <p>API文档: <a href="/docs">/docs</a></p>
                <p>Web界面开发中...</p>
            </body>
        </html>
        """


@app.get("/health", tags=["Root"])
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
