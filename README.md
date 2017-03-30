![Mini Sentry](http://wiki.teamfortress.com/w/images/e/ea/Red_Mini_Sentry.png)

# Mini Sentry

This is a dead-simple movement detection application with slack notification.

To install, configure and run the script, see [`sentry.py`](https://github.com/nobe4/mini-sentry/blob/master/sentry.py).

# Theory
The detection algorithm is based on the work of Kameda, Y. & Minoh, M. in *"A human motion estimation method using 3-successive video frames."*  
The idea is to compare a frame against the previous and next one, and apply a bitwise and to the result. That way we can remove most of the artifacts of a temporal comparison.  
The movement is then obtained by looking at pixels above a certain threshold in that final and image. In this version, number of pixels changing is also monitored in order to reject case with too many changes (e.g.: major background change, camera movement, etc.)

# License

This script is released under the [MIT License](https://github.com/nobe4/mini-sentry/blob/master/LICENSE).

OpenCV is used in respect with its [3-clause BSD License](http://opencv.org/license.html).

Requests is used in respect with its [Apache License, Version 2.0](http://docs.python-requests.org/en/master/user/intro/#requests-license).

All references to TeamFortress and Valve are properties of their respective owners.
