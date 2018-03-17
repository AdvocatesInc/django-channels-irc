from channels.consumer import AsyncConsumer, SyncConsumer
from channels.exceptions import InvalidChannelLayerError, StopConsumer
from asgiref.sync import async_to_sync


class IrcConsumer(SyncConsumer):
    """
    Base IRC consumer; Implements basic hooks for interfacing with the IRC Interface Server
    """
    groups = []

    def irc_connect(self, message):
        """
        Called when the IRC Interface Server connects to the IRC Server
        """
        try:
            for group in self.groups:
                async_to_sync(self.channel_layer.group_add)(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")

        self.connect(
            message['server'][0],
            message['server'][1],
        )

    def connect(self, server, port):
        """
        Hook for any action(s) to be run on connecting to the IRC Server
        """
        pass

    def irc_disconnect(self, message):
        """
        Called when the connection to the IRC Server is closed
        """
        try:
            for group in self.groups:
                async_to_sync(self.channel_layer.group_discard)(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")

        self.disconnect(message['server'][0], message['server'][1])
        raise StopConsumer()

    def disconnect(self, server, port):
        """
        Hook for any action(s) to be run on disconnecting from the IRC Server
        """
        pass

    def irc_receive(self, message):
        """
        Parses incoming messages and routes them to the appropriate handler, depending on the
        incoming action type
        """
        command_type = self.message.get('command', None)

        if command_type is None:
            raise ValueError('An `irc.receive` message must specify a `command` key')

        handler = getattr(self, 'on_{}'.format(command_type), None)

        if handler is not None:
            handler(
                channel=message.get('channel', None),
                user=message.get('user', None),
                body=message.get('body', None),
            )

    def send_message(self, channel, text):
        """
        Sends a PRIVMSG to the IRC Server
        """
        self.send({
            'type': 'irc.send',
            'command': 'message',
            'channel': channel,
            'body': text,
        })


def get_handler_name(message):
    """
    Looks at a message, checks it has a sensible type, and returns the
    handler name for that type.
    """
    # Check message looks OK
    if "type" not in message:
        raise ValueError("Incoming message has no 'type' attribute")
    if message["type"].startswith("_"):
        raise ValueError("Malformed type in message (leading underscore)")
    # Extract type and replace . with _
    return message["type"].replace(".", "_")


class AsyncIrcConsumer(AsyncConsumer):
    """
    Base IRC consumer; Implements basic hooks for interfacing with the IRC Interface Server
    """
    groups = []

    async def irc_connect(self, message):
        """
        Called when the IRC Interface Server connects to the IRC Server
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_add(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")

        await self.connect(
            message['server'][0],
            message['server'][1],
        )

    async def connect(self, server, port):
        """
        Hook for any action(s) to be run on connecting to the IRC Server
        """
        pass

    async def irc_disconnect(self, message):
        """
        Called when the connection to the IRC Server is closed
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_discard(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")

        await self.disconnect(message['server'][0], message['server'][1])
        raise StopConsumer()

    async def disconnect(self, server, port):
        """
        Hook for any action(s) to be run on disconnecting from the IRC Server
        """
        pass

    async def irc_receive(self, message):
        """
        Parses incoming messages and routes them to the appropriate handler, depending on the
        incoming action type
        """
        command_type = message.get('command', None)

        if command_type is None:
            raise ValueError('An `irc.receive` message must specify a `command` key')

        handler = getattr(self, 'on_{}'.format(command_type), None)

        if handler is not None:
            await handler(
                channel=message.get('channel', None),
                user=message.get('user', None),
                body=message.get('body', None),
            )

    async def send_message(self, channel, text):
        """
        Sends a PRIVMSG to the IRC Server
        """
        await self.send({
            'type': 'irc.send',
            'command': 'message',
            'channel': channel,
            'body': text,
        })

    async def send_command(self, command, channel=None, body=None):
        """
        Sends a command to the IRC Server.  Message should be of the format:
            {
                'type': 'irc.command',
                'command': '<IRC_COMMAND>',
                'channel': '<IRC_CHANNEL>',  # Optional, depending on command
                'body': '<COMMAND_TEXT>',  # Optional, depending on command
            }
        """
        await self.send({
            'type': 'irc.send',
            'command': command,
            'channel': channel,
            'body': body,
        })
