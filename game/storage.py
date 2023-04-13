import redis
import os


redis_db = redis.Redis(
    host=os.environ.get("REDIS_HOST"),
    port=os.environ.get("REDIS_PORT"),
    password=os.environ.get("REDIS_PASSWORD"),
    charset='utf-8',
    decode_responses=True,
    )