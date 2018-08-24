================
Interface Server
================

The **Django Channels IRC** interface server acts as an IRC Client, converting incoming messages to channels and translating outgoing messages from channels message format to valid IRC messages.  Starting it as simple as running::

    channels-irc

in the command line.

Options
=======

-a, --application     (**Required**) Import string pointing to the project's default ASGI
                      application. Should be in the form of ``path.to.module:instance.path``.
                      It can also be set by the ``CHANNELS_IRC_APPLICATION`` env variable.

--multi               Flag for using the ``MultiConnectionClient`` instead of the default
                      ``ChannelsIRCClient``. This client allows you to create and manage
                      multiple IRC connections, rather than simply auto-connecting to a 
                      single provided server.

-s, --server          (**Required when --multi flag is not used**) This is the address of
                      the IRC server to connect to. It can be also set by the 
                      ``CHANNELS_IRC_SERVER`` env variable

-p, --port            (**Required when --multi flag is not used**) Port number of the IRC server
                      to connect to. It can be also set by the ``CHANNELS_IRC_PORT``
                      env variable

-n, --nickname        (**Required --when multi flag is not used**) Nickname on the IRC Server.
                      This will be used for authentication.  It can also be set by the
                      ``CHANNELS_IRC_NICKNAME`` env variable.

--password            Password for authentication on the IRC Server. 

--username            Username for the IRC Server. If none is provided, the value of
                      ``nickname`` will be used.

-r, --realname        Real name on the IRC Server. If none is provided, the value of
                      for ``nickname`` will be used.

-v, --verbosity       How verbose to make the output.  Valid options are ``0`` (WARN),
                      ``1`` (INFO), and ``2`` (DEBUG).  Default is ``1``

--autoreconnect       Flag to set whether to automatically reconnect to the server if
                      disconnected.  It can also be set with the ``CHANNELS_IRC_RECONNECT``
                      env variable.

--reconnect-delay     Time between reconnection attempts (in seconds).  Default is ``60``.
                      It can also be set with the ``CHANNELS_IRC_RECONNECT_DELAY`` env
                      variable.

