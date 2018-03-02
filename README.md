# Channels-Chatbot

A bridge between IRC and Django's `channels`. Built according to the [ASGI IRC spec](https://github.com/django/channels/blob/master/docs/asgi/irc-client.rst)

## Installation

run `python setup.py install` to install the library and set up the command line interface

## Usage

The interface server can be started by simply running the command,

```
channels-chatbot
```

The server requires that the `server`, `nickname`, and `channel_layer` properties be set. The `channel_layer` should be an import string pointing to the location of your app's channel_layer instance.  Hence, if your app was named `myapp`, contained an ASGI filed called `asgi.py`, and your channel_layer is named `my_channel_layer`, you could start the server by running:

```
channels-chatbot -s 'irc.freenode.net' -n 'my_irc_nickname' -c 'myapp.asgi:my_channel_layer'
```

You can also set these values using the env varialbes `CHANNELS_CHATBOT_SERVER`, `CHANNELS_CHATBOT_NICKNAME`, and `CHANNELS_CHATBOT_LAYER`.

## Channels

As specified in the [ASGI IRC spec](https://github.com/django/channels/blob/master/docs/asgi/irc-client.rst), the following channels will be available in your channels-enabled Django app:

```
channel_routing = {
    'irc-client.connect': 'path.to.connect.consumer', # receives messages when client connects to IRC server
    'irc-client.join': 'path.to.join.consumer', # receives messages when client joins an IRC channel
    'irc-client.receive': 'path.to.receive.consumer', # receives messages when client gets an action, message, or notification
}
```

## Options

Full options list coming soon.  For a full list of possible command line options, run

```
channels-chatbot --help
```
