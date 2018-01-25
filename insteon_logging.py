# Log messages sent to and from the Insteon modem.

import actions
import logging
import time
from pydispatch import dispatcher


_logger = None

_time_format = '%Y-%m-%d %H:%M:%S %Z'


def _log_modem_command(sender, signal, timestamp, bytes):
  _logger.info("%s: %s %r" % (
    time.strftime(_time_format, timestamp), signal, bytes))


def _log_modem_response(sender, signal, timestamp, bytes):
  _logger.info("%s: %s %r" % (
    time.strftime(_time_format, timestamp), signal, bytes))


# See actions.py.
def _do_onStartup_logging():
  logging.basicConfig(filename='modem.log', level=logging.INFO)
  global _logger
  _logger = logging.getLogger(__name__)

def _do_onShutdown_logging():
  logging.shutdown()

def _do_onStartup_DispatchRegistration():
  dispatcher.connect(_log_modem_command, signal='MODEM_COMMAND')
  dispatcher.connect(_log_modem_response, signal='MODEM_RESPONSE')

