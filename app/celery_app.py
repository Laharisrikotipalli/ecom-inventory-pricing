import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ecom",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.timezone = "UTC"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
