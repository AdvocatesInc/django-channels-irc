import asyncio

from .client import ChannelsIRCClient
from .server import BaseServer


class MultiConnectionClient(BaseServer):
    def __init__(self, application, autoreconnect=False, reconnect_delay=60, loop=None):
        self.application = application
        self.autoreconnect = autoreconnect
        self.reconnect_delay = reconnect_delay

        self.loop = loop if loop is not None else asyncio.get_event_loop()

        # dictionary of 'SERVER:NICKNAME': ChannelsIRCClient
        self.connections = {}

        self.create_application(
            scope={'type': 'irc.multi'}, from_consumer=self.from_consumer
        )
        self.send_init()
        self.loop.call_later(1, self.futures_checker)

    def start(self):
        self.loop.run_forever()

    def send_init(self):
        """
        Sent when the applcation is initialized.
        Used as a hook for creating any automatic connections
        """
        self._send_application_msg({
            'type': 'irc.multi.init',
        })

    async def from_consumer(self, message):
        """
        Receives message from channels from the consumer.
        """
        if 'type' not in message:
            raise ValueError('Message has no type defined')

        elif message['type'] == 'irc.multi.connect':
            await self.create_connection(**message)

        elif message['type'] == 'irc.multi.disconnect':
            await self.remove_connection(message['server'], message['nickname'])

        else:
            raise ValueError("Cannot handle message type %s!" % message["type"])

    def get_connection_key(self, server, nickname):
        """
        cretes the key for a connection in `self.connections`
        """
        return '{}:{}'.format(server, nickname)

    async def create_connection(self, server, port, nickname, **kwargs):
        """
        Create an instance of `ChannelsIRCClient`, and store it in self.connections
        under the key of `SERVER:NICKNAME`.  To ensure idempotency, it first checks
        whether the connection exists and is already connected before attempt to
        start a new connection
        """
        key = self.get_connection_key(server, nickname)
        connection = self.connections.get(key, None)

        if connection is None or not connection.connected:
            client = ChannelsIRCClient(
                self.application, autoreconnect=self.autoreconnect,
                reconnect_delay=self.reconnect_delay, loop=self.loop
            )

            kwargs.pop('type')
            await client.connect(server, port, nickname, **kwargs)

            self.connections[key] = client

    async def remove_connection(self, server, nickname):
        """
        Shuts down the connection, clean up tasks, remove from self.connections
        """
        key = self.get_connection_key(server, nickname)

        connection = self.connections.get(key)

        if connection is not None:
            connection.disconnect()

            if not connection.application_instance.done():
                connection.application_instance.cancel()
                await asyncio.wait([connection.application_instance])

            self.connections.pop(key, None)
            connection = None

    def disconnect(self):
        """
        Disconnect from all active connections
        """
        for connection in self.connections.values():
            connection.disconnect()
