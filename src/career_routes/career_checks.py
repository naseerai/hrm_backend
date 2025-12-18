from minio import Minio
from .career_settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, USE_HTTPS,MINIO_BUCKET
from minio.error import S3Error 
import os
import logging
logger = logging.getLogger(__name__)
from datetime import timedelta
try : 
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
except Exception as e:
    logger.error(f"Error initializing Minio client: {e}")
    print("Error initializing Minio client: ", e)
    raise


async def upload_file(file_path: str, object_name: str | None = None) -> str:
    """
    Uploads a local file to the MinIO bucket running on your server.
    Returns the object name used in the bucket.
    """
    try:
        logger.info(f"Uploading file {file_path} to MinIO bucket {MINIO_BUCKET}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        # Create bucket if it doesn't exist
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)

        logger.info(f"Bucket {MINIO_BUCKET} is ready.")

        client.fput_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            file_path=file_path)
        logger.info(f"File {file_path} uploaded as {object_name} to bucket {MINIO_BUCKET}")
        return object_name
    except S3Error as e:
        logger.error(f"Error occurred while uploading file: {e}")
        print("Error occurred while uploading file: ", e)
        raise

async def get_file_url(object_name: str) -> str:
    """
    Returns a direct URL (works if bucket/object are publicly readable).
    """
    try: 
        logger.info(f"Generating presigned URL for object {object_name} in bucket {MINIO_BUCKET}")
        url = client.get_presigned_url(
            "GET",
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            expires=timedelta(days=7)  # URL valid for 7 days
        )
        logger.info(f"Presigned URL generated: {url}")
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned URL: {e}")
        print("Error generating presigned URL: ", e)
        raise





