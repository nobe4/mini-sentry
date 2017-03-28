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
            'as_user': "true"
        }
        
        r = requests.post(self.SLACK_API_LOCATION+self.SLACK_API_MESSAGE,params=slack_message_call_args)
        print r