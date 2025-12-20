from fastapi import FastAPI, APIRouter,HTTPException,Depends,Request,status,Query
from .calendar_setting import HOLIDAY_PROXY_URL, HOLIDAY_TARGET_URL
from src.common_routes.common_checks import get_supabase_client
from src.login.login_checks import get_current_user_id 
from supabase import Client
from .calendar_checks import get_year_holidays
from .calendar_models import HolidayUpdate ,HolidayCreate
from typing import List
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar Main Routes"])



@router.get("/holidays/{year}", summary="Get Holidays for a given year")
async def get_holidays(year: int, supabase: Client = Depends(get_supabase_client),_: str =Depends(get_current_user_id)):
    try:
        # Step 1: Fetch holidays from the database
        holidays = supabase.table("holidays_calendar").select("*").eq("year", year).execute()

        # Handle database query failure
        if getattr(holidays, "error", None):
            logger.error("Failed to get holiday calendar: %s", holidays.error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get holiday calendar from database"
            )

        # Step 2: If no holidays are found in the database, fetch from external API
        if not holidays.data:
            logger.info("No holidays found in the database for the year %d. Fetching from external API.", year)

            # Fetch holidays from the external API
            fetched_holidays = await get_year_holidays(year)

            # If no holidays are fetched from the external API, raise an error
            if not fetched_holidays:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No holidays found for the given year from the external API"
                )

            # Insert the fetched holidays into the database
            insert_response = supabase.table("holidays_calendar").insert(fetched_holidays).execute()

            # Handle insert failure
            if getattr(insert_response, "error", None):
                logger.error("Failed to insert holidays: %s", insert_response.error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to insert holiday data into database"
                )

            logger.info("Successfully inserted %d holidays into the database for the year %d.", len(fetched_holidays), year)

            # Step 3: Re-fetch the holidays after insertion to return the updated data
            holidays = supabase.table("holidays_calendar").select("*").eq("year", year).execute()

            # Handle re-fetch failure
            if getattr(holidays, "error", None):
                logger.error("Failed to get holiday calendar after insertion: %s", holidays.error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch holiday calendar after insertion"
                )

        # Step 4: Return the holidays data
        return holidays.data

    except HTTPException as e:
        # Catch specific HTTP errors
        logger.error("HTTP error occurred: %s", str(e.detail))
        raise e
    except Exception as e:
        # Handle unexpected errors
        logger.error("Unexpected error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.patch("/update/holidays", summary="Bulk update holidays")
async def patch_holidays(
    payload: List[HolidayUpdate],
    supabase: Client = Depends(get_supabase_client),_: str =Depends(get_current_user_id)
):
    try:
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload list cannot be empty",
            )

        # Convert to list of plain dicts
        data = []
        for item in payload:
            d = item.model_dump(exclude_unset=True,exclude_none=True)
            if "id" not in d:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each holiday item must include 'id'",
                )
            data.append(d)

        logger.info("Upserting holidays: %s", data)

        # Use upsert exactly as the Supabase docs show
        response = supabase.table("holidays_calendar").upsert(data).execute()

        logger.info("Upsert response: %s", response)

        if getattr(response, "error", None):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update holidays: {response.error}",
            )

        return {
            "message": "Holidays updated successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error upserting holidays: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating holidays",
        )


@router.post("/holidays", summary="Create new holidays")
async def create_holidays(
    payload: List[HolidayCreate],
    supabase: Client = Depends(get_supabase_client),_: str =Depends(get_current_user_id)
):
    try:
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload list cannot be empty",
            )

        # Convert to list of plain dicts, excluding None values
        data = []
        for item in payload:
            d = item.model_dump(exclude_none=True)
            data.append(d)

        logger.info("Creating holidays: %s", data)

        # Insert new holidays
        response = supabase.table("holidays_calendar").insert(data).execute()

        logger.info("Insert response: %s", response)

        if getattr(response, "error", None):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create holidays: {response.error}",
            )

        return {
            "message": "Holidays created successfully",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating holidays: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating holidays",
        )




@router.delete("/holidays", summary="Delete holidays by ids")
async def delete_holidays(
    ids: List[str] = Query(..., description="IDs of holidays to delete"),  
    supabase: Client = Depends(get_supabase_client),_: str =Depends(get_current_user_id)
):
    try:
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one id must be provided",
            )

        logger.info("Deleting holidays with ids: %s", ids)

        # Delete all rows where id is in the list
        response = (
            supabase
            .table("holidays_calendar")
            .delete()
            .in_("id", ids)
            .execute()
        )

        logger.info("Delete response: %s", response)

        if getattr(response, "error", None):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete holidays: {response.error}",
            )

        return {
            "message": f"Successfully deleted {len(ids)} holidays",
            "data": response.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting holidays: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting holidays",
        )



