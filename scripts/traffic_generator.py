#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from datetime import datetime

API_BASE = os.getenv("API_BASE", "http://backend:8000").rstrip("/")
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "0.75"))
AUTHOR_NAME = os.getenv("AUTHOR_NAME", "load-bot")


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list | str | None]:
    url = f"{API_BASE}{path}"
    body = None
    headers = {"accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"

    req = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def _create_post() -> str | None:
    payload = {
        "type": random.choice(["text", "link", "photo"]),
        "title": f"Synthetic event {datetime.utcnow().isoformat()}",
        "author_name": AUTHOR_NAME,
    }
    if payload["type"] == "text":
        payload["body"] = "Shift review: workflow simulated by traffic generator."
    elif payload["type"] == "link":
        payload["link_url"] = "https://example.com/devops-portfolio"
    else:
        payload["image_url"] = "https://picsum.photos/300"

    status, data = _request("POST", "/posts", payload)
    if status in (200, 201) and isinstance(data, dict):
        return data.get("id")
    return None


def _comment_on_latest() -> None:
    status, data = _request("GET", "/posts?limit=1")
    if status != 200 or not isinstance(data, dict) or not data.get("items"):
        return
    post_id = data["items"][0]["id"]
    _request(
        "POST",
        f"/posts/{post_id}/comments",
        {"body": "Automated engagement for observability tests.", "author_name": AUTHOR_NAME},
    )


def run() -> None:
    while True:
        _request("GET", "/healthz")
        _request("GET", f"/posts?limit={random.choice([5, 10, 20])}")
        if random.random() < 0.35:
            _create_post()
        if random.random() < 0.25:
            _comment_on_latest()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
