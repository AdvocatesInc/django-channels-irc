import sys
import argparse
import logging
import importlib
import os

from .client import ChannelsIRCClient


logger = logging.getLogger(__name__)


class CLI(object):
    """
    Primary command-line interface for irc -> channels bridge
    """
    description = "Django Channels <-> IRC Interface server"

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=self.description,
        )
        self.parser.add_argument(
            '-s',
            '--server',
            dest='server',
            help='IRC server to connect to. Can also be set from CHANNALS_CHATBOT_SERVER env variable',
            default=os.environ.get('CHANNELS_CHATBOT_SERVER', None),
        )
        self.parser.add_argument(
            '-p',
            '--port',
            type=int,
            help=(
                'Port number of IRC server to connect to. Can also be set from '
                'CHANNELS_CHATBOT_PORT env variable. Default is 6667'
            ),
            default=os.environ.get('CHANNELS_CHATBOT_PORT', 6667),
        )
        self.parser.add_argument(
            '-n',
            '--nickname',
            dest='nickname',
            help='Nickname on the IRC server',
            default=os.environ.get('CHANNELS_CHATBOT_NICKNAME', None),
        )
        self.parser.add_argument(
            '--password',
            dest='password',
            help='Password on the IRC server',
            default=os.environ.get('CHANNELS_CHATBOT_PASSWORD', None),
        )
        self.parser.add_argument(
            '--username',
            dest='username',
            help='Username on the IRC server. If none is provided, the value for `nickname` will be used',
            default=None,
        )
        self.parser.add_argument(
            '-r',
            '--realname',
            dest='realname',
            help='Real name on the IRC server.  If none is provided, the value for `nickname will be used',
            default=None,
        )
        self.parser.add_argument(
            '-v',
            '--verbosity',
            type=int,
            help='How verbose to make the output. Default is 1',
            default=1,
        )
        self.parser.add_argument(
            '-c',
            '--channel_layer',
            dest='channel_layer',
            help='The ASGI channel layer instance to use as path.to.module:instance.path',
            default=os.environ.get('CHANNELS_CHATBOT_LAYER', None),
        )

    @classmethod
    def entrypoint(cls):
        """
        Many entrypoint for external starts
        """
        cls().run(sys.argv[1:])

    def run(self, args):
        """
        Mounts the IRC interface server based on the raw arguments passed in
        """
        args = self.parser.parse_args(args)

        # Set up logging
        logging.basicConfig(
            level={
                0: logging.WARN,
                1: logging.INFO,
                2: logging.DEBUG,
            }[args.verbosity],
            format="%(asctime)-15s %(levelname)-8s %(message)s",
        )

        if not any([args.channel_layer, args.server, args.nickname]):
            raise ValueError(
                "--channel_layer, --server, and --nickname are required arguments. "
                "Please add them via the command line or their respective env variables."
            )

        # import the channel layer
        asgi_module, layer_path = args.channel_layer.split(':', 1)
        channel_module = importlib.import_module(asgi_module)
        for part in layer_path.split('.'):
            channel_layer = getattr(channel_module, part)

        client = ChannelsIRCClient(channel_layer)
        client.connect(
            args.server,
            args.port,
            args.nickname,
            password=args.password,
            username=args.username,
            ircname=args.realname
        )

        try:
            client.start()
        except KeyboardInterrupt:
            logger.info("Disconnecting from {}:{}...".format(
                client.connection.server, client.connection.port
            ))
            client.disconnect()
            sys.exit(0)
