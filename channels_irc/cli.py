import sys
import argparse
import logging
import importlib
import os
import asyncio

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
            help='IRC server to connect to. Can also be set from CHANNALS_IRC_SERVER env variable',
            default=os.environ.get('CHANNELS_IRC_SERVER', None),
        )
        self.parser.add_argument(
            '-p',
            '--port',
            type=int,
            help=(
                'Port number of IRC server to connect to. Can also be set from '
                'CHANNELS_IRC_PORT env variable. Default is 6667'
            ),
            default=os.environ.get('CHANNELS_IRC_PORT', 6667),
        )
        self.parser.add_argument(
            '-n',
            '--nickname',
            dest='nickname',
            help='Nickname on the IRC server',
            default=os.environ.get('CHANNELS_IRC_NICKNAME', None),
        )
        self.parser.add_argument(
            '--password',
            dest='password',
            help='Password on the IRC server',
            default=os.environ.get('CHANNELS_IRC_PASSWORD', None),
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
            '-a',
            '--application',
            dest='application',
            help='The application to dispatch to as path.to.module:instance.path',
            default=os.environ.get('CHANNELS_IRC_APPLICATION', None),
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

        if not all([args.application, args.server, args.nickname]):
            raise ValueError(
                "--application, --server, and --nickname are required arguments. "
                "Please add them via the command line or their respective env variables."
            )

        # import the channel layer
        asgi_module, application_path = args.application.split(':', 1)
        application_module = importlib.import_module(asgi_module)
        for part in application_path.split('.'):
            application = getattr(application_module, part)

        client = ChannelsIRCClient(application)

        logger.info('Connecting to IRC Server {}:{}'.format(args.server, args.port))

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

            loop = client.reactor.loop

            tasks = asyncio.gather(
                *asyncio.Task.all_tasks(loop=loop),
                loop=loop,
                return_exceptions=True
            )
            tasks.add_done_callback(lambda t: loop.stop())
            tasks.cancel()

            while not tasks.done() and not loop.is_closed():
                loop.run_forever()
        finally:
            loop.close()
            sys.exit(0)
