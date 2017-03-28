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
    sentry.py [--speed=<speed>] [--training] [--debug] [(--slack --slack-token=<token> --slack-channel=<channel>)]
    sentry.py [--speed=<speed>] [--capture=<number>]
    sentry.py (-h | --help)
    sentry.py --version

Options:
    -h --help                   Show this screen
    --version                   Show version
    --speed=<speed>             Set playback or record speed in millisecond [default: 2000]
    --training                  Use training sequence located under export
    --capture=<number>          Capture and save a set of images
    --debug                     Display in a window the images used and processed
    --slack                     Send messages for events on slack
    --slack-token=<token>       OAuth token to interact on slack
    --slack-channel=<channel>   Which slack channel to interact on

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
import slack

SPEED = 0

def process_frame(frame, last_frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

    # Init the first frame
    if last_frame is None:
        return gray_frame

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
        print 'Movement detected at {}'.format(now)

        # Save the image
        result = cv2.imwrite('detected/{:%d%m%y%H%M%S}.jpg'.format(now), frame)

    # Update the last frame
    return gray_frame

def play_feed():
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    camera = cv2.VideoCapture(0)
    last_frame = None

    i = 0
    while True:
        frame = None
        if arguments["--training"]:
            frame = cv2.imread("export/{}.jpg".format(i))
            if frame is None:
                return
        else:
            (success, frame) = camera.read()

        # Process the frame
        last_frame = process_frame(frame, last_frame)

        if arguments["--debug"]:
            cv2.imshow("frame",frame)
            cv2.waitKey(int(SPEED))
        else:
            time.sleep(int(SPEED)*1000)
        
        i+=1


    camera.release()

def capture_training(number):
    # Use the video capture
    camera = cv2.VideoCapture(0)

    # Capture number images
    for i in range(0, int(number)):
        (success, frame) = camera.read()
        cv2.imwrite("export/{}.jpg".format(i), frame)
        time.sleep(int(SPEED)*1000)

    camera.release()

# Get the argument dictionnary
arguments = docopt(__doc__, version='Sentry 0.1.1')
SPEED = arguments["--speed"]

if arguments["--capture"] != None:
    capture_training(arguments["--capture"])
else:
    play_feed()
