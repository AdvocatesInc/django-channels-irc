import logging
from irc.client import SimpleIRCClient, Reactor

logger = logging.getLogger(__name__)

CHANNELS = {
    'connect': 'irc-client.connect',
    'join': 'irc-client.join',
    'receive': 'irc-client.receive',
    'disconnect': 'irc-client.disconnect',
}


class ChannelsReactor(Reactor):
    ACTION_TYPES = ['join', 'part', 'message', 'action']

    def __init__(self, channel_layer, listening_channel):
        super(ChannelsReactor, self).__init__()
        self.listening_channel = listening_channel
        self.channel_layer = channel_layer

    def process_once(self, *args, **kwargs):
        """
        Read messages from channels, then pass of to Reactor for
        IRC data handling
        """
        self._read_channel()
        super(ChannelsReactor, self).process_once(*args, **kwargs)

    def _read_channel(self):
        """
        get messages from channels, route to the appropriate action
        """
        channel, msg = self.channel_layer.receive([self.listening_channel], block=False)
        if channel:
            action_type = msg.get('type', '').lower()

            if not action_type and action_type not in self.ACTION_TYPES:
                logger.error('"{}" is not a valid action type for the IRC Client')
                return

            handler = getattr(self, '_handle_{}'.format(action_type))
            handler(msg)

    def _handle_join(self, msg):
        """
        Makes join call as requested from channels.  Channel msg should be in format:
            {
                'channel': <CHANNEL_NAME>,
                'reply_channel': <REPLY_CHANNEL_NAME>,
            }
        """
        channel = msg.get('channel', '')

        if channel:
            channel = channel if channel[0] == '#' else '#{}'.format(channel)

            for c in self.connections:
                c.join(channel)

    def _handle_message(self, msg):
        """
        Posts a message to the passed channel from Django channels. Channel msg should be in format:
            {
                'channel': <CHANNEL_NAME>,
                'reply_channel': <REPLY_CHANNEL_NAME>,
                'body': <MESSAGE_TEXT>,
            }
        """
        channel = msg.get('channel', '')

        if channel:
            channel = channel if channel[0] == '#' else '#{}'.format(channel)
            message = msg.get('body', '')

            for c in self.connections:
                c.privmsg(channel, message)


class ChannelsIRCClient(SimpleIRCClient):
    reactor_class = ChannelsReactor

    def __init__(self, channel_layer):
        self.channel_layer = channel_layer
        self.reply_channel = self._make_reply_channel()
        self.reactor = self.reactor_class(channel_layer, self.reply_channel)
        self.connection = self.reactor.server()
        self.dcc_connections = []
        self.reactor.add_global_handler("all_events", self._dispatcher, -10)
        self.reactor.add_global_handler(
            "dcc_disconnect",
            self._dcc_disconnect, -10)

    # def _dispatcher(self, connection, event):
        # print(event)
        # super(ChannelsIRCClient, self)._dispatcher(connection, event)

    def _make_reply_channel(self):
        return 'irc-client.send'

    def _send_channel_msg(self, channel_name, msg):
        """
        sends a msg (serializable dict) to the appropriate Django channel
        """
        return self.channel_layer.send(channel_name, msg)

    def on_welcome(self, connection, event):
        """
        Sends message to `irc-client.connect` Channel
        """
        channel_name = CHANNELS['connect']
        msg = {
            'reply_channel': self.reply_channel,
            'server': [connection.server, connection.port],
        }
        self._send_channel_msg(channel_name, msg)

    def on_join(self, connection, event):
        """
        Sends message to `irc-client.join` Channel
        """
        channel_name = CHANNELS['join']
        msg = {
            'reply_channel': self.reply_channel,
            'channel': event.target,
        }
        self._send_channel_msg(channel_name, msg)

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
        Sends message to `irc-client.disconect` with disconnected server info
        """
        channel_name = CHANNELS['disconnect']
        msg = {
            'reply_channel': self.reply_channel,
            'server': [connection.server, connection.port],
        }
        self._send_channel_msg(channel_name, msg)

    def _handle_on_message(self, connection, event):
        channel_name = CHANNELS['receive']
        msg = {
            'reply_channel': self.reply_channel,
            'type': 'message',
            'user': event.source,
            'channel': event.target,
            'body': event.arguments[0],
        }
        self._send_channel_msg(channel_name, msg)

    def disconnect(self, message=""):
        """
        Disconnects from IRC server
        """
        self.connection.disconnect(message=message)
