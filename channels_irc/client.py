import logging
import asyncio
import traceback

from asgiref.sync import sync_to_async
from irc.client import SimpleIRCClient, Reactor

logger = logging.getLogger(__name__)


class ChannelsReactor(Reactor):
    def __init__(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()
        super().__init__(*args, **kwargs)

    async def process_once_loop(self, timeout=0):
        """
        Transfers the process_once function to the asyncio event loop
        """
        while True:
            await asyncio.sleep(0)
            await sync_to_async(self.process_once)(timeout)

    def process_forever(self, timeout=0.2):
        """
        Use asyncio as event loop instead of select-based loop
        """
        self.process_future = asyncio.ensure_future(self.process_once_loop(timeout), loop=self.loop)
        self.loop.run_forever()


class ChannelsIRCClient(SimpleIRCClient):
    reactor_class = ChannelsReactor

    def __init__(self, application):
        self.application = application

        super().__init__()

    def _dispatcher(self, connection, event):
        method = getattr(self, "on_" + event.type, None)

        if method is not None:
            method(connection, event)
        else:
            self._send_application_msg({
                'type': 'irc.receive',
                'command': event.type,
                'args': event.arguments,
                'channel': event.target,
            })

    def _send_application_msg(self, msg):
        """
        sends a msg (serializable dict) to the appropriate Django channel
        """
        return self.application_queue.put_nowait(msg)

    def on_welcome(self, connection, event):
        """
        Sends `irc.connect` message type
        """
        logger.info('Connected to IRC Server {}:{}'.format(connection.server, connection.port))

        msg = {
            'type': 'irc.connect',
            'server': [connection.server, connection.port],
        }
        self._send_application_msg(msg)

    def on_privmsg(self, connection, event):
        """
        Sends message to `irc-client.receive` with incoming info
        """
        self._handle_on_message(connection, event)

    def on_pubmsg(self, connection, event):
        """
        Sends message to `irc-client.receive` with incoming info
        """
        self._handle_on_message(connection, event)

    def on_disconnect(self, connection, event):
        """
        Sends message type `irc-client.disconect` with disconnected server info
        """
        msg = {
            'type': 'irc.disconnect',
            'server': [connection.server, connection.port],
        }
        self._send_application_msg(msg)

    def _handle_on_message(self, connection, event):
        msg = {
            'type': 'irc.receive',
            'command': 'message',
            'user': event.source,
            'channel': event.target,
            'body': event.arguments[0],
        }
        self._send_application_msg(msg)

    def disconnect(self, message=""):
        """
        Disconnects from IRC server
        """
        self.connection.disconnect(message=message)

    def connect(self, server, port, nickname, *args, **kwargs):
        """
        Instantiates the connection to the server.  Also creates the requisite
        application instance
        """
        application_instance = self.application(scope={
            'type': 'irc',
            'server': server,
            'port': port,
            'nickname': nickname,
        })
        self.application_queue = asyncio.Queue()
        self.application_instance = asyncio.ensure_future(application_instance(
            receive=self.application_queue.get,
            send=self.from_application),
            loop=self.reactor.loop
        )
        super().connect(server, port, nickname, *args, **kwargs)

    async def from_application(self, message):
        """
        Receives message from channels from the applications.  Message should have the format:
            {
                'type': 'irc.send',
                'command': VALID_COMMAND_TYPE
            }
        """
        if "type" not in message:
            raise ValueError("Message has no type defined")

        elif message['type'] == 'irc.send':
            command_type = message.get('command', '').lower()

            handler = getattr(self, '_handle_{}'.format(command_type))
            await handler(message)

        else:
            raise ValueError("Cannot handle message type %s!" % message["type"])

    async def _handle_join(self, msg):
        """
        Makes join call as requested from channels.  Channels msg should be in format:
            {
                'type': 'irc.send',
                'command': 'join',
                'channel': <CHANNEL_NAME>,
            }
        """
        channel = msg.get('channel', '')

        if channel:
            channel = channel if channel[0] == '#' else '#{}'.format(channel)
            self.connection.join(channel)

    async def _handle_message(self, msg):
        """
        Posts a message to the passed channel from Django channels. Channel msg should be in format:
            {
                'type': 'irc.send',
                'command': 'message',
                'channel': <CHANNEL_NAME>,
                'body': <MESSAGE_TEXT>,
            }
        """
        channel = msg.get('channel', '')

        channel = channel if channel[0] == '#' else '#{}'.format(channel)
        message = msg.get('body', '')
        self.connection.privmsg(channel, message)

    async def _handle_names(self, msg):
        """
        Posts a NAMES request to the passed channel from Django channels.
        Channel msg should be in the format:
            {
                'type': 'irc.send',
                'command': 'names',
                'channel': <CHANNEL_NAME>,
            }
        """
        channel = msg.get('channel', '')
        channel = channel if channel[0] == '#' else '#{}'.format(channel)

        self.connection.names(channel)

    async def _handle_part(self, msg):
        """
        Handles PART commands
        """
        channel = msg.get('channel', '')
        channel = channel if channel[0] == '#' else '#{}'.format(channel)

        self.connection.part(channel)

    def futures_checker(self):
        """
        Looks for exeptions raised in the application or irc loops
        """
        for future in [self.application_instance, self.reactor.process_future]:
            if future.done():
                try:
                    exception = future.exception()
                except asyncio.CancelledError:
                    # Future cancellation. We can ignore this.
                    pass
                else:
                    if exception:
                        exception_output = "{}\n{}{}".format(
                            exception,
                            "".join(traceback.format_tb(
                                exception.__traceback__,
                            )),
                            "  {}".format(exception),
                        )
                        print(exception_output)
                        logger.error(
                            "Exception inside application: %s",
                            exception_output,
                        )
                        self.disconnect()

        self.reactor.loop.call_later(1, self.futures_checker)

    def start(self):
        self.reactor.loop.call_later(1, self.futures_checker)
        super().start()
