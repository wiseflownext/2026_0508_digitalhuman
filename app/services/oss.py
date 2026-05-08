import oss2
import os
from typing import Optional
import requests

BUCKET_NAME = "wiseflownext-digitalhuman"
ENDPOINT = "oss-cn-beijing.aliyuncs.com"
ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")


def get_bucket():
    """Get OSS bucket instance."""
    if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
        raise ValueError("OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET must be set")
    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, ENDPOINT, BUCKET_NAME)


def upload_image(image_data: bytes, uuid: str, ext: str) -> str:
    """
    Upload image to OSS.
    Returns the public URL of the uploaded image.
    """
    bucket = get_bucket()
    object_name = f"digitalhuman/images/{uuid}.{ext}"
    bucket.put_object(object_name, image_data)
    return f"https://{BUCKET_NAME}.{ENDPOINT}/{object_name}"


def upload_video(video_data: bytes, task_id: str) -> str:
    """
    Upload video to OSS.
    Returns the public URL of the uploaded video.
    """
    bucket = get_bucket()
    object_name = f"digitalhuman/videos/{task_id}.mp4"
    bucket.put_object(object_name, video_data)
    return f"https://{BUCKET_NAME}.{ENDPOINT}/{object_name}"


def download_file(url: str) -> bytes:
    """Download file from URL."""
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.content
