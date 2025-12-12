from supabase import Client
import secrets
import string
import os
from supabase import create_client
from fastapi import APIRouter, HTTPException, status, Depends
import aiosmtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .common_setting import SUPABASE_URL, SUPABASE_ANON_KEY,SMTP_HOST,SMTP_PORT,SMTP_USERNAME,SMTP_PASSWORD
import smtplib
import ssl
from jinja2 import Template
import logging
from passlib.context import CryptContext
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")





async def generate_user_based_password(
    name: str,
    email: str,
    length: int = 16,
) -> str:
    """
    Generate a random password that loosely uses user details
    (e.g., initials, domain), but is still mostly random.
    """
    try:

        # Character pools
        letters = string.ascii_letters
        digits = string.digits
        specials = "!@#$%^&*()-_=+"

        # 1) Derive a few deterministic bits from user data (optional flavor)
        name_part = (name.strip().split(" ")[0][:3] or "usr").title()
        email_user = (email.split("@")[0][:3] or "acc").lower()

        base = name_part + email_user  # e.g., "Rajraj" or "Samdev"

        # 2) Fill the rest with secure random characters
        remaining_len = max(length - len(base), 8)  # enforce minimum randomness
        pool = letters + digits + specials

        random_tail = "".join(secrets.choice(pool) for _ in range(remaining_len))

        # 3) Mix and shuffle
        raw = (base + random_tail)[:length]
        # Shuffle characters to avoid predictable prefix
        chars = list(raw)
        secrets.SystemRandom().shuffle(chars)

        return "".join(chars)
    except Exception as e:
        logger.error("Error generating password for name=%s email=%s: %s", name, email, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate password",
        )



def get_supabase_client() -> Client:
    try:
        logger.debug("Creating Supabase client for user routes")
        url = SUPABASE_URL
        key = SUPABASE_ANON_KEY # use service key for writes [web:161]
        print(f"Supabase URL: {url}, Key: {key}")
        if not url or not key:
            logger.warning("Supabase URL or key not configured")
            raise RuntimeError("Supabase URL/key not configured")
        return create_client(url, key)
    except RuntimeError as re:
        raise re
    except Exception as e:
        logger.error("Error creating Supabase client: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Supabase client",
        )




async def send_email(template_path, data, receiver_email,subject, smtp_server, smtp_port, username, password):
    try:
        # Load HTML template
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()

        # Render template with data using Jinja2
        template_obj = Template(template)
        email_body = template_obj.render(**data)

        

        # Build email message
        msg = MIMEMultipart('alternative')
        msg['From'] = username
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg['Return-Path'] = username  # bounce address
        msg['Delivery-Status-Notification'] = 'Success, Failure'
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))

        # Create SSL context
        context = ssl.create_default_context()

        # Connect to SMTP server over SSL (port 465)
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.set_debuglevel(0)  # Set to 0 in production, 1 for debugging
            server.login(username, password)
            server.send_message(msg)

        print(f"Email sent successfully to {receiver_email}!")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False
        