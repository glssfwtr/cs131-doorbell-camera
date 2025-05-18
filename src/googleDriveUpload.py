from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from datetime import datetime

# Path to your service account key
SERVICE_ACCOUNT_FILE = 'smart-doorbell.json'

# Google Drive Folder ID
FOLDER_ID = '12B-dUbqpAJavA29yJSD7ZWeNTMaibwlt'

# Auth scopes
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Google Drive API service
service = build('drive', 'v3', credentials=creds)

def upload_video(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    # For now uploads only mp4 but can be expanded
    media = MediaFileUpload(file_path, mimetype='video/mp4')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"Uploaded '{file_name}' with file ID: {uploaded_file.get('id')}")

# Example usage:
if __name__ == '__main__':
    # Edit this line if you want to test another clip
    video_file = 'clips/dummy_test_clip.mp4'
    upload_video(video_file)

