from app.interface.repositories import InterfaceRepository
from app.interface.services import InterfaceService


def get_interface_service() -> InterfaceService:
    interface_repo = InterfaceRepository()
    return InterfaceService(interface_repo)
