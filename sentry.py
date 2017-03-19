#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sentry
This is a dead-simple motion tracking with image ~hosting and notification.
The computer's camera is used to take a picture every 5 seconds, then use open
cv to detect the difference and display the contours.

When a contour is found, a picture is uploaded to gist and a message is sent to
slack. The only configuration required is for those two tasks.

Installation/Configuration:
    1. Clone the gist repository, keeping its name
    2. Copy this script inside the gist folder
    3. `pip install opencv-python requests`
    4. Change the slack token and the slack channel below (search for TODO)

Usage:
    sentry.py [--training] [--debug]
    sentry.py (-h | --help)
    sentry.py --version

Options:
    -h --help       Show this screen
    --version       Show version
    --training      Use training sequence located under export
    --debug         Display in a window the images used and processed

LICENSE:
    MIT (see LICENSE file)
"""

import os
import subprocess
import time
from datetime import datetime
from docopt import docopt

import cv2
import requests

# Get the argument dictionnary
arguments = docopt(__doc__, version='Sentry 0.1.1')

# Get the gist id from the current directory
gist_share_url = 'https://gist.github.com/{}'.format(os.path.relpath(".",".."))

# Post a message on the channel with a link to the gist
slack_api_url = 'https://slack.com/api/chat.postMessage'
slack_api_params = {
    'token':   'XXXX', # TODO: Change here !
    'channel': 'XXXX', # TODO: Change here !
    'text':    'WARNING: {}'.format(gist_share_url),
}

# Time to get out!
time.sleep(10)

# Use the video capture
camera = cv2.VideoCapture(0)

# Last frame
last_frame = None

while True:

    # Read a new frame from the camera
    (success, frame) = camera.read()

    # Break on camera not working
    if not success:
        raise Exception('Couldn\'t get the webcam to work')

    # Convert the frame to a blurred gray equivalent for contours detection
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

    # Init the first frame
    if last_frame is None:
        last_frame = gray_frame
        continue

    # Compute the diff With the last frame
    frameDelta = cv2.absdiff(last_frame, gray_frame)

    # Prepare the threshold for finding contours
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Get all contours on the threshold image
    (_, cnts, _) = cv2.findContours(thresh.copy(),
                                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    movement_detected = False

    # Detect significant contours
    for c in cnts:
        if cv2.contourArea(c) < 1000:
            continue

        # Add the contour to the image
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
        movement_detected = True

    # Save the image and notify the user
    if movement_detected:

        # Generate filename
        now = datetime.now()
        filename = '{}.jpg'.format(now)

        print 'Movement detected at {}'.format(now)

        # Save the image
        cv2.imwrite(filename, frame)

        # Add the new file to the gist
        subprocess.call(["git", "add", filename])
        subprocess.call(["git", "commit", "-m", str(now)])
        subprocess.call(["git", "push"])

        # Notify
        r = requests.post(slack_api_url, params=slack_api_params)

    # Update the last frame
    last_frame = gray_frame
    time.sleep(5)

camera.release()
