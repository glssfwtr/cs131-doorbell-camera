"""
objectdetection.py

This script will run on Jetson#2 and is responsible for performing object detection 
on short video clips received from Jetson #1. Jetson #1 performed lightweight motion 
detection and sends clips when motion is detected. Jetson #2 then analyzes these clips 
using a YOLO model and if relevant objects are detected then the clip is uploaded to 
a cloud storage service such as google drive. An email will also be sent to the user
notifying them to check their cloud drive. 

Libraries:
OpenCV (cv2)
os, subprocess (for automation and file handling)
rclone (for cloud uploading)
smtplib/email (for sending email notifications)

Authors: Angel Franco
Date: May 8th, 2025
"""


#implementation will come soon
