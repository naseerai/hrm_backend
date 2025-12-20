from pydantic import BaseModel
from typing import Optional, List

class HolidayUpdate(BaseModel):
    id: str                     # required to match the row
    name: Optional[str] | None = None
    holiday_date: Optional[str] | None = None   # ISO date string
    description: Optional[str] | None = None
    holiday_type: Optional[str] | None = None
    


class HolidayCreate(BaseModel):
    name: str                      # Required for creation
    holiday_date: str              # Required for creation
    description: Optional[str] = None
    holiday_type: Optional[str] = None
    year: str
    