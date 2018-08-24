from unittest.mock import patch

from channels.testing import ApplicationCommunicator

from .utils import AsyncTestCase, AsyncMock, async_test
from ..consumers import AsyncIrcConsumer


class AsyncIrcConsumerTests(AsyncTestCase):
    @patch('channels_irc.consumers.AsyncIrcConsumer.welcome', new_callable=AsyncMock)
    @async_test
    async def test_on_welcome(self, mock_welcome):
        """
        `irc.receive` called with a `welcome` command should call the
        `on_welcome`
        """
        communicator = ApplicationCommunicator(AsyncIrcConsumer, {'type': 'irc'})

        await communicator.send_input({
            'type': 'irc.receive',
            'command': 'welcome',
            'channel': 'test_channel',
            'user': 'my_nick',
            'body': None,
        })

        await communicator.wait(timeout=.2)
        self.assertEqual(mock_welcome.call_count, 1)

    @async_test
    async def test_send_command(self):
        """
        `send_command` should format the correct message and return it to the
        server
        """
        communicator = ApplicationCommunicator(AsyncIrcConsumer, {'type': 'irc'})

        # Give the loop a beat to initialize the instance
        await communicator.receive_nothing(timeout=.2)

        await communicator.instance.send_command('join', channel='my_channel')

        event = await communicator.receive_output(timeout=1)
        self.assertEqual(event, {
            'type': 'irc.send',
            'command': 'join',
            'channel': 'my_channel',
            'body': None,
        })

    @async_test
    async def test_send_message(self):
        """
        `send_message` should format the correct message and return it to the
        server
        """
        communicator = ApplicationCommunicator(AsyncIrcConsumer, {'type': 'irc'})

        # Give the loop a beat to initialize the instance
        await communicator.receive_nothing(timeout=.2)

        await communicator.instance.send_message('my_channel', 'Hello IRC!')

        event = await communicator.receive_output(timeout=1)
        self.assertEqual(event, {
            'type': 'irc.send',
            'command': 'message',
            'channel': 'my_channel',
            'body': 'Hello IRC!',
        })
