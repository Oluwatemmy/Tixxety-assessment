from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv(override=True)

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "tixxety",
    broker=broker_url,
    backend=backend_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    result_expires=os.getenv("RESULT_EXPIRATION"),  # 1 hour=3600seconds, 1 day=86400seconds, 1 minute=60seconds
    task_ignore_result=False,  # keep result temporarily
    task_store_errors_even_if_ignored=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
