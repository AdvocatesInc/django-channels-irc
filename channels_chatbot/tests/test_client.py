from unittest import TestCase
from unittest.mock import patch
from asgiref.inmemory import ChannelLayer as InMemoryChannelLayer

from ..client import ChannelsIRCClient


class MockEvent(object):
    def __init__(self, **kwargs):
        self.source = kwargs.get('source', None)
        self.target = kwargs.get('target', None)
        self.arguments = kwargs.get('arguments', [''])


class MockConnection(object):
    def __init__(self, **kwargs):
        self.server = kwargs.get('server', None)
        self.port = kwargs.get('port', None)


class ChannelsIRCClientTests(TestCase):
    def setUp(self):
        self.channel_layer = InMemoryChannelLayer()

    def assertChannelHasMessage(self, channel_name, msg):
        receive_channel, content = self.channel_layer.receive([channel_name])

        if receive_channel is None:
            self.fail('Expected a message on channel {}, got none'.format(channel_name))

        self.assertEqual(msg, content)

    def test_make_reply_channel(self):
        """
        TODO: add randomized strings to reply channel to allow for multiple client instances
        """
        client = ChannelsIRCClient(self.channel_layer)
        self.assertEqual(client._make_reply_channel(), 'irc-client.send')

    def test_on_welcome(self):
        """
        According to the ASGI spec, when an IRC channel is joined, the client should
        return the a message on the `irc-client.connect` channel
        """
        mock_event = MockEvent()
        mock_connection = MockConnection(server='test.irc.server', port=6667)

        client = ChannelsIRCClient(self.channel_layer)
        client.on_welcome(mock_connection, mock_event)

        self.assertChannelHasMessage('irc-client.connect', {
            'reply_channel': client.reply_channel,
            'server': ['test.irc.server', 6667],
        })

    def test_on_join(self):
        """
        According to the ASGI spec, when an IRC channel is joined, the client should
        return the a message on the `irc-client.join` channel
        """
        mock_event = MockEvent(target='#testchannel')
        mock_connection = MockConnection()

        client = ChannelsIRCClient(self.channel_layer)
        client.on_join(mock_connection, mock_event)

        self.assertChannelHasMessage('irc-client.join', {
            'channel': '#testchannel',
            'reply_channel': client.reply_channel
        })

    def test_handle_on_message(self):
        """
        `privmsg`, `pubmg`, and other messgate-related IRC events should be handled
        b the `_handle_on_message`, which should return the appropriately spec'ed data
        on the `irc-client.receive` channel
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        mock_connection = MockConnection()

        client = ChannelsIRCClient(self.channel_layer)
        client._handle_on_message(mock_connection, mock_event)

        self.assertChannelHasMessage('irc-client.receive', {
            'reply_channel': client.reply_channel,
            'channel': '#testchannel',
            'user': 'testuser',
            'type': 'message',
            'body': 'hello',
        })

    def test_on_pubmsg_calls_handle_on_message(self):
        """
        `on_pubmsg` pass the event and connection to the `_on_handle_message` method
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        mock_connection = MockConnection()

        with patch.object(ChannelsIRCClient, '_handle_on_message') as mock:
            client = ChannelsIRCClient(self.channel_layer)
            client.on_pubmsg(mock_connection, mock_event)

        mock.assert_called_once_with(mock_connection, mock_event)

    def test_on_privmsg_calls_handle_on_message(self):
        """
        `on_privmsg` pass the event and connection to the `_on_handle_message` method
        """
        mock_event = MockEvent(target='#testchannel', source='testuser', arguments=['hello'])
        mock_connection = MockConnection()

        with patch.object(ChannelsIRCClient, '_handle_on_message') as mock:
            client = ChannelsIRCClient(self.channel_layer)
            client.on_privmsg(mock_connection, mock_event)

        mock.assert_called_once_with(mock_connection, mock_event)
