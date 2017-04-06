#/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sentry
This is a dead-simple movement detection application with slack notification.
The computer's camera is used to take a picture at a given speed, then use opencv
to detect movement.
When a movement is detected, a picture is uploaded to slack.

Installation/Configuration:
    1. `pip install -r requirements.txt`
    2. If you want slack integration set your token and channel accordingly in the command line arguments.

Usage:
    sentry.py [--speed=<speed>] [--use-training] [--debug] [(--slack-token=<token> --slack-channel=<channel>)] [--slack-blind]
    sentry.py [--speed=<speed>] --train [ --frame_number=<number>]
    sentry.py (-h | --help)
    sentry.py --version

Options:
    -h --help                   Show this screen
    --version                   Show version
    --speed=<speed>             Set playback or record speed in millisecond [default: 1000]
    --use-training              Use saved training sequence
    --train                     Save pictures locally for training use
    --frame_number=<number>     Number of frame to consider [default: 10]
    --debug                     Display in a window the images used and processed
    --slack-token=<token>       OAuth token to interact on slack
    --slack-channel=<channel>   Which slack channel to interact on
    --slack-blind               Only send message notification to slack (no image)

LICENSE:
    MIT (see LICENSE file)
"""

import os
import time
from datetime import datetime
from docopt import docopt
import cv2

from slack import slack_post

SENTRY_VERSION = '1.0.0'


class Sentry():

    def __init__(self,
                 speed=1000,
                 slack_token=None, slack_channel=None, slack_blind=False,
                 training_folder='training', export_folder='export',
                 debug=False, use_training=False,
                 ):
        '''Init the class, setup slack and configure the different options.'''

        self.speed = float(speed) / 1000.0

        # Use slack only if both the token and the channel are provided
        if slack_token and slack_channel:
            self.slack = slack_post(slack_token, slack_channel, slack_blind)
        else:
            self.slack = None

        # Get the camera now, and save it in the object
        self.camera = cv2.VideoCapture(0)

        # Images folder
        self.training_folder = training_folder
        self.export_folder = export_folder

        # Create the folders if they don't exist.
        if not os.path.exists(training_folder):
            os.makedirs(training_folder)
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        # Debug means showing the result in a window, which can fail depending
        # on your OS.
        try:
            cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            self.debug = True
        except Exception:
            self.debug = False

        self.use_training = use_training

    def __del__(self):
        '''On the class deletion, remember to release the camera.'''
        if self.camera:
            self.camera.release()

    def get_frames(self, frame_number=float('inf')):
        '''Generate frames from the camera or the training.'''

        # Counter, to keep track fo the current requested picture
        index = 0

        while index < frame_number:

            # Are we using training data or the camera?
            if self.use_training:
                frame = cv2.imread(
                    "{}/{}.jpg".format(self.training_folder, index))
                if frame is None:
                    return
            else:
                (success, frame) = self.camera.read()

            yield (frame, index)

            index += 1

            # Debug and wait for the next frame
            if self.debug:
                cv2.imshow("frame", frame)
                cv2.waitKey(self.speed * 1000)
            else:
                time.sleep(self.speed)

    def train(self, frame_number=10):
        '''Capture some training frames for debugging purpose.'''

        for frame, index in self.get_frames(int(frame_number)):
            cv2.imwrite("{}/{}.jpg".format(self.training_folder, index), frame)

    def alert(self, frame):
        '''Send an alert message to slack, and possibly a picture.'''
        # Use the current time for the filename
        now = datetime.now().strftime('%y-%m-%dT%H-%M-%S')

        alert_message = "Alert! A red spy is in the base! At: {}".format(now)
        print alert_message

        # Save the image using a comprehensive filename using ISO 8601
        image_name = '{}.jpg'.format(now)
        image_path = '{}/{}'.format(self.export_folder, image_name)

        # Write the file to disk
        result = cv2.imwrite(image_path, frame)

        # Send a message to slack, and a picture, if needed
        if self.slack:
            # The image posting could fail, let it fail, but don't break the
            # program.
            try:
                image = open(image_path, "rb")
                self.slack(alert_message, image_name, image)
            except Exception as e:
                print e
                pass

    def process_frame(self, frame_tm1, frame_t, frame_tp1):
        '''Process the frame to extract movement. Get previous, under analysis,
        and next frame as arguments. Return gray scale version of the next
        frame and boolean corresponding to movement detection.

        Based on on the work of Kameda, Y. & Minoh, M. "A human motion
        estimation method using 3-successive video frames." The idea is to
        estimate movement based on the analysis on three frames to eliminate
        ghosting artifacts.

        The three arguments are three frames, respectively at t-1, t and t+1.
        '''

        # Convert the last frame to a grayscale version of it
        gray_frame_tp1 = cv2.cvtColor(frame_tp1, cv2.COLOR_BGR2GRAY)

        # If none fo the t-1 and t frames are present, return the gray frame,
        # without detection.
        if frame_tm1 is None or frame_t is None:
            return (gray_frame_tp1, False)

        # Get the difference between t-1 and t, and t and t+1
        diff_image_im1 = cv2.absdiff(frame_tm1, frame_t)
        diff_image_i = cv2.absdiff(frame_t, gray_frame_tp1)

        # And between the two differences
        double_diff = cv2.bitwise_and(diff_image_im1, diff_image_i)

        # Clean the result a bit
        ret, thres_double_diff = cv2.threshold(
            double_diff, 40, 255, cv2.THRESH_BINARY)

        # How much pixels have changed?
        number_changed = cv2.countNonZero(thres_double_diff)

        # How many pixels is there on the shape?
        height, width = thres_double_diff.shape
        pixel_count = height * width

        # If we have enough pixel changed, but not too much: a movement is
        # detected
        movement_detected = number_changed > pixel_count * 0.01 and \
            number_changed < pixel_count * 0.4

        return (gray_frame_tp1, movement_detected)

    def capture(self):
        '''Capture images and send them to the detection function.'''

        frame_tm1 = None
        frame_t = None

        i = 0
        for frame, index in self.get_frames():

            temp, detected = self.process_frame(frame_tm1, frame_t, frame)

            if detected:
                self.alert(frame_t)

            # Update the current and past frames
            frame_tm1 = frame_t
            frame_t = temp

            i += 1


if __name__ == '__main__':

    arguments = docopt(__doc__, version='Sentry {}'.format(SENTRY_VERSION))

    sentry = Sentry(
        speed=arguments.get('--speed'),
        slack_token=arguments.get('--slack-token'),
        slack_channel=arguments.get('--slack-channel'),
        slack_blind=arguments.get('--slack-blind'),
        debug=arguments.get('--debug'),
        use_training=arguments.get('--use-training'),
    )

    # We're only training for a number of frame, not
    if arguments.get("--train"):
        sentry.train(arguments.get('--frame_number'))
    else:
        sentry.capture()
