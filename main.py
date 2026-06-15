from fastapi import FastAPI
from core.database import Base, engine
from routers import user, blog, task, file,product
from middleware.auth_middleware import AuthMiddleware
app = FastAPI(title="Auth API")
app.add_middleware(AuthMiddleware)
app.include_router(user.router)
app.include_router(blog.router)
app.include_router(task.router)
app.include_router(file.router)
app.include_router(product.router) 
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)