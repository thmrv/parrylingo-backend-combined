from app.core.services import BaseService
from app.interface.repositories import InterfaceRepository
from loggers import get_logger

logger = get_logger(__name__)


class InterfaceService(BaseService):

    def __init__(self, repository: InterfaceRepository):
        super().__init__(repository)
