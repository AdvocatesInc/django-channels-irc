from channels.consumer import AsyncConsumer
from channels.exceptions import InvalidChannelLayerError, StopConsumer


class AsyncIrcConsumer(AsyncConsumer):
    """
    Base IRC consumer; Implements basic hooks for interfacing with the IRC Interface Server
    """
    groups = []

    async def on_welcome(self, channel, user=None, body=None):
        """
        Called when the IRC Interface Server connects to the IRC Server
        and receives the "welcome" command from IRC
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_add(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")
        await self.welcome(channel)

    async def welcome(self, channel):
        """
        Hook for any action(s) to be run on connecting to the IRC Server
        """
        pass

    async def irc_on_disconnect(self, message):
        """
        Called when the connection to the IRC Server is closed
        """
        try:
            for group in self.groups:
                await self.channel_layer.group_discard(group, self.channel_name)
        except AttributeError:
            raise InvalidChannelLayerError("BACKEND is unconfigured or doesn't support groups")

        await self.on_disconnect(message['server'][0], message['server'][1])
        raise StopConsumer()

    async def on_disconnect(self, server, port):
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
        await self.send_command('message', channel=channel, body=text)

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


class MultiIrcConsumer(AsyncConsumer):
    """
    Consumer for managing multiple IRC connections.  Used with the `MultiConnectionClient`
    """
    async def irc_multi_init(self, message):
        """
        Called when the consumer is initially loaded.
        """
        await self.on_init()

    async def on_init(self):
        """
        Hook for executing commands on loading the consumer
        """
        pass

    async def send_connect(self, server, port, nickname, **kwargs):
        """
        Creates a new connection, if no connection to that server/nickname
        combination exists.
        """
        await self.send({
            'type': 'irc.multi.connect',
            'server': server,
            'port': port,
            'nickname': nickname,
            **kwargs
        })

    async def send_disconnect(self, server, nickname):
        """
        Disconnects a connnect and removes it from the stored connections
        """
        await self.send({
            'type': 'irc.multi.disconnect',
            'server': server,
            'nickname': nickname,
        })
