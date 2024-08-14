#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import requests

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
INVOICE_ID = os.getenv('INVOICE_ID')
API_URL = os.getenv('API_URL').replace('$INVOICE_ID', INVOICE_ID)
API_KEY = os.getenv('API_KEY')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH')
EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT')
EMAIL_BODY = os.getenv('EMAIL_BODY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))

def download_invoice():
    headers = {'Authorization': f'Token {API_KEY}'}
    response = requests.get(API_URL, headers=headers, stream=True)
    if response.status_code == 200:
        with open(DOWNLOAD_PATH, 'wb') as file:
            file.write(response.content)
        print("Invoice downloaded successfully.")
    else:
        print(f"Failed to download invoice. Status code: {response.status_code}")

def send_email(subject, body, to_email, attachment_file):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    try:
        with open(attachment_file, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={attachment_file}')
        msg.attach(part)

        # Send the email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"Email sent to {to_email}")

    except smtplib.SMTPException as e:
        print(f"Failed to send email. SMTP Error: {e}")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
    finally:
        try:
            server.quit()
        except UnboundLocalError:
            print("Server connection was not established; no need to quit.")

if __name__ == "__main__":
    download_invoice()
    send_email(EMAIL_SUBJECT, EMAIL_BODY, RECIPIENT_EMAIL, DOWNLOAD_PATH)
