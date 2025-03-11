import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")


def send_training_completion_email(user_email, project_label):
    """Sends an email notification when training is completed."""
    subject = f"🎉 Your Model Training is Complete: {project_label}"

    body = f"""
    Hi {user_email.split('@')[0]},

    Your fine-tuned model for "{project_label}" has successfully completed training! 🎯

    You can now generate images using your model.

    Next Steps:
    - Visit the dashboard to generate images using text prompts.
    - Ensure you use the project label "{project_label}" as the trigger word in your prompts.
    - Experiment with different prompt variations to get the best results.

    🚀 Happy Generating!
    """

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email sent to {user_email}")
            return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False
