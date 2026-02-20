import redis.asyncio as redis # Change this to the asyncio module
from typing import AsyncGenerator
import os

from app.core.settings import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_database,
    decode_responses=True,
)

REDIS_URL = settings.redis_host + str(settings.redis_port)

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    # decode_responses=True makes Redis return strings instead of bytes
    #client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield redis_client
    finally:
        await redis_client.close()
