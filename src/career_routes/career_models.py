from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field , EmailStr ,FilePath
from fastapi import UploadFile, File


class JobBase(BaseModel):
    job_title: Optional[str] = None
    experience: Optional[str] = None
    salary: Optional[str] = None
    job_location: Optional[str] = None

    job_description: Optional[str] = None
    key_skills: List[str] = Field(default_factory=list)

    employment_type: Optional[str] = None
    work_mode: Optional[str] = None

    company_name: Optional[str] = None
    company_location: Optional[str] = None

    openings: Optional[int] = None
    posted_date: Optional[date] = Field(default=None)
    job_status: Optional[str] = "open"
    
    created_by: Optional[str] = None

    job_type: Optional[str] = None  # 'internal' or 'external'



class InternalHiringJobCreate(JobBase):
    pass


class ExternalHiringJobCreate(JobBase):
    pass





class UpdateJobs(BaseModel):
    job_title: Optional[str] = None
    experience: Optional[str] = None
    salary: Optional[str] = None
    job_location: Optional[str] = None

    job_description: Optional[str] = None
    key_skills: Optional[List[str]] = Field(default_factory=list)

    employment_type: Optional[str] = None
    work_mode: Optional[str] = None

    company_name: Optional[str] = None
    company_location: Optional[str] = None

    openings: Optional[int] = None
    posted_date: Optional[date] = Field(default=None)
    job_status: Optional[str] = None
    
    created_by: Optional[str] = None

   

class JobApplications(BaseModel):
    job_id: str
    application_data: dict
    email: EmailStr
    mobile: str
    resume_file : UploadFile | None = File(None)
    remarks: Optional[str] = None
    recruiter_id: Optional[str] = None
    application_status: Optional[str] = "applied"


class UpdateJobApplications(BaseModel):
    application_data: Optional[dict] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    remarks: Optional[str] = None
    application_status: Optional[str] = "applied"