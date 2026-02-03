from app.admin.repositories import SuperUserRepository
from app.admin.services import SuperUserService


def get_superuser_service():
    superuser_repo = SuperUserRepository()
    return SuperUserService(superuser_repo)
