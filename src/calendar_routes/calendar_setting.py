import os
from dotenv import load_dotenv
load_dotenv()

HOLIDAY_PROXY_URL = os.getenv("HOLIDAY_PROXY_URL")
HOLIDAY_TARGET_URL = os.getenv("HOLIDAY_TARGET_URL")