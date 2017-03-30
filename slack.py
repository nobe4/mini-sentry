import requests

class slack_instance():
    SLACK_API_LOCATION = "https://slack.com/api/"
    SLACK_API_MESSAGE = "chat.postMessage"
    SLACK_API_FILES = "files.upload"

    def __init__(self, token, channel):
        self.token = token
        self.channel = channel

    def post_message(self, text):
        # Compose arguments
        slack_message_call_args = {
            'token': self.token,
            'channel': self.channel,
            'text': text,
            'as_user': "false",
            'username': "Mini-Sentry",
            'icon_url': "https://wiki.teamfortress.com/w/images/e/ea/Red_Mini_Sentry.png"
        }
        
        r = requests.post(self.SLACK_API_LOCATION+self.SLACK_API_MESSAGE,params=slack_message_call_args)

    def post_image(self, image, comment, title):
        # Compose arguments
        slack_message_call_args = {
            'token': self.token,
            'channels': self.channel,
            "title": title,
            "initial_comment": comment
        }
        
        r = requests.post(self.SLACK_API_LOCATION+self.SLACK_API_FILES,params=slack_message_call_args, files=dict(file=image))
