from fastapi import APIRouter

from app.admin.auth.routers import router as auth_admin_user_router
from app.interface.routers import router as interface_routers
from app.language.routers import router as language_router
from app.lesson.routers import admin_router as lesson_admin_router
from app.lesson.routers import router as lesson_router
from app.topic.routers import admin_router as topic_admin_router
from app.user.auth.routers import router as auth_user_router
from app.user.routers import admin_router as admin_avatar_router
from app.user.routers import router as user_router

v1 = APIRouter()

# ===== Super User Auth ===== #
v1.include_router(auth_admin_user_router, tags=["Super User Auth"])

# ===== User Auth ===== #
v1.include_router(auth_user_router, tags=["User Auth"])

# ===== User Auth ===== #
v1.include_router(user_router, tags=["User"])

# ===== Avatars ===== #
v1.include_router(admin_avatar_router, tags=["Avatar"])

# ===== Lessons ===== #
v1.include_router(lesson_router, tags=["Lesson"])
v1.include_router(lesson_admin_router, tags=["Lesson"])

# ===== Language ===== #
v1.include_router(language_router, tags=["Language"])

# ===== Interface ===== #
v1.include_router(interface_routers, tags=["Interface Languages"])

# ===== Topic ===== #
v1.include_router(topic_admin_router, tags=["Topic"])
