import os
import requests
from typing import Optional

BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_SEEDANCE_ENDPOINT = os.getenv("ARK_SEEDANCE_ENDPOINT", "")


def get_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ARK_API_KEY}",
    }


def create_video_task(prompt: str) -> str:
    """
    Create a video generation task via Ark API.
    Returns the task_id.
    """
    if not ARK_API_KEY or not ARK_SEEDANCE_ENDPOINT:
        raise ValueError("ARK_API_KEY and ARK_SEEDANCE_ENDPOINT must be set")

    url = f"{BASE_URL}/contents/generations/tasks"
    payload = {
        "model": ARK_SEEDANCE_ENDPOINT,
        "content": [
            {
                "type": "text",
                "text": prompt,
            }
        ],
    }

    response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    task_id = data.get("id")
    if not task_id:
        raise RuntimeError(f"No task id in response: {data}")
    return task_id


def get_task_status(task_id: str) -> dict:
    """
    Query task status from Ark API.
    Returns the full response dict.
    """
    url = f"{BASE_URL}/contents/generations/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {ARK_API_KEY}"}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def poll_task_until_done(task_id: str, max_wait_seconds: int = 600, poll_interval: int = 5) -> dict:
    """
    Poll task status until succeeded, failed, or timeout.
    Returns the final task data dict.
    """
    import time

    start_time = time.time()
    while True:
        data = get_task_status(task_id)
        status = data.get("status", "unknown")

        elapsed = int(time.time() - start_time)
        if status == "succeeded":
            return data
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"Task {status}: {data}")
        if elapsed > max_wait_seconds:
            raise TimeoutError(f"Polling timeout after {max_wait_seconds}s, last status: {status}")

        time.sleep(poll_interval)
