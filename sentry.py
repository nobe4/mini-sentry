#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sentry
This is a dead-simple movement detection application with slack notification.
The computer's camera is used to take a picture at a given speed, then use opencv
to detect movement.
When a movement is detected, a picture is uploaded to slack.

Installation/Configuration:
    1. `pip install opencv-python requests docopt`
    2. If you want slack integration set your token and channel accordingly in the command line arguments

Usage:
    sentry.py [--speed=<speed>] [--training] [--debug] [(--slack --slack-token=<token> --slack-channel=<channel>)] [--slack-blind]
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
    --slack-blind               Only send message notification to slack (no images)

LICENSE:
    MIT (see LICENSE file)
"""

import os, sys
import subprocess
import time
from datetime import datetime
from docopt import docopt

import cv2
import requests
import slack

SPEED = 0
SLACK = None

def detected(frame):
    """ Movement was detected, send notification to slack, get the frame where the movement was detected"""
    now = datetime.now()
    image_name = 'detected/{:%d%m%y%H%M%S}.jpg'.format(now)
    result = cv2.imwrite(image_name, frame)

    if SLACK:
        if arguments["--slack-blind"]:
            SLACK.post_message("Alert! A red spy is in the base!! At: {}".format(now))
        else:
            image = open(image_name, "rb")
            SLACK.post_image(image, "Alert! A red spy is in the base!!", "{}".format(now))

# This method is based on the work of Kameda, Y. & Minoh, M. "A human motion
# estimation method using 3-successive video frames."
# The idea is to estimate movement based on the analysis on three frames to
# eliminate ghosting artifacts.
def process_frame(frame_tm1, frame_t, frame_tp1):
    """
    Process the frame to extract movement
    Get previous, under analysis, and next frame as arguments
    Return gray scale version of the next frame and boolean corresponding to movement detection
    """

    gray_frame = cv2.cvtColor(frame_tp1, cv2.COLOR_BGR2GRAY)

    if frame_tm1 is None or frame_t is None:
        return (gray_frame, False)

    
    # Get the difference between t-1 and t, and t and t+1
    diff_image_im1 = cv2.absdiff(frame_tm1, frame_t)
    diff_image_i = cv2.absdiff(frame_t, gray_frame)

    # And between the wo previous images
    double_diff = cv2.bitwise_and(diff_image_im1,diff_image_i);

    # Clean the result a bit
    ret, thres_double_diff = cv2.threshold(double_diff, 40, 255, cv2.THRESH_BINARY)

    # Enough pixel changed but not too much (aka. background change)
    number_changed = cv2.countNonZero(thres_double_diff)
    height, width = thres_double_diff.shape
    nb_pixel = height*width
    if number_changed > nb_pixel * 0.01 and number_changed < nb_pixel * 0.4:
        if arguments["--debug"]:
            cv2.imshow("frame",thres_double_diff)
            cv2.waitKey(0)
        return (gray_frame, True)
    
    return (gray_frame, False)

def play_feed():
    """ Play the video feed, either from file or from camera """
    camera = cv2.VideoCapture(0)
    frame_tm1 = None
    frame_t = None

    if arguments["--debug"]:
        cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

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
        temp, detection = process_frame(frame_tm1, frame_t, frame)
        
        # Alert! A red spy is in the base!!
        if detection:
            detected(frame_t)

        
        frame_tm1 = frame_t;
        frame_t = temp

        if arguments["--debug"]:
            cv2.imshow("frame",frame)
            cv2.waitKey(int(SPEED))
        else:
            time.sleep(int(SPEED)/1000)
        
        i+=1


    camera.release()

def capture_training(number):
    """ Capture a define number of training frames in order to be used later """
    # Use the video capture
    camera = cv2.VideoCapture(0)

    # Capture number images
    for i in range(0, int(number)):
        (success, frame) = camera.read()
        cv2.imwrite("export/{}.jpg".format(i), frame)
        time.sleep(int(SPEED)/1000)

    camera.release()

# Get the argument dictionnary
arguments = docopt(__doc__, version='Sentry 0.1.1')
SPEED = arguments["--speed"]

# Create the slack instance if needs be
if arguments["--slack"]:
    SLACK = slack.slack_instance(arguments["--slack-token"], arguments["--slack-channel"])

if arguments["--capture"]:
    capture_training(arguments["--capture"])
else:
    play_feed()
