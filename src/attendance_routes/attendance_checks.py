import face_recognition
import cv2
import os
from fastapi import UploadFile,Depends,HTTPException,status
import tempfile


import requests
import io
from typing import Union,List,Dict,Optional,Any
from datetime import datetime, date, timedelta
from enum import Enum
from src.common_routes.common_checks import get_supabase_client
from supabase import Client,create_client
import logging
logger = logging.getLogger(__name__)

async def validate_images(img1: UploadFile, img2: Union[UploadFile, str]):
    # Handle img1 (always UploadFile)
    content1 = await img1.read()
    image1 = face_recognition.load_image_file(io.BytesIO(content1))
    
    # Handle img2 (UploadFile or URL string)
    if isinstance(img2, str):  # URL from database
        response = requests.get(img2, timeout=10)
        response.raise_for_status()
        image2 = face_recognition.load_image_file(io.BytesIO(response.content))
    else:  # UploadFile
        content2 = await img2.read()
        image2 = face_recognition.load_image_file(io.BytesIO(content2))
    
    # Face encoding and comparison (same as before)
    enc1 = face_recognition.face_encodings(image1)
    enc2 = face_recognition.face_encodings(image2)
    
    if not enc1 or not enc2:
        return {
            "matched": False,  # Native Python bool
            "error": "No face detected in one or both images"
        }
    
    enc1 = enc1[0]
    enc2 = enc2[0]
    
    distance = face_recognition.face_distance([enc1], enc2)[0]
    matched = distance < 0.6
    
    return {
        "matched": bool(matched),  # Convert numpy.bool_ to Python bool
        "distance": float(round(distance, 3)),  # Convert numpy.float64 to Python float
        "confidence": float(round(1 - distance, 3))  # Convert numpy.float64 to Python float
    }

