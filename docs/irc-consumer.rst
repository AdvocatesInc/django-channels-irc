=============
IRC Consumers
=============

**Django Channels IRC** provides the ``AsyncIrcConsumer``, which provides
basic functionality for interacting with the IRC Server.

Built-in Methods
================

``welcome(self, nickname)`` (**async**)

Called when the ``welcome`` command is received from IRC.  This function
is an optional hook for your consumer to take specific actions immediately
after connecting to IRC

``on_disconnect(self, server, port`` (**async**)

Called when the ``quit`` command is received from IRC.  This function
is an optional hook for your consumer to take specific actions immediately
after disconnecting from IRC.

``send_message(self, channel, text)`` (**async**)

Sends a ``privmsg`` command to IRC, with the ``channel`` paramter as the
target channel and the ``text`` parameter as the body.

``send_command(self, command, channel=None, body=None)`` (**async**)

Sends a command to IRC.  Whether ``channel`` and ``body`` are required
depends on the particular command.  For example, to join the channel
``my-super-fun-channel``, call::

    await self.send_command('join', channel='my-super-fun-channel')

Adding Handlers
===============

The outcoming messages can be handled by the built-in methods.  However,
handlers must be created for responding to incoming IRC messages/commands.
You can do that be adding a function to the consumer with the name 
``on_{COMMAND_NAME}``.  For example, to create a function that runs after
a channel is joined, you could write::

    from channels_irc.consumers import AsyncIrcConsumer

    MyConsumer(AsyncIrcConsumer):
        async def on_join(self, channel, user, body):
            print("You just joined the channel {}".format(channel) 

Handlers generally use the command name straight from the IRC spec (e.g.
``join``, ``part``, ``names``).  One except is ``privmsg`` and ``pubmsg``
commands, which have been funneled to a single ``message`` command.  To 
process incoming messages, use the ``on_message`` handler::
    
    MyConsumer(AsyncIrcConsumer):
        async def on_message(self, channel, user, body):
            print("User {} just posted {} to channel {}".format(
                user, body, channel
            )

**NOTE**: Ping/Pong messages and responses are handled automatically
by the client.  You should only need to write a specific ``ping``
handler if you need some extra functionality besides send the ``pong``
response back
