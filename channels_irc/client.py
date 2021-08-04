import logging
import asyncio
from socket import gaierror

from irc.client_aio import AioSimpleIRCClient

from .server import BaseServer

logger = logging.getLogger(__name__)


class ChannelsIRCClient(AioSimpleIRCClient, BaseServer):
    def __init__(self, application, autoreconnect=False, reconnect_delay=60, loop=None):
        self.application = application
        self.autoreconnect = autoreconnect
        self.reconnect_delay = reconnect_delay

        self.reactor = self.reactor_class(loop=loop)
        self.connection = self.reactor.server()
        self.loop = self.reactor.loop

        self.reactor.add_global_handler("all_events", self._dispatcher, -10)
        self.loop.call_later(1, self.futures_checker)

    @property
    def connected(self):
        return getattr(self.connection, 'connected', False)

    def _dispatcher(self, connection, event):
        method = getattr(self, "on_" + event.type, None)

        if method is not None:
            method(connection, event)
        else:
            self._send_application_msg({
                'type': 'irc.receive',
                'command': event.type,
                'body': event.arguments,
                'channel': event.target,
            })

    def on_welcome(self, connection, event):
        """
        Sends `irc.receive` with welcome info
        """
        logger.info('Connected to IRC Server {}:{}'.format(connection.server, connection.port))

        msg = {
            'type': 'irc.receive',
            'command': 'welcome',
            'channel': event.target,
        }
        self._send_application_msg(msg)

    def on_privmsg(self, connection, event):
        """
        Sends message to `irc.receive` with incoming info
        """
        self._handle_on_message(connection, event)

    def on_pubmsg(self, connection, event):
        """
        Sends message to `irc.receive` with incoming info
        """
        self._handle_on_message(connection, event)

    def on_disconnect(self, connection, event):
        """
        Sends message type `irc.disconnected` with disconnected server info
        """
        msg = {
            'type': 'irc.on.disconnect',
            'server': [connection.server, connection.port],
        }
        self._send_application_msg(msg)

    def _handle_on_message(self, connection, event):
        msg = {
            'type': 'irc.receive',
            'command': 'message',
            'user': event.source.nick,
            'channel': event.target,
            'body': event.arguments[0],
        }
        self._send_application_msg(msg)

    def disconnect(self, message=""):
        """
        Disconnects from the current IRC connection
        """
        logger.info("Disconnecting from {}:{}...".format(
            self.connection.server, self.connection.port
        ))
        self.connection.disconnect(message=message)

    async def connect(
        self,  server, port, nickname, is_reconnect=False, *args, **kwargs
    ):
        """
        Instantiates the connection to the server.  Also creates the requisite
        application instance
        """
        scope = {
            'type': 'irc',
            'server': server,
            'port': port,
            'nickname': nickname,
        }
        self.create_application(scope=scope, from_consumer=self.from_consumer)

        try:
            await self.connection.connect(
                server, port, nickname, *args, **kwargs
            )
        except gaierror:
            logger.debug('Connection attempt to {} with user {} failed '.format(
              server, nickname
            ))
        if self.autoreconnect and not is_reconnect:
            self.loop.call_later(self.reconnect_delay, self.reconnect_checker)

    async def from_consumer(self, message):
        """
        Receives message from channels from the consumer.  Message should have the format:
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

    async def _handle_status(self, msg):
        """
        Gets the current status of the IRC Interface server, returns that information to
        channels
        """
        self._send_application_msg({
            'type': 'irc.receive',
            'command': 'status',
            'body': {
                'connected': self.connected,
            },
        })

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
            self.connection.join(self.format_channel_name(channel))

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

        message = msg.get('body', '')
        self.connection.privmsg(self.format_channel_name(channel), message)

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

        if channel:
            self.connection.names(self.format_channel_name(channel))

    async def _handle_part(self, msg):
        """
        Handles PART commands
        """
        channel = msg.get('channel', '')

        if channel:
            self.connection.part(self.format_channel_name(channel))

    async def _handle_disconnect(self, msg):
        """
        a DISCONNECT command should disconnect from the IRC server. Channel msg should be in
        the format:
            {
                'type': 'irc.send',
                'command': 'disconnect',
                'body': <MESSAGE_TEXT>,  # optional disconnect message
            }
        """
        message = msg.get('body', '')
        self.disconnect(message=message)

    async def _handle_cap(self, msg):
        """
        a CAP command handles additional capabilities from the IRC server. Channel msg
        should be in the format:
            {
                'type': 'irc.send',
                'command': 'cap',
                'subcommand': '<ONE OF: LS LIST REQ ACK NAK CLEAR END>',
                'args': [], # optinal string list of additional arguments
            }
        """
        subcommand = msg.get('subcommand')

        if subcommand is not None:
            self.connection.cap(subcommand, *msg.get('args', []))

    def reconnect_checker(self):
        """
        Checks at a regular interval as to whether the connection to IRC has been
        disconnected, and re-starts the connection if it has
        """
        if not self.connected and self.autoreconnect:
            logger.info('Attempting to reconnect to {}:{}'.format(
                self.connection.server, self.connection.port
            ))
            asyncio.ensure_future(
                self.connect(
                    self.connection.server,
                    self.connection.port,
                    self.connection.nickname,
                    password=self.connection.password,
                    username=self.connection.username,
                    ircname=self.connection.ircname,
                    is_reconnect=True,
                ),
                loop=self.loop
            )

        self.loop.call_later(self.reconnect_delay, self.reconnect_checker)

    def start(self):
        super().start()

    def format_channel_name(self, name):
        """
        Adds missing `#` if necessary
        """
        if name is None:
            return name

        return name if name[0] == '#' else '#{}'.format(name)
