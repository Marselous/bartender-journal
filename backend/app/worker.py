from __future__ import annotations

import logging
from typing import Any

from celery import Celery

from app.settings import settings

logger = logging.getLogger(__name__)

broker_url = settings.redis_url or "redis://redis:6379/0"

celery_app = Celery(
    "bartender_journal",
    broker=broker_url,
    backend=broker_url,
)


@celery_app.task(name="tasks.process_image")
def process_image(post_id: str, image_url: str | None) -> dict[str, Any]:
    # Placeholder: in a real system you would download and resize the image,
    # write back to object storage, etc. For now we just log.
    logger.info("Processing image for post %s: %s", post_id, image_url)
    return {"post_id": post_id, "image_url": image_url}


@celery_app.task(name="tasks.send_notification")
def send_notification(recipient: str, message: str) -> dict[str, Any]:
    # Placeholder: integrate with an email or webhook provider later.
    logger.info("Sending notification to %s: %s", recipient, message)
    return {"recipient": recipient}

