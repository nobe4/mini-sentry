#/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from collections import OrderedDict

def slack_post(token, channel, blind=False):
    '''Post a slack message possibly with a picture. Prepare a function that
    will be called later by the main script.'''
    slack_api_url = 'https://slack.com/api/{}'

    params = {
        'token': token,
        'channel': channel,
    }

    if blind:
        params.update({
            'as_user': 'false',
            'username': 'Mini-Sentry',
            'icon_url': 'https://wiki.teamfortress.com/w/images/e/ea/Red_Mini_Sentry.png'
        })
        url = slack_api_url.format('chat.postMessage')
    else:
        params['channels'] = params.pop('channel')
        url = slack_api_url.format('files.upload')

    def make_request(*args):
        '''Will make the request, use the prepared params.'''
        request_args = OrderedDict(
            url=url,
            params=params,
        )

        if blind:
            request_args['params'].update({
                'text': args[0]
            })
        else:
            request_args['params'].update({
                'title': args[0],
                'initial_comment': args[1],
            })
            request_args['files'] = dict(file=args[2])

        response = requests.post(**request_args)

    return make_request
