import uuid
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional

from app.models import (
    TaskCreateResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskItem,
)
from app.database import create_task, update_task_status, get_task, get_tasks
from app.services.seedance import create_video_task, get_task_status
from app.services.oss import upload_image, upload_video, download_file

router = APIRouter(prefix="/api", tags=["video"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image(file: UploadFile):
    """Validate uploaded image file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check content type
    content_type = file.content_type or ""
    if "jpeg" in ext or "jpg" in ext:
        if "jpeg" not in content_type and "jpg" not in content_type:
            raise HTTPException(status_code=400, detail="File type mismatch")
    elif ext == "png":
        if "png" not in content_type:
            raise HTTPException(status_code=400, detail="File type mismatch")

    return ext


async def process_video_download(task_id: str):
    """
    Background task: poll task status, download video when ready, and upload to OSS.
    """
    import time

    max_wait = 600
    poll_interval = 5
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            await update_task_status(task_id, "timeout")
            return

        try:
            data = get_task_status(task_id)
            status = data.get("status", "unknown")

            if status == "succeeded":
                # Get video URL from response
                content = data.get("content", {})
                video_url = content.get("video_url")
                if video_url:
                    # Download video
                    video_data = download_file(video_url)
                    # Upload to OSS
                    oss_url = upload_video(video_data, task_id)
                    await update_task_status(task_id, "succeeded", oss_url)
                else:
                    await update_task_status(task_id, "succeeded")
                return

            elif status in ("failed", "cancelled"):
                await update_task_status(task_id, status)
                return

            # Still running, wait and poll again
            time.sleep(poll_interval)

        except Exception as e:
            # Log error but continue polling
            time.sleep(poll_interval)


@router.post("/generate", response_model=TaskCreateResponse)
async def generate_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    prompt: str = Form(...),
):
    """
    Submit a video generation task.
    1. Upload image to OSS
    2. Create task via Ark API
    3. Save to SQLite
    4. Return task_id immediately
    """
    # Validate image
    ext = validate_image(image)

    # Read image data
    image_data = await image.read()
    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit")

    # Upload to OSS
    img_uuid = str(uuid.uuid4())
    try:
        image_url = upload_image(image_data, img_uuid, ext)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    # Create task via Ark API
    try:
        task_id = create_video_task(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

    # Save to database
    await create_task(task_id, prompt, image_url)

    # Start background polling task
    background_tasks.add_task(process_video_download, task_id)

    return TaskCreateResponse(task_id=task_id, status="queued")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_api(task_id: str):
    """
    Get task status.
    If status is succeeded, ensure video is uploaded to OSS.
    """
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If already succeeded or failed, return cached status
    if task["status"] in ("succeeded", "failed", "cancelled", "timeout"):
        return TaskStatusResponse(
            task_id=task["task_id"],
            status=task["status"],
            video_url=task.get("video_url"),
            created_at=task.get("created_at"),
        )

    # Poll for current status
    try:
        data = get_task_status(task_id)
        status = data.get("status", task["status"])

        if status == "succeeded":
            # Check if we already have video URL
            video_url = task.get("video_url")
            if not video_url:
                content = data.get("content", {})
                video_url = content.get("video_url")
                if video_url:
                    try:
                        video_data = download_file(video_url)
                        video_url = upload_video(video_data, task_id)
                    except Exception:
                        pass  # Keep trying
            await update_task_status(task_id, "succeeded", video_url)
            return TaskStatusResponse(
                task_id=task_id,
                status="succeeded",
                video_url=video_url,
                created_at=task.get("created_at"),
            )

        elif status in ("failed", "cancelled"):
            await update_task_status(task_id, status)
            return TaskStatusResponse(
                task_id=task_id,
                status=status,
                video_url=None,
                created_at=task.get("created_at"),
            )

        else:
            # queued or running, just return current status from DB
            return TaskStatusResponse(
                task_id=task_id,
                status=task["status"],
                video_url=None,
                created_at=task.get("created_at"),
            )

    except Exception as e:
        # Return DB status on error
        return TaskStatusResponse(
            task_id=task_id,
            status=task["status"],
            video_url=task.get("video_url"),
            created_at=task.get("created_at"),
        )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks():
    """Get recent task list (last 20, ordered by created_at desc)."""
    tasks = await get_tasks(limit=20)
    return TaskListResponse(
        tasks=[
            TaskItem(
                id=t["id"],
                task_id=t["task_id"],
                prompt=t["prompt"],
                image_url=t.get("image_url"),
                video_url=t.get("video_url"),
                status=t["status"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
            )
            for t in tasks
        ]
    )
