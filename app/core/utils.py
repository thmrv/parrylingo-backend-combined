import asyncio
import os
import uuid
from datetime import date, datetime, time
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union
from zoneinfo import ZoneInfo

import aiofiles
import pytz
from fastapi import UploadFile
from passlib.context import CryptContext
from pydub import AudioSegment

from app.core.settings import settings
from loggers import get_logger

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=2,
)
MEDIA_ROOT = "media"
logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Hashes the provided password using Argon2 with the configured parameters.

    :param password: The plaintext password as a string.
    :return: The hashed password as a string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies that a text password matches its hashed counterpart.

    :param plain_password: The text password provided by the user.
    :param hashed_password: The stored hashed password from the database.
    :return: True if the passwords match, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


LOCAL_TZ = pytz.timezone(str(settings.tz))


def parse_date_range(
    from_date: Optional[Union[str, date, datetime]],
    to_date: Optional[Union[str, date, datetime]],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """If only `to_date` is provided, both `from_date` and `to_date` will be set to the start and end of that day.
    If both `from_date` and `to_date` are provided, they will be converted to datetime objects
    representing the start and end of their respective days.

    :param from_date: Start date string (format YYYY-MM-DD) or None
    :param to_date: End date string (format YYYY-MM-DD) or None
    :return: Tuple (from_date, to_date) with datetime objects or (None, None) if both are None
    """

    def to_utc(
        input_date: Union[str, date, datetime], is_end: bool = False
    ) -> datetime:
        """Convert local time to UTC"""
        if isinstance(input_date, str):
            _date = list(map(int, input_date.split("-")))
            time_part = time.max if is_end else time.min
            local_dt = LOCAL_TZ.localize(
                datetime.combine(date(_date[0], _date[1], _date[2]), time_part)
            )
        elif isinstance(input_date, date):
            local_dt = LOCAL_TZ.localize(
                datetime.combine(input_date, time.max if is_end else time.min)
            )
        elif isinstance(input_date, datetime):
            local_dt = input_date.astimezone(LOCAL_TZ)
        else:
            return None
        return local_dt.astimezone(pytz.utc)  # convert to UTC

    if to_date and not from_date:
        from_date = to_utc(to_date, is_end=False)  # Local 00:00 → UTC
        to_date = to_utc(to_date, is_end=True)  # Local 23:59:59 → UTC

    elif from_date and to_date:
        from_date = to_utc(from_date, is_end=False)
        to_date = to_utc(to_date, is_end=True)

    return from_date, to_date


def get_utc_now() -> datetime:
    """
    Get the current date and time in UTC.

    This function returns the current time with timezone information set to UTC,
    ensuring that the returned datetime object is offset-aware.

    Returns:
        datetime: The current date and time in UTC with tzinfo set to ZoneInfo("UTC").
    """
    return datetime.now(ZoneInfo("UTC"))


async def save_upload_file(
    upload_file: UploadFile, subdir: str, convert_to_mp3: bool = False
) -> str:
    dir_path = os.path.join(MEDIA_ROOT, subdir)
    os.makedirs(dir_path, exist_ok=True)

    original_ext = os.path.splitext(upload_file.filename)[1]
    ext = ".mp3" if convert_to_mp3 else original_ext
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(dir_path, filename)

    try:
        content = await upload_file.read()

        if convert_to_mp3:
            # читаем как AudioSegment и конвертируем
            temp = BytesIO(content)
            audio = AudioSegment.from_file(temp)
            audio.export(file_path, format="mp3")
        else:
            async with aiofiles.open(file_path, "wb") as out:
                await out.write(content)

        logger.info("File saved successfully as %s", file_path)

    except Exception as e:
        logger.error("Failed to save file %s: %s", upload_file.filename, e)
        raise

    return f"{subdir}/{filename}"


async def remove_media_file(rel_path: str) -> None:
    """
    Асинхронно удаляет файл по относительному пути rel_path.
    """
    full_path = Path(MEDIA_ROOT) / rel_path
    logger.info("Attempting to delete media file: %s", full_path)

    def _unlink():
        try:
            full_path.unlink()
            logger.info("File deleted successfully: %s", full_path)
        except FileNotFoundError:
            logger.warning("File not found when deleting: %s", full_path)
        except Exception as e:
            # логируем и пропускаем, чтобы не сломать основной flow
            logger.error("Error deleting file %s: %s", full_path, e)

    # Переносим блокирующий unlink в поток
    await asyncio.to_thread(_unlink)
    logger.debug("Deletion task scheduled for: %s", full_path)
