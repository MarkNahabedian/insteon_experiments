# This module provides a hreatbeat mechanism to help investigate when
# the controller went down, perhaps due to power failure.  It does
# this by periodically touching a file named "HEARTBEAT".

import os
import datetime
import logging
import actions
import config
from schedule import Every, Event, Scheduler

logging.getLogger(__name__).propagate = True

HEARTBEAT_FILE = "HEARTBEAT"
HEARTBEAT_INTERVAL = datetime.timedelta(seconds=5*60)

def still_alive():
  os.utime(HEARTBEAT_FILE)

def _do_onLoggingStarted_first_heartbeat():
  # Check time of heartbeat file before the Event is schedules.
  try:
    stat = os.stat(HEARTBEAT_FILE)
    logging.getLogger(__name__).info(
        'Last heartbeat before startup: %s' %
        datetime.datetime.fromtimestamp(stat.st_mtime).
          strftime(config.TIME_FORMAT))
  except FileNotFoundError:
    pass
  Event(still_alive, Every(HEARTBEAT_INTERVAL)).schedule()


