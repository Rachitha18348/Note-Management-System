import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_email(to_email, username, otp):
    try:
        msg = MIMEMultipart()

        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "OTP Verification"

        body = f"""
Hello {username},

Your OTP is: {otp}

Please use this OTP to verify your email.

Thank you,
Notes Management System
"""

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(
                SMTP_EMAIL,
                to_email,
                msg.as_string()
            )

        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
