from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Path to service account key
SERVICE_ACCOUNT_FILE = 'smart-doorbell.json'

# Google Drive Folder ID
FOLDER_ID = '12B-dUbqpAJavA29yJSD7ZWeNTMaibwlt'

# Prevent duplicates from uploading
VIDEO_FOLDER = '/home/immortal/good'
UPLOADED_LOG = 'uploaded.log'

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
    media = MediaFileUpload(file_path, mimetype='video/mp4')

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

# Creates an uploaded file set to prevent adding the same videos
def load_uploaded():
    if not os.path.exists(UPLOADED_LOG):
        return set()
    with open(UPLOADED_LOG, 'r') as f:
        return set(line.strip() for line in f)

# Marks a file
def mark_uploaded(file_name):
    with open(UPLOADED_LOG, 'a') as f:
        f.write(file_name + '\n')

# Constantly watches for a new file to upload every 5 seconds
def watch_and_upload():
    print(f"Watching folder: {VIDEO_FOLDER}")
    uploaded = load_uploaded()

    while True:
        for file in os.listdir(VIDEO_FOLDER):
            if file.endswith('.mp4') and file not in uploaded:
                full_path = os.path.join(VIDEO_FOLDER, file)
                upload_video(full_path)
                uploaded.add(file)
                mark_uploaded(file)
        time.sleep(5)  # check every 5 seconds

if __name__ == '__main__':
    watch_and_upload()
