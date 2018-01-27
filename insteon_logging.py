# Log messages sent to and from the Insteon modem.

import actions
import logging
import time
from translator import interpret_all, Pattern, ReadFromModem
from pydispatch import dispatcher


_logger = None

_time_format = '%Y-%m-%d %H:%M:%S %Z'

_signal_abbreviations = {
  'MODEM_COMMAND': 'H',  # Sent from host to modem.
  'MODEM_RESPONSE': 'm'  # Sent or relayed from modem to host.
}

_signal_translators = {
  'MODEM_COMMAND': Pattern,
  'MODEM_RESPONSE': ReadFromModem
}


def _log_modem_traffic(sender, signal, timestamp, bytes):
  entry_list = ["%s: %s %r" % (
    time.strftime(_time_format, timestamp),
    _signal_abbreviations[signal],
    bytes)]
  interpreted = []
  try:
    interpreted, _, _ = interpret_all(bytes, _signal_translators[signal])
  except e:
    entry_list.append(str(e))
  finally:
    entry = '\n\t'.join(entry_list + [repr(i) for i in interpreted])
  _logger.info(entry)


# See actions.py.
def _do_onStartup_logging():
  logging.basicConfig(filename='modem.log', level=logging.INFO)
  global _logger
  _logger = logging.getLogger(__name__)

def _do_onShutdown_logging():
  logging.shutdown()

def _do_onStartup_DispatchRegistration():
  dispatcher.connect(_log_modem_traffic, signal='MODEM_COMMAND')
  dispatcher.connect(_log_modem_traffic, signal='MODEM_RESPONSE')

