from unittest.mock import patch, Mock
from irc.client import NickMask

from ..consumers import AsyncIrcConsumer
from ..client import ChannelsIRCClient
from .utils import async_test, AsyncTestCase


class MockEvent(object):
    def __init__(self, **kwargs):
        self.source = NickMask(kwargs.get(
            'source', 'axiologue!axiologue@axiologue.tmi.twitch.tv'
        ))
        self.target = kwargs.get('target', None)
        self.arguments = kwargs.get('arguments', [''])
        self.type = kwargs.get('type', None)


class MockConnection(object):
    def __init__(self, **kwargs):
        self.server = kwargs.get('server', None)
        self.port = kwargs.get('port', None)


class ChannelsIRCClientTests(AsyncTestCase):
    @patch('irc.client.SimpleIRCClient.connect')
    def setUp(self, mock_connect):
        super().setUp()

        self.client = ChannelsIRCClient(AsyncIrcConsumer)
        self.loop.run_until_complete(self.client.connect('test.irc.server', 6667, 'advogg'))
        self.client.connection.send_raw = Mock()

        self.mock_connection = MockConnection(server='test.irc.server', port=6667)

    @async_test
    async def test_on_welcome(self):
        """
        According to the ASGI spec, when an IRC channel is joined, the client should
        return the a message on the `irc.connect` channel
        """
        mock_event = MockEvent(target='test-channel')
        self.client.on_welcome(self.mock_connection, mock_event)

        response = await self.client.application_queue.get()

        self.assertEqual(response, {
            'type': 'irc.receive',
            'channel': 'test-channel',
            'command': 'welcome',
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
            'body': [''],
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

    @async_test
    async def test_handle_join_calls_send_raw(self):
        """
        `_handle_join` should take the Channels message and send the appropriate join
        to IRC
        """
        join_msg = {
            'type': 'irc.send',
            'command': 'join',
            'channel': '#advogg',
        }

        await self.client._handle_join(join_msg)

        self.client.connection.send_raw.assert_called_with('JOIN #advogg')

    @async_test
    async def test_handle_join_adds_missing_hashtag(self):
        """
        `_handle_join` should add # to the channel name if it's missing
        """
        join_msg = {
            'type': 'irc.send',
            'command': 'join',
            'channel': 'advogg',
        }

        await self.client._handle_join(join_msg)

        self.client.connection.send_raw.assert_called_with('JOIN #advogg')

    @async_test
    async def test_handle_join_does_nothing_if_no_channel_is_specified(self):
        """
        `_handle_join` should not be called if no channel is given
        """
        join_msg = {
            'type': 'irc.send',
            'command': 'join',
        }

        await self.client._handle_join(join_msg)

        self.client.connection.send_raw.assert_not_called()

    @async_test
    async def test_handle_message_calls_send_raw(self):
        """
        `_handle_message` should call `send_raw` with the appropriate PRIVMSG text
        """
        privmsg = {
            'type': 'irc.send',
            'command': 'message',
            'channel': 'advogg',
            'body': 'Hello World!',
        }

        await self.client._handle_message(privmsg)

        self.client.connection.send_raw.assert_called_with('PRIVMSG #advogg :Hello World!')

    @async_test
    async def test_handle_part_calls_send_raw(self):
        """
        `_handle_part` should call `send_raw` with the appropriate PART message
        """
        part_msg = {
            'type': 'irc.send',
            'command': 'part',
            'channel': 'advogg',
        }

        await self.client._handle_part(part_msg)

        self.client.connection.send_raw.assert_called_with('PART #advogg')
