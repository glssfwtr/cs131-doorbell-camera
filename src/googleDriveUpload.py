from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Path to service account key
SERVICE_ACCOUNT_FILE = 'smart-doorbell.json'

# Google Drive Folder ID
FOLDER_ID = '12B-dUbqpAJavA29yJSD7ZWeNTMaibwlt'

# Auth scopes
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Google Drive API service
service = build('drive', 'v3', credentials=creds)

# load env file
load_dotenv()

# Notifications
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')

# Sends notifications
def send_email_notification(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Notification sent to {EMAIL_RECEIVER}")
    
    except Exception as e:
        print(f"Email failed: {e}")

# Uploads the video
def upload_video(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='video/x-msvideo')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id,webViewLink'
    ).execute()

    file_link = uploaded_file.get('webViewLink')
    print(f"Uploaded '{file_name}' with file ID: {uploaded_file.get('id')}")

    # Send email
    send_email_notification(
        subject="Doorbell Clip Uploaded",
        body=f"A new video '{file_name}' was uploaded.\nView it here:\n{file_link}"
    )


if __name__ == '__main__':
    # Edit this line if you want to test another clip
    video_file = 'clips/motion_20250517_154955.avi'
    upload_video(video_file)

