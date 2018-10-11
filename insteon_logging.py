# Log messages sent to and from the Insteon modem.

import actions
import logging
import datetime
import schedule
from translator import interpret_all, Pattern, ReadFromModem
from pydispatch import dispatcher


LOG_FILE = 'modem.log'

_logger = None

_time_format = '%Y-%m-%d %H:%M:%S %Z'


def info(message):
  '''Add message to the log.'''
  if _logger:
    _logger.info('%s: %s' % (
      schedule.now().strftime(_time_format),
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
    timestamp.strftime(_time_format),
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
  logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
  global _logger
  _logger = logging.getLogger(__name__)
  info('LOGGING STARTED')
  actions.run('onLoggingStarted')

def _do_onShutdown_logging():
  logging.shutdown()

def _do_onStartup_DispatchRegistration():
  dispatcher.connect(_log_modem_traffic, signal='MODEM_COMMAND')
  dispatcher.connect(_log_modem_traffic, signal='MODEM_RESPONSE')

