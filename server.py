import os
from os.path import join, dirname

import cherrypy
from cherrypy import tools
from dotenv import load_dotenv
from pyfcm import FCMNotification

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
ENVIRONMENT = os.environ.get('ENVIRONMENT')
FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY')
WEBHOOK_TOKEN = os.environ.get('WEBHOOK_TOKEN')

push_service = FCMNotification(api_key=FCM_SERVER_KEY)


class ZendeskPush(object):
    @cherrypy.expose
    @tools.json_out()
    @cherrypy.tools.json_in()
    def callback(self, token=None):
        if token is None:
            cherrypy.response.status = 401
            return {'detail': 'Authentication credentials were not provided.'}
        if token != WEBHOOK_TOKEN:
            cherrypy.response.status = 401
            return {'detail': 'Invalid token'}

        data = cherrypy.request.json
        devices = data.get('devices')
        notification = data.get('notification')
        errors = {}
        if not devices:
            errors['devices'] = 'This field is required'
        elif not all('identifier' in device for device in devices):
            errors['devices'] = 'Invalid format'
        if not notification:
            errors['notification'] = 'This field is required'
        elif not all(key in notification for key in ['body', 'title', 'ticket_id']):
            errors['notification'] = 'Invalid format'

        if errors:
            cherrypy.response.status = 400
            return errors

        registration_ids = list(device['identifier'] for device in devices)
        message_title = notification['title']
        message_body = notification['body']
        message_data = {
            'zendesk_sdk_request_id': notification['ticket_id']
        }
        result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title,
                                                      message_body=message_body, data_message=message_data)

        return result


def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"


if __name__ == '__main__':
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    push = ZendeskPush()

    config = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 9020,
            'server.thread_pool': 10,
            'environment': ENVIRONMENT,
        },
        '/': {
            'tools.CORS.on': True,
        }
    }
    cherrypy.quickstart(push, '/push', config=config)
