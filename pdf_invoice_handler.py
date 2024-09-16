#!/usr/bin/env python3

import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
api_key = os.getenv('API_KEY')
headers = {'Authorization': f'Token {api_key}'}
organisation_id = os.getenv('ORGANISATION_ID')
download_dir = os.getenv('DOWNLOAD_PATH', '.')
recipient_email = os.getenv('RECIPIENT_EMAIL')
sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))

api_url = 'https://api.divio.com/apps/v3/invoices/'

# Ensure the download directory exists
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Disable loading environment settings of .netrc auth for the session
session = requests.Session()
session.trust_env = False

def get_first_invoice():
    """Fetches the first invoice from the API."""
    invoice_receipt_url = f'{api_url}?organisation={organisation_id}&page=1'
    
    response = session.get(invoice_receipt_url, headers=headers)
    if response.status_code == 200:
        invoices = response.json().get('results', [])
        if invoices:
            return invoices[0]  # Return the first invoice only
        else:
            raise Exception("No invoices found.")
    else:
        raise Exception(f"Failed to retrieve invoices. Status code: {response.status_code}")

def download_invoice_pdf(receipt_url, invoice_id):
    """Downloads the PDF invoice by appending '.pdf' to the receipt URL."""
    pdf_url = f"{receipt_url}.pdf"  # Access the PDF by appending '.pdf' to the receipt URL
    response = session.get(pdf_url, allow_redirects=True)
    
    if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
        filename = f"invoice_{invoice_id}.pdf"
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'wb') as file:  # Save the PDF in binary mode
            file.write(response.content)
        print(f"Invoice {invoice_id} saved successfully as PDF: {filename}")
        return filepath
    else:
        raise Exception(f"Failed to download the invoice. Status code: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")

def send_email_with_attachment(subject, body, to_email, attachment_file):
    """Sends an email with the invoice attached as PDF."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF invoice file
    with open(attachment_file, 'rb') as f:  # Open the PDF in binary mode for attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_file)}')
    msg.attach(part)

    # Send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to secure
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        print(f"Email sent to {to_email}")
    finally:
        server.quit()

if __name__ == "__main__":
    try:
        # Step 1: Get the first invoice
        first_invoice = get_first_invoice()
        receipt_url = first_invoice.get('receipt')  # Assuming the receipt contains the base URL
        invoice_id = first_invoice.get('number') or first_invoice.get('uuid')

        # Step 2: Download the invoice PDF from the modified URL
        pdf_file = download_invoice_pdf(receipt_url, invoice_id)

        # Step 3: Send the email with the attached PDF invoice
        email_subject = f"Invoice {invoice_id}"
        email_body = f"Please find attached your invoice #{invoice_id}."
        send_email_with_attachment(email_subject, email_body, recipient_email, pdf_file)
    
    except Exception as e:
        print(f"Error: {e}")
