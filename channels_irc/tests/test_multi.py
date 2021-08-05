import asyncio
from unittest.mock import patch, MagicMock

from django.test import TestCase

from ..client import ChannelsIRCClient
from ..consumers import MultiIrcConsumer
from ..multi import MultiConnectionClient
from .utils import AsyncMock


class MultiConnectionClientTests(TestCase):
    def make_fake_client(self):
        client = ChannelsIRCClient(MagicMock)
        client.application_instance = asyncio.Future()
        return client

    async def test_send_init(self):
        """
        On creating a new instance of `MultiConnectionClient` it should
        send the `irc.multi.init` message
        """
        client = MultiConnectionClient(MultiIrcConsumer())

        response = await client.application_queue.get()
        self.assertEqual(response, {'type': 'irc.multi.init'})

    @patch('channels_irc.multi.ChannelsIRCClient.connect', new_callable=AsyncMock)
    async def test_creating_new_connection(self, mock_connect):
        """
        Sending a `irc.multi.connect` message to the `MultiConnectionClient`
        should spin up a new connection with the appropriate server, nickname, etc,
        and add it to the connections dict
        """
        msg = {
            'type': 'irc.multi.connect',
            'server': 'my.test.server',
            'port': 6667,
            'nickname': 'my_nick',
        }

        client = MultiConnectionClient(MultiIrcConsumer())

        self.assertEqual(len(client.connections), 0)
        await client.from_consumer(msg)

        self.assertEqual(len(client.connections), 1)
        self.assertIn('my.test.server:my_nick', client.connections)

        mock_connect.assert_called_with(
            'my.test.server', 6667, 'my_nick',
        )

    @patch('channels_irc.multi.ChannelsIRCClient.disconnect', new_callable=AsyncMock)
    async def test_disconnecting(self, mock_disconnect):
        """
        Sending a `irc.multi.disconnect` message to the `MultiConnectionClient`
        should disconnect the connection and remove it from the connections dict
        """
        msg = {
            'type': 'irc.multi.disconnect',
            'server': 'my.test.server',
            'port': 6667,
            'nickname': 'my_nick',
        }

        client = MultiConnectionClient(MultiIrcConsumer())

        client.connections = {
            'my.test.server:my_nick': self.make_fake_client(),
            'my.test.server:other_nick': self.make_fake_client(),
        }
        self.assertEqual(len(client.connections), 2)
        await client.from_consumer(msg)

        self.assertEqual(len(client.connections), 1)
        self.assertNotIn('my.test.server:my_nick', client.connections)

        self.assertEqual(mock_disconnect.call_count, 1)
