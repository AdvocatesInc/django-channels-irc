# Channels-IRC

[![Join the chat at https://gitter.im/django-channels-irc/Lobby](https://badges.gitter.im/django-channels-irc/Lobby.svg)](https://gitter.im/django-channels-irc/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![CircleCI](https://circleci.com/gh/AdvocatesInc/django-channels-irc.svg?style=svg)](https://circleci.com/gh/AdvocatesInc/django-channels-irc)

**Django Channels IRC** is a bridge between IRC and Django's `channels`.  It contains both a new interface server for connecting to IRC and Channels consumers -- everything you need to turn your Django app into an IRC chatbot, chat monitoring/moderating service, or whatever else you might use a real-time IRC client to do.

## Documentation

Full docs available at [django-channels-irc.readthedocs.io](https://django-channels-irc.readthedocs.io/en/latest/)

## Requirements

- [Django Channels 3+](https://channels.readthedocs.io/en/latest/)

## Installation

Install the package from pip:

```bash
pip install channels-irc
```

## Basic Usage

1. Add the library to `INSTALLED_APPS`:

    ```
    INSTALLED_APPS = (
        ...
        'channels_irc',
    )
    ```

2. Create a Consumer

    **Django Channels IRC** contains two consumers for interacting with the IRC Client: `IrcConsumer` and `AsyncIrcConsumer`:

    ```python
    from channels_irc import IrcConsumer

    class MyIrcConsumer(IrcConsumer):
        def welcome(self, channel):
            """
            Optional hook for actions on connection to IRC Server
            """
            print('Connected to server {}:{} with nickname'.format(server, port, nickname)

        def disconnect(self, server, port):
            """
            Optionl hook fr actions on disconnect from IRC Server
            """
            print('Disconnect from server {}:{}'.format(server, port)

        def my_custom_message(self):
            """
            Use built-in functions to send basic IRC messages
            """
            self.send_message('my-channel', 'here is what I wanted to say')

            """
            You can also use built-in functions to send basic IRC commands
            """
            self.send_command('join', channel='some-other-channel')
    ```

3. Add your consumer(s) to your router

    You can use the `irc` type in channels `ProtocolTypeRouter` to connect your new consumer to the interface server, and ensure your `irc` messages are delivered to the right place:

    ```python
    from channels.routing import ProtocolTypeRouter
    from myapp.consumers import MyIrcConsumer

    application = ProtocolTypeRouter({
        'irc': MyIrcConsumer.as_asgi(),
    })
    ```

4. Start the interface server

    The interface server can be started by simply running this in the command line:

    ```bash
    channels-irc
    ```

    The server requires that the `server`, `nickname`, and `application` properties be set. The `application` should be an import string pointing to the location of your app's ASGI application. Hence, if your app was named `myapp`, contained an ASGI filed called `asgi.py`, and your ASGI application is named `my_application`, you could start the server by running:

    ```
    channels-irc -s 'irc.freenode.net' -n 'my_irc_nickname' -a 'myapp.asgi:my_application'
    ```

    You can also set these values using the env variables `CHANNELS_IRC_SERVER`, `CHANNELS_IRC_NICKNAME`, and `CHANNELS_IRC_LAYER`.
