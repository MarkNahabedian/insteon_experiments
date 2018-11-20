# Log messages sent to and from the Insteon modem.

import actions
import logging
import datetime
import config
import config
from translator import interpret_all, Pattern, ReadFromModem
from pydispatch import dispatcher

logging.getLogger(__name__).propagate = True

def info(message):
  '''Add message to the log.'''
  logging.getLogger(__name__).info('%s: %s' % (
    config.now().strftime(config.TIME_FORMAT),
    message))


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
    timestamp.strftime(config.TIME_FORMAT),
    _signal_abbreviations[signal],
    bytes)]
  interpreted = []
  try:
    interpreted, _, _ = interpret_all(bytes, _signal_translators[signal])
  except e:
    entry_list.append(str(e))
  finally:
    entry = '\n\t'.join(entry_list + [repr(i) for i in interpreted])
  logging.getLogger(__name__).info(entry)

def _do_onShutdown_logging():
  logging.shutdown()

def _do_onStartup_DispatchRegistration():
  dispatcher.connect(_log_modem_traffic, signal='MODEM_COMMAND')
  dispatcher.connect(_log_modem_traffic, signal='MODEM_RESPONSE')

