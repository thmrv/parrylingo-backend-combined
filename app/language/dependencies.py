from app.language.repositories import LanguageRepository
from app.language.services import LanguageService

def get_language_service() -> LanguageService:
    language_repo = LanguageRepository()
    return LanguageService(language_repo)
