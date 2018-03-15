import asyncio

from unittest import TestCase
from unittest.mock import patch

from ..consumers import AsyncIrcConsumer
from ..client import ChannelsIRCClient
from .utils import async_test


class MockEvent(object):
    def __init__(self, **kwargs):
        self.source = kwargs.get('source', None)
        self.target = kwargs.get('target', None)
        self.arguments = kwargs.get('arguments', [''])
        self.type = kwargs.get('type', None)


class MockConnection(object):
    def __init__(self, **kwargs):
        self.server = kwargs.get('server', None)
        self.port = kwargs.get('port', None)


class ChannelsIRCClientTests(TestCase):
    @patch('irc.client.SimpleIRCClient.connect')
    def setUp(self, mock_connect):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.client = ChannelsIRCClient(AsyncIrcConsumer)
        self.client.connect('test.irc.server', 6667, 'advogg')

        self.mock_connection = MockConnection(server='test.irc.server', port=6667)

    def tearDown(self):
        tasks = asyncio.gather(
            *asyncio.Task.all_tasks(loop=self.loop),
            loop=self.loop,
            return_exceptions=True
        )
        tasks.add_done_callback(lambda t: self.loop.stop())
        tasks.cancel()

        while not tasks.done() and not self.loop.is_closed():
            self.loop.run_forever()

        self.loop.close()

    @async_test
    async def test_on_welcome(self):
        """
        According to the ASGI spec, when an IRC channel is joined, the client should
        return the a message on the `irc.connect` channel
        """
        mock_event = MockEvent()
        self.client.on_welcome(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.connect',
            'server': ['test.irc.server', 6667],
        })

    @async_test
    async def test_on_join(self):
        """
        `join` doesn't have a specific in client handler, so it should send the generic 'irc.receive'
        with the relevant information
        """
        mock_event = MockEvent(target='#testchannel', type='join', args=[])
        self.client._dispatcher(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.receive',
            'command': 'join',
            'channel': '#testchannel',
            'args': [''],
        })

    @async_test
    async def test_handle_on_message(self):
        """
        `privmsg`, `pubmg`, and other messgate-related IRC events should be handled
        b the `_handle_on_message`, which should return the appropriately spec'ed data
        on the `irc.receive` channel
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        self.client._handle_on_message(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.receive',
            'channel': '#testchannel',
            'user': 'testuser',
            'command': 'message',
            'body': 'hello',
        })

    @async_test
    async def test_on_pubmsg_calls_handle_on_message(self):
        """
        `on_pubmsg` pass the event and connection to the `_on_handle_message` method
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        self.client.on_pubmsg(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.receive',
            'channel': '#testchannel',
            'user': 'testuser',
            'command': 'message',
            'body': 'hello',
        })

    @async_test
    async def test_on_privmsg_calls_handle_on_message(self):
        """
        `on_privmsg` pass the event and connection to the `_on_handle_message` method
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        self.client.on_privmsg(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.receive',
            'channel': '#testchannel',
            'user': 'testuser',
            'command': 'message',
            'body': 'hello',
        })
