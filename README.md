# Channels-IRC

A bridge between IRC and Django's `channels`. Built according to the [ASGI IRC spec](https://github.com/django/channels/blob/master/docs/asgi/irc-client.rst)

## Installation

run `python setup.py install` to install the library and set up the command line interface

## Usage

The interface server can be started by simply running the command,

```
channels-irc
```

The server requires that the `server`, `nickname`, and `application` properties be set. The `application` should be an import string pointing to the location of your app's ASGI application. Hence, if your app was named `myapp`, contained an ASGI filed called `asgi.py`, and your ASGI application is named `my_application`, you could start the server by running:

```
channels-irc -s 'irc.freenode.net' -n 'my_irc_nickname' -a 'myapp.asgi:my_application'
```

You can also set these values using the env variables `CHANNELS_IRC_SERVER`, `CHANNELS_IRC_NICKNAME`, and `CHANNELS_IRC_LAYER`.

## IRC Consumers

`channels_irc` is comes with the `IrcConsumer` and the `AsyncIrcConsumer` for bootstrapping IRC connection handling.

```
from channels_irc import IrcConsumer

class MyConsumer(IrcConsumer):
    def connect(self, server, port, nickname):
        """
        Optional hook for actions on connection to IRC Server
        """
        print('Connected to server {}:{} with nickname'.format(server, port, nickname)

    def disconnect(self, server, port):
        """
        Optionl hook fr actions on disconnect from IRC Server
        """
        print('Disconnect from server {}:{}'.format(server, port)

    def my_custom_action(self):
        """
        Use built-in functions to send basic IRC commands
        """
        self.message('my-channel', 'here is what I wanted to say')
```

Make sure to use `irc` as the protocol in the `ProtocolTypeRouter`

```
from channels.routing import ProtocolTypeRouter

from my_irc_app.consumers import MyConsumer


application = ProtocolTypeRouter({
    'irc': MyConsumer,
})
```
