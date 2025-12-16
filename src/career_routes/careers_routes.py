from fastapi import FastAPI , APIRouter,HTTPException,Depends,status
from .career_models import InternalHiringJobCreate, ExternalHiringJobCreate , JobBase,UpdateJobs
from supabase import create_client, Client
from src.common_routes.common_checks import get_supabase_client
from src.login.login_checks import get_current_user_id 
import logging
from datetime import date
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/careers", tags=["careers"])


@router.post("/create/job", summary="Create a new job posting internla and external")
async def create_internal_job(
    payload: JobBase,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        posted_date = payload.posted_date
        # Convert date to ISO string if present
        posted_date_str = posted_date.isoformat() if isinstance(posted_date, date) else None
          # or payload.dict() if you're on Pydantic v1

        data = {
            "job_title": payload.job_title,
            "experience": payload.experience,
            "salary": payload.salary,
            "job_location": payload.job_location,
            "job_description": payload.job_description,
            "key_skills": payload.key_skills,
            "employment_type": payload.employment_type,
            "work_mode": payload.work_mode,
            "company_name": payload.company_name,
            "company_location": payload.company_location,
            "openings": payload.openings,
            "posted_date": posted_date_str,
            "job_status": payload.job_status,
            "created_by": str(payload.created_by),
        }
        if payload.job_type == 'internal':
            response = (
                supabase
                .table("internal_hiring_jobs")
                .insert(data)
                .execute()
            )  # [web:15]
        elif payload.job_type == 'external':
            response = (
                supabase
                .table("external_hiring_jobs")
                .insert(data)
                .execute()
            )  # [web:15]

        if getattr(response, "error", None):
            logger.error("Failed to create internal job: %s", response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create internal job",
            )

        logger.info("Internal job created successfully: %s", response.data)
        return {
            "message": "Internal job created successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error creating internal job: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create internal job",
        )




@router.get("/list/{job_type}/jobs", summary="List all internal job postings")
async def list_external_jobs(
    job_type: str,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    
    try:

        if job_type == 'external':
            response = (
                supabase
                .table("external_hiring_jobs")
                .select("*")
                .execute()
            )

            if getattr(response, "error", None):
                logger.error("Failed to fetch external jobs: %s", response.error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch external jobs",
                )

            logger.info("Fetched external jobs successfully")
            return {
                "message": "Fetched external jobs successfully",
                "data": response.data,
            }
        
        elif job_type == 'internal':
            response = (
                supabase
                .table("internal_hiring_jobs")
                .select("*")
                .execute()
            )

            if getattr(response, "error", None):
                logger.error("Failed to fetch internal jobs: %s", response.error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch internal jobs",
                )

            logger.info("Fetched internal jobs successfully")
            return {
                "message": "Fetched internal jobs successfully",
                "data": response.data,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching {job_type} jobs: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch {job_type} jobs",
        )
    



@router.patch("/update/job/{job_type}/{job_id}", summary="Update a job posting")
async def update_job_posting(
    job_id: str,
    job_type: str,
    payload: UpdateJobs,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        # Build dict of only provided fields
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        print(f"Update data before date normalization:\n\n{update_data}\n")

        # Normalize posted_date (date -> ISO string)
        if "posted_date" in update_data:
            posted_date = update_data["posted_date"]
            if isinstance(posted_date, date):
                update_data["posted_date"] = posted_date.isoformat()
            else:
                # if something weird comes in, drop it instead of breaking JSON
                update_data.pop("posted_date", None)

        logger.debug("Final update_data payload: %s", update_data)

        # Route to the correct table
        if job_type == "internal":
            logger.debug("Updating internal job with ID %s: %s", job_id, update_data)
            response = (
                supabase
                .table("internal_hiring_jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
        elif job_type == "external":
            logger.debug("Updating external job with ID %s: %s", job_id, update_data)
            response = (
                supabase
                .table("external_hiring_jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )

        logger.debug("Update response: %s", response)

        if getattr(response, "error", None):
            logger.error("Failed to update job posting: %s", response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update job posting",
            )

        if not response.data:
            logger.warning("Job posting not found job_id=%s job_type=%s", job_id, job_type)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found",
            )

        logger.info("Job posting updated successfully: %s", response.data)
        return {
            "message": "Job posting updated successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error updating job posting: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job posting",
        )
    



@router.delete("/delete/job/{job_type}/{job_id}", summary="Delete a job posting")
async def delete_job_posting(
    job_id: str,
    job_type: str,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        # Route to the correct table
        if job_type == "internal":
            logger.debug("Deleting internal job with ID %s", job_id)
            response = (
                supabase
                .table("internal_hiring_jobs")
                .delete()
                .eq("id", job_id)
                .execute()
            )
        elif job_type == "external":
            logger.debug("Deleting external job with ID %s", job_id)
            response = (
                supabase
                .table("external_hiring_jobs")
                .delete()
                .eq("id", job_id)
                .execute()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )

        if getattr(response, "error", None):
            logger.error("Failed to delete job posting: %s", response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete job posting",
            )

        if not response.data:
            logger.warning("Job posting not found for deletion job_id=%s job_type=%s", job_id, job_type)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found",
            )

        logger.info("Job posting deleted successfully: %s", response.data)
        return {
            "message": "Job posting deleted successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error deleting job posting: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job posting",
        )
    
