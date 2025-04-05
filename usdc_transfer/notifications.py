import smtplib
from email.message import EmailMessage
from twilio.rest import Client
import os

def send_email_notification(subject, body, recipient_email):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_user, smtp_password, recipient_email]):
        print("Missing email notification environment variables.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"✅ Email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def send_sms_notification(body, recipient_number):
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([twilio_sid, twilio_token, twilio_number, recipient_number]):
        print("Missing SMS notification environment variables.")
        return

    try:
        client = Client(twilio_sid, twilio_token)
        message = client.messages.create(
            body=body,
            from_=twilio_number,
            to=recipient_number
        )
        print(f"✅ SMS sent to {recipient_number}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
