import cherrypy
from telebot import TeleBot, types

from config import WEBHOOK_LISTEN, WEBHOOK_PORT, WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV


class WebhookServer(object):
    bot = None

    def __init__(self, bot: TeleBot):
        self.bot = bot

        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)

        cherrypy.config.update({
            'server.socket_host': WEBHOOK_LISTEN,
            'server.socket_port': WEBHOOK_PORT,
            'server.ssl_module': 'builtin',
            'server.ssl_certificate': WEBHOOK_SSL_CERT,
            'server.ssl_private_key': WEBHOOK_SSL_PRIV
        })

    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = types.Update.de_json(json_string)
            self.bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)
