import asyncio
import traceback
import logging

logger = logging.getLogger(__name__)


class BaseServer:
    """
    Base class for common interface server functions, including
    creating an application, sending to the consumer, and application_checking/
    error handling
    """

    def _send_application_msg(self, msg):
        """
        sends a msg (serializable dict) to the appropriate Django channel
        """
        return self.application_queue.put_nowait(msg)

    def noop_from_consumer(self, msg):
        """
        empty default for receiving from consumer
        """

    def create_application(self, scope={}, from_consumer=noop_from_consumer):
        """
        Handles creating the ASGI application and instatiating the
        send Queue
        """
        self.application_queue = asyncio.Queue()
        application_instance = self.application(
            scope=scope,
            receive=self.application_queue.get,
            send=from_consumer
        )
        self.application_instance = asyncio.ensure_future(
            application_instance, loop=self.loop,
        )

    def futures_checker(self):
        """
        Looks for exeptions raised in the application or irc loops
        """
        if getattr(self, 'application_instance', False) and self.application_instance.done():
            try:
                exception = self.application_instance.exception()
            except asyncio.CancelledError:
                # Future cancellation. We can ignore this.
                pass
            else:
                if exception:
                    exception_output = "{}\n{}{}".format(
                        exception,
                        "".join(traceback.format_tb(
                            exception.__traceback__,
                        )),
                        "  {}".format(exception),
                    )
                    logger.error(
                        "Exception inside application: %s",
                        exception_output,
                    )
                    self.disconnect()

                del self.application_instance
                self.application_instance = None

        self.loop.call_later(1, self.futures_checker)
