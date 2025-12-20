import httpx
from .calendar_setting import HOLIDAY_PROXY_URL, HOLIDAY_TARGET_URL
from fastapi import HTTPException,status
import json

async def get_year_holidays(year: int):
    try:
        # Construct the URL to fetch holidays for the given year
        url = f"{HOLIDAY_PROXY_URL}{HOLIDAY_TARGET_URL}{year}"
        print(f"Fetching holidays from: {url}")
        
        # Send an asynchronous GET request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60)

        # Check if the response is successful
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch holidays")
        
        # Parse the JSON response
        data = response.json()

        # If the 'contents' field is found in the response
        if 'contents' in data:
            holidays = json.loads(data['contents'])
            
            # Filter out only the necessary fields
            filtered_holidays = [
                {
                    "name": holiday.get("name"),
                    "holiday_date": holiday.get("date"),
                    "description": holiday.get("description"),
                    "holiday_type": holiday.get("type"),
                    "year": year
                }
                for holiday in holidays
            ]

            # Return the filtered holidays
            return filtered_holidays
        
        # If 'contents' field is missing in the response, raise an error
        raise HTTPException(status_code=500, detail="No holiday data found in the response")

    except httpx.RequestError as e:
        # Handle errors with the request, such as network issues
        raise HTTPException(status_code=500, detail=f"Error while making the request: {e}")
    
    except json.JSONDecodeError:
        # Handle cases where the JSON response is not valid
        raise HTTPException(status_code=500, detail="Error decoding the JSON response")
    
    except Exception as e:
        # Catch any other errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

