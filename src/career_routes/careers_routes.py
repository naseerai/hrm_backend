from fastapi import FastAPI , APIRouter,HTTPException,Depends,status
from .career_models import InternalHiringJobCreate, ExternalHiringJobCreate , JobBase,UpdateJobs,JobApplications,UpdateJobApplications
from supabase import create_client, Client
from src.common_routes.common_checks import get_supabase_client
from src.login.login_checks import get_current_user_id 
import logging
from datetime import date
from typing import  Optional
from pydantic import  EmailStr 
from fastapi import UploadFile, File ,Form
from .career_checks import upload_file,get_file_url
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
    




@router.get("/job/details/{job_type}/{job_id}", summary="Get job details")
def job_details(job_id: str  ,job_type:str, supabase: Client = Depends(get_supabase_client)):
    """
    Returns the job_id details.
    """
    try:
        logger.info("Fetching job details for job_id=%s", job_id)
        if job_type == 'internal':
            res = supabase.table("internal_hiring_jobs").select("*").eq("id", job_id).maybe_single().execute()  # [web:15][web:172]
        elif job_type == 'external':
            res = supabase.table("external_hiring_jobs").select("*").eq("id", job_id).maybe_single().execute()  # [web:15][web:172]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )
        # [web:15][web:172]

        if getattr(res, "error", None):
            logger.error("Failed to fetch job_id=%s: %s", job_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch job details",
            )

        if not res.data:
            logger.warning("User not found job_id=%s", job_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="job not found",
            )

        logger.info("Fetched job details for job_id=%s", job_id)
        return res.data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error fetching job_id=%s: %s", job_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job details",
        )
    



@router.post("/applications/{job_type}/{job_id}", summary="Submit job application")
async def job_applications(
    job_type: str,
    job_id: str,
    application_data: str = Form(...),          # JSON string
    email: EmailStr = Form(...),
    mobile: str = Form(...),
    remarks: Optional[str] = Form(None),
    recruiter_id: Optional[str] = Form(None),
    application_status: Optional[str] = Form("applied"),
    resume_file: UploadFile = File(...),        # required file
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        logger.info("Submitting application for job_id=%s", job_id)

        # Parse JSON string into dict
        import json
        try:
            application_data_dict = json.loads(application_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid application_data JSON",
            )

        # Validate presence of resume file
        if resume_file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume file is required",
            )

        # Save resume to temp path
        tmp_path = f"/tmp/{resume_file.filename}"
        with open(tmp_path, "wb") as f:
            f.write(await resume_file.read())

        # Upload to MinIO and get object name
        resume_link = await upload_file(file_path=tmp_path)

        data = {
            "job_id": job_id,
            "applicant_data": application_data_dict,  # matches DB column
            "email": email,
            "mobile": mobile,
            "resume_link": resume_link,
            "remarks": remarks,
            "recruiter_id": recruiter_id,
            "application_status": application_status,
        }

        if job_type == "internal":
            logger.info("Inserting application into internal_job_applications for job_id=%s", job_id)
            response = supabase.table("internal_job_applications").insert(data).execute()
        elif job_type == "external":
            logger.info("Inserting application into external_job_applications for job_id=%s", job_id)
            response = supabase.table("external_job_applications").insert(data).execute()
        else:
            logger.error("Invalid job_type provided: %s", job_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )

        if getattr(response, "error", None):
            logger.error("Failed to submit application for job_id=%s: %s", job_id, response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit job application",
            )

        logger.info("Application submitted successfully for job_id=%s: %s", job_id, response.data)
        return {
            "message": "Application submitted successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error submitting application for job_id=%s: %s", job_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit job application",
        )
    



@router.get("/job/applications/{job_type}/{job_id}", summary="Get job applications for a job posting")
async def get_job_applications(
    job_type: str,
    job_id: str,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        logger.info("Fetching applications for job_id=%s", job_id)

        if job_type == "internal":
            response = (
                supabase
                .table("internal_job_applications")
                .select("*")
                .eq("job_id", job_id)
                .execute()
            )  # returns .data as a list of dicts [web:15]
        elif job_type == "external":
            response = (
                supabase
                .table("external_job_applications")
                .select("*")
                .eq("job_id", job_id)
                .execute()
            )
        else:
            logger.error("Invalid job_type provided: %s", job_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )

        if getattr(response, "error", None):
            logger.error("Failed to fetch applications for job_id=%s: %s", job_id, response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch job applications",
            )

        # response.data is a list of dicts; update each dict's resume_link
        applications = []
        for row in response.data or []:
            object_name = row.get("resume_link")
            resume_url = await get_file_url(object_name=object_name) if object_name else None

            applications.append({
                **row,
                "resume_link": resume_url,
            })

        logger.info("Fetched %d applications successfully for job_id=%s", len(applications), job_id)
        return {
            "message": "Fetched applications successfully",
            "data": applications,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching applications for job_id=%s: %s", job_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job applications",
        )



@router.patch("/update/application/{job_type}/{application_id}", summary="Update a job application")
async def update_job_application(
    application_id: str,
    job_type: str,
    payload: UpdateJobApplications,
    supabase: Client = Depends(get_supabase_client),
    _: str = Depends(get_current_user_id),
):
    try:
        # Build dict of only provided fields
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        logger.debug("Final update_data payload for application_id=%s: %s", application_id, update_data)

        # Route to the correct table
        if job_type == "internal":
            logger.debug("Updating internal application with ID %s: %s", application_id, update_data)
            response = (
                supabase
                .table("internal_job_applications")
                .update(update_data)
                .eq("id", application_id)
                .execute()
            )
        elif job_type == "external":
            logger.debug("Updating external application with ID %s: %s", application_id, update_data)
            response = (
                supabase
                .table("external_job_applications")
                .update(update_data)
                .eq("id", application_id)
                .execute()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_type. Use 'internal' or 'external'.",
            )

        logger.debug("Update response for application_id=%s: %s", application_id, response)

        if getattr(response, "error", None):
            logger.error("Failed to update job application: %s", response.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update job application",
            )

        if not response.data:
            logger.warning("Job application not found application_id=%s job_type=%s", application_id, job_type)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found",
            )

        logger.info("Job application updated successfully: %s", response.data)
        return {
            "message": "Job application updated successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error updating job application: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job application",
        )
    

