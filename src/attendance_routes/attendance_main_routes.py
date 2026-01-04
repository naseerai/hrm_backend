from fastapi import APIRouter , UploadFile,File,HTTPException,Depends,security,status
from fastapi.responses import JSONResponse
from .attendance_checks import validate_images
from supabase import Client
from typing import Optional
from src.common_routes.common_checks import get_supabase_client
from src.login.login_checks import get_current_user_id 
from src.career_routes.career_checks import get_file_url
from datetime import date, datetime , time
import logging
from datetime import date,timedelta
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/attendace",tags=["take attaendance of users"],
    dependencies=[Depends(get_current_user_id)])


@router.post("/validate/images", summary="Check if uploaded image matches user's profile picture")
async def validate_image(
    user_id: str,
    image1: UploadFile = File(..., description="Uploaded image to compare"),
    supabase: Client = Depends(get_supabase_client)
):
    try:
        if not image1.content_type.startswith('image/'):
            raise HTTPException(400, "Only image files allowed")
        
        # Fix: Access data correctly from Supabase response
        user_response = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
        
        if not user_response.data:
            raise HTTPException(404, "User not found")
        
        user_data = user_response.data  # Now correctly accessed
        profile_picture = user_data.get("user_profile_picture")
        
        if not profile_picture:
            raise HTTPException(400, "User has no profile picture")
        
        logger.info(f"User profile picture: {profile_picture}")
        image2_url = await get_file_url(object_name=profile_picture)  # Fix: use profile_picture
        # logger.info(f"Profile image URL: {image2_url}")
        
        result = await validate_images(image1, image2_url)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(500, f"Processing error: {str(e)}")
   