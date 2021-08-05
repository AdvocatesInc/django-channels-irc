============
Channels-IRC
============

A bridge between IRC and Django's ``channels``. 

Installation
============

run ``pip install channels_irc`` to install the library and set up the command line interface

Documentation
=============

Full docs available at `django-channels-irc.readthedocs.io
<https://django-channels-irc.readthedocs.io/en/latest/>`_.

Requirements
============

- `Django Channels 3+
  <https://channels.readthedocs.io/en/latest/>`_

Usage
=====

Follow these steps to set up **Django Channels IRC** in your project

Add to INSTALLED_APPS
=====================

Add the library to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'channels_irc',
    )

Create a Consumer
=================

**Django Channels IRC** contains two consumers for interacting with the 
IRC interface server: ``IrcConsumer`` and ``AsyncIrcConsumer``::

    from channels_irc import IrcConsumer

    class MyIrcConsumer(IrcConsumer):
        def welcome(self, channel):
            """
            Optional hook for actions on connection to IRC Server
            """
            print('Connected to IRC with nickname'.format(nickname)

        def disconnect(self, server, port):
            """
            Optionl hook for actions on disconnect from IRC Server
            """
            print('Disconnect from server {}:{}'.format(server, port)

        def my_custom_message(self):
            """
            Use built-in functions to send basic IRC messages
            """
            self.send_message('my-channel', 'here is what I wanted to say')

        def my_custom_command(self):
            """
            You can also use built-in functions to send basic IRC commands
            """
            self.send_command('join', channel='some-other-channel')

Add your consumer(s) to your router
===================================

You can use the ``irc`` type in channels ``ProtocolTypeRouter`` to connect
your new consumer to the interface server, and ensure
your ``irc`` messages are delivered to the right place::

    from channels.routing import ProtocolTypeRouter
    from myapp.consumers import MyIrcConsumer

    application = ProtocolTypeRouter({
        'irc': MyIrcConsumer.as_asgi(),
    })

Start the interface server
==========================

The interface server can be started by simply running this in the command line::

    channels-irc

The server requires that the ``server``, ``nickname``, and ``application`` properties be 
set. The ``application`` should be an import string pointing to the location of 
your app's ASGI application. Hence, if your app was named ``myapp``, contained an
ASGI file called ``asgi.py``, and your ASGI application is named ``my_application``,
you could start the server by running::

    channels-irc -s 'irc.freenode.net' -n 'my_irc_nickname' -a 'myapp.asgi:my_application'

You can also set these values using the env variables 
``CHANNELS_IRC_SERVER``, ``CHANNELS_IRC_NICKNAME``, and ``CHANNELS_IRC_LAYER``.
