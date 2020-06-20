
# I'd like to be able to show the current status of each device on the
# web page.  We can't poll each device while computing the HTTP
# response because it takes too long for each device to respond.

# We could try to maintain the current status of each defice in
# InsteonDevice.  The web server could then just read the cached
# status from there.  I've looked at using threads or asynchio as the
# infrastructure for maintaining the cached status. # For now, since
# I'm already making minimal use of pydispatch to control the logging
# of traffic to or from the modem, I figured, for now at least, I can
# use it here to trigger reading from the modem whenever the modem is
# written to, and to update InsteonDevice status when a response is
# read back.  This approach would not notice power line traffic
# initiated by controllers other than this software through the
# Insteon modem, but my installation currently has no such use cases.

# The orchestration of that activity through pydispatch is frgoned
# here.

import actions
import modem
import logging
from modem import InsteonModem
from pydispatch import dispatcher


def _do_onInsteonModemInitialized(modem):
  if not isinstance(modem, InsteonModem):
    logging.getLogger(__name__).error(
      "onInsteonModemInitialized action requires an InsteonModem.")
    return
  def read_from_modem_after_writing(
      sender, signal, timestamp, bytes):
    logging.getLogger(__name__).info("read_from_modem_after_writing")
    modem.readResponse()
  def update_device_status_from_incoming_messages(
      sender, signal, timestamp, bytes):
    logging.getLogger(__name__).info("update_device_status_from_incoming_messages")
    modem.process_incoming(bytes)

  logging.getLogger(__name__).info("hash for read_from_modem_after_writing: %d"
                                   % hash(read_from_modem_after_writing))
  logging.getLogger(__name__).info("hash for update_device_status_from_incoming_messages: %d"
                                   % hash(update_device_status_from_incoming_messages))

  dispatcher.connect(read_from_modem_after_writing,
                     weak=False,
                     signal='MODEM_COMMAND')
  dispatcher.connect(update_device_status_from_incoming_messages,
                     weak=False,
                     signal='MODEM_RESPONSE')

  logging.getLogger(__name__).info(
    "dispatcher.getAllReceivers: %r" %
    [d for d in dispatcher.getAllReceivers()])

