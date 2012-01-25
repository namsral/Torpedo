#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Std libs
import os
import datetime
import json
import logging
import hashlib
import re

# 3rd libs
import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.options
import tornado.httpclient

# Other
re_iso8601 = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z')


# Functions
def gen_deadline(datestring):
    '''
    Calculate the difference between datestring and now.
    Returns a timedelta.
    Requires a ISO 8601 UTC type datestring.
    '''
    # Parse the ISO 8601 UTC datestring
    date = datetime.datetime.strptime(datestring, '%Y-%m-%dT%H:%M:%SZ')
    deadline = date - datetime.datetime.utcnow()
    return deadline


# Objects
class TorpedoException(Exception):
    '''Default Torpedo Exceptoion'''
    pass


class Callback(object):
    """docstring for Callback"""
    __slot__ = ('uuid', 'url', 'eta', 'job', 'callbacks')

    def __init__(self, url, eta, callbacks):
        self.url = url
        self.eta = eta
        self.callbacks = callbacks
        self.uuid = self._gen_uuid()
        self.job = None

    def _gen_uuid(self):
        '''
        Generate a UUID based on the hasf of URL and ETA.
        '''
        return hashlib.sha1(''.join([self.url, self.eta])).hexdigest()

    def make(self):
        '''
        Make the Callback.
        '''
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch(self.url, self._on_response)

    def _on_response(self, response):
        '''
        Act on response from self.make
        '''
        if response.error:
            message = '{uuid}: Callback failed, error: {error}'.format(
                uuid=self.uuid, error=response.error)
            logging.error(message)
        else:
            message = '{uuid}: Callback succeeded'.format(uuid=self.uuid)
            logging.debug(message)

        # Remove callback either way
        callbacks = [i for i in self.callbacks if self.uuid == i.uuid]
        if len(callbacks) > 0:
            self.callbacks.remove(callbacks[0])


# Handlers
class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        if not hasattr(self.application, 'callbacks'):
            self.application.callbacks = list()
        self.callbacks = self.application.callbacks


class RootHandler(BaseHandler):
    def get(self):
        self.write("This is Torpedo.")


class ListOrCreateCallbackHandler(BaseHandler):
    def get(self):
        '''
        List all callbacks.
        '''
        l = [{'uuid':i.uuid, 'url':i.url, 'eta':i.eta} for i in self.callbacks]
        response = json.dumps({'result': l, 'total': len(l)})
        self.write(response)

    def post(self):
        '''
        Add a callback to the ioloop.
        '''
        url = self.get_argument('url')
        eta = self.get_argument('eta')
        try:
            # Basic validation
            if not re_iso8601.match(eta):
                raise TorpedoException('Invalid ISO 8601 UTC datestring.')

            # Create callback
            callback = Callback(url, eta, self.callbacks)

            # Check for duplicates
            callbacks = [i for i in self.callbacks if i.uuid == callback.uuid]
            if len(callbacks) > 0:
                raise TorpedoException('Received duplicate callback.')

            # Create job
            deadline = gen_deadline(eta)
            job = tornado.ioloop.IOLoop.instance().add_timeout(deadline, callback.make)
            callback.job = job
            self.callbacks.append(callback)
            self.write({'url': '/api/callbacks/{uuid}/'.format(uuid=callback.uuid)})
        except TorpedoException, e:
            message = json.dumps({'status': 'failed', 'message': str(e)})
            self._status_code = 500
            self.write(message)


class DeleteCallbackHandler(BaseHandler):
    def delete(self, uuid):
        '''
        Remove a callback from the ioloop.
        '''
        callbacks = [i for i in self.callbacks if uuid == i.uuid]
        if len(callbacks) > 0:
            callback = callbacks[0]
            # Cancel the job from the ioloop
            tornado.ioloop.IOLoop.instance().remove_timeout(callback.job)
            # Remove callback
            self.callbacks.remove(callback)
            self._status_code = 204
            self.finish()
        else:
            raise tornado.web.HTTPError(404)


def main():

    # Register command line options
    tornado.options.define('address', default='127.0.0.1', help='Host address')
    tornado.options.define('port', default=7931, help='Port number')
    tornado.options.define('config', default='/etc/torpedo/torpedo.conf', help='Path to config file')
    tornado.options.define('log', default='torpedo.log', help='Path to log file')
    tornado.options.define('debug', default=False, help="Enable console debugging", type=bool)
    tornado.options.parse_command_line()

    # Read config
    CONFIG = tornado.options.options.config
    if os.access(CONFIG, 4):
        tornado.options.parse_config_file(CONFIG)

    # Options
    TORPEDO_PORT = tornado.options.options.port
    TORPEDO_ADDRESS = tornado.options.options.address
    LOG_PATH = tornado.options.options.log
    DEBUG = tornado.options.options.debug

    # Configure logging
    logger = logging.getLogger()
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        tornado.options.enable_pretty_logging()
    else:
        LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(LOG_FORMAT)
        flog = logging.FileHandler(LOG_PATH)
        flog.setFormatter(formatter)
        logger.addHandler(flog)
        logger.setLevel(logging.ERROR)

    # Setup Tornado
    application = tornado.web.Application(
        [
            (r'/', RootHandler),
            (r'/api/callbacks/', ListOrCreateCallbackHandler),
            (r'/api/callbacks/([a-zA-Z0-9]+)/', DeleteCallbackHandler),
        ],
        debug=DEBUG)
    application.listen(port=TORPEDO_PORT, address=TORPEDO_ADDRESS)

    # Start Tornado
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
        print "Torpedo stopped."


if __name__ == "__main__":
    main()
