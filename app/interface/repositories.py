from app.core.database.repositories import BaseRepository
from app.interface.models import Interface


class InterfaceRepository(BaseRepository):
    def __init__(self):
        super().__init__(Interface)
