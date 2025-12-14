from fastapi import APIRouter, HTTPException, status, Depends,BackgroundTasks
from supabase import Client
from .common_models import UserCreate,UserUpdate,ChangePasswordRequest
import os
from supabase import create_client
from dotenv import load_dotenv
import logging
from src.login.login_checks import get_current_user_id 
from .common_checks import get_supabase_client, generate_user_based_password , send_email
from .common_setting import SUPABASE_URL, SUPABASE_ANON_KEY,SMTP_HOST,SMTP_PORT,SMTP_USERNAME,SMTP_PASSWORD
load_dotenv()
router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)





@router.post("/create/user", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    supabase: Client = Depends(get_supabase_client),background_tasks: BackgroundTasks = None,user_id: str = Depends(get_current_user_id)
):
    # Check duplicate email
    try:
        logger.info("User creation attempt by user_id=%s for email=%s", user_id, payload.email)
        existing = (
            supabase
            .table("users")
            .select("id")
            .or_(f"email.eq.{payload.email},mobile.eq.{payload.mobile}")
            .maybe_single()
            .execute()
        )  # [web:171][web:179][web:182]
        if existing is not None:
            logger.warning("User creation failed: email or mobile already exists email=%s mobile=%s", payload.email, payload.mobile)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or mobile already exists",
            )
        password = await generate_user_based_password(payload.name, payload.email)
        template_path = "src/common_routes/email_templates/office_mail_template.html"
        smtp_server = SMTP_HOST
        smtp_port = SMTP_PORT
        smtp_username = SMTP_USERNAME
        smtp_password = SMTP_PASSWORD

        # Insert row (no id / created_at provided, DB defaults are used)
        to_insert = {
            "name": payload.name,
            "email": payload.email,
            "office_mail": payload.office_mail,
            "password": password,  # plain text as requested (not safe)
            "role": payload.role,
            "mobile": payload.mobile,
            "createdby": payload.created_by,
        }
        mail_data = {
            "name": payload.name,
            "office_mail": payload.office_mail,
            "password": password,
            "role": payload.role,
        }
        receiver_email = payload.email
        subject = "Your Account Details"
        background_tasks.add_task(
            send_email,
            template_path,
            mail_data,
            receiver_email,
            subject,
            smtp_server,
            smtp_port,
            smtp_username,
            smtp_password,
        )
        logger.info("Email sending task added for user email=%s", payload.email)

        res = supabase.table("users").insert(to_insert).execute()  # [web:161]
        # print(f"this is response : \n\n\n\n{res}\n\n\n\n\n")
        if not res:
            logger.error("User creation failed for email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        # Return minimal info (you can shape this how you like)
        created = res.data[0]
        logger.info("User created successfully user_id=%s email=%s", created.get("id"), created.get("email"))
        return {
            "id": created.get("id"),
            "email": created.get("email"),
            "name": created.get("name"),
            
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error creating user email=%s: %s", payload.email, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get("/user/profile", summary="Get current user details")
def read_me(user_id: str = Depends(get_current_user_id) , supabase: Client = Depends(get_supabase_client)):
    """
    Returns the current user's details.
    """
    try:
        logger.info("Fetching current user details for user_id=%s", user_id)
        res = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()  # [web:15][web:172]

        if getattr(res, "error", None):
            logger.error("Failed to fetch user_id=%s: %s", user_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user details",
            )

        if not res.data:
            logger.warning("User not found user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info("Fetched user details for user_id=%s", user_id)
        return res.data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error fetching user_id=%s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user details",
        )



@router.get("/allusers", summary="Get all users")
def get_all_users(
    _: str = Depends(get_current_user_id),          # require auth
    supabase: Client = Depends(get_supabase_client)
):
    """
    Returns all users from the `users` table.
    """
    try:
        logger.info("Fetching all users requested by user_id=%s", _)
        res = supabase.table("users").select("*").execute()  # [web:15]

        if getattr(res, "error", None):
            logger.error("Failed to fetch users: %s", res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users",
            )
        logger.info("Fetched %d users", len(res.data))
        # Supabase Python client returns rows in `data` [web:15][web:172]
        return res.data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error fetching users: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users",
        )



@router.patch("/update/{user_id}", summary="Update user details")
def update_user(
    user_id: str,
    payload: UserUpdate,
    _: str = Depends(get_current_user_id),        # require auth
    supabase: Client = Depends(get_supabase_client),
):
    # Build dict of only provided fields
    try:

        logger.info("Updating user_id=%s", user_id)
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Optional: prevent email/mobile duplicates here if needed

        # Perform update
        res = (
            supabase
            .table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )  # [web:15][web:171]

        if getattr(res, "error", None):
            logger.error("Failed to update user_id=%s: %s", user_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

        if not res.data:
            logger.warning("User not found for update user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return res.data[0]
    except HTTPException as he:
        raise he
    except Exception as e: 
        logger.exception("Error updating user_id=%s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    



@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
def delete_user(
    user_id: str,
    _: str = Depends(get_current_user_id),          # require auth
    supabase: Client = Depends(get_supabase_client),
):
    """
    Delete a user from the `users` table by id.
    """
    try:
        logger.info("Deleting user_id=%s", user_id)

        res = (
            supabase
            .table("users")
            .delete()
            .eq("id", user_id)
            .execute()
        )  # [web:239]

        if getattr(res, "error", None):
            logger.error("Failed to delete user_id=%s: %s", user_id, res.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

        # Supabase returns deleted rows in data when using representation [web:239]
        if not res.data:
            logger.warning("User not found for delete user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info("User deleted successfully user_id=%s", user_id)
        return  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error deleting user_id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
    




@router.put("/reset_password/{user_id}", summary="Reset user password")
async def reset_user_password(
    user_id: str,
    _: str = Depends(get_current_user_id),          # require auth
    supabase: Client = Depends(get_supabase_client),
    background_tasks: BackgroundTasks = None,
):
    """
    Resets the user's password and sends an email with the new password.
    """
    try:
        logger.info("Resetting password for user_id=%s", user_id)
        # Fetch user details
        res = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
        if not res.data:
            logger.warning("User not found for password reset user_id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        user = res.data
        new_password = await generate_user_based_password(user["name"], user["email"])
        
        # Update password in DB
        update_res = (
            supabase
            .table("users")
            .update({"password": new_password , "password_updated" : True})
            .eq("id", user_id)
            .execute()
        )
        if getattr(update_res, "error", None):
            logger.error("Failed to update password for user_id=%s: %s", user_id, update_res)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password",
            )

        # Send email with new password
        template_path = "src/common_routes/email_templates/password_reset_template.html"
        smtp_server = SMTP_HOST
        smtp_port = SMTP_PORT
        smtp_username = SMTP_USERNAME
        smtp_password = SMTP_PASSWORD

        mail_data = {
            "name": user["name"],
            "office_mail": user["office_mail"],
            "new_password": new_password,
        }
        receiver_email = user["office_mail"]
        subject = "Your Password Has Been Reset"
        background_tasks.add_task(
            send_email,
            template_path,
            mail_data,
            receiver_email,
            subject,
            smtp_server,
            smtp_port,
            smtp_username,
            smtp_password,
        )
        logger.info("Password reset email task added for user_id=%s", user_id)

        return {"detail": "Password reset successfully."}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error resetting password for user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )
    


@router.put("/change_password/", summary="Change user password")
async def change_user_password(
    data: ChangePasswordRequest,
     _: str = Depends(get_current_user_id),       # require auth
    supabase: Client = Depends(get_supabase_client),
):
    """
    Changes the user's password to the provided new password.
    """
    try:
        logger.info("Changing password for user_id=%s", data.user_id)

        # Update password in DB
        update_res = (
            supabase
            .table("users")
            .update({"password": data.new_password , "password_updated" : False,"firstlogin":False})
            .eq("id", data.user_id)
            .execute()
        )
        if getattr(update_res, "error", None):
            logger.error("Failed to change password for user_id=%s: %s", data.user_id, update_res)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password",
            )

        logger.info("Password changed successfully for user_id=%s", data.user_id)
        return {"detail": "Password changed successfully."}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error changing password for user_id=%s: %s", data.user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )
    


