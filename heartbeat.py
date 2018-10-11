# This module provides a hreatbeat mechanism to help investigate when
# the controller went down, perhaps due to power failure.  It does
# this by periodically touching a file named "heartbeat".

import os
import datetime
import actions
import insteon_logging
from schedule import Every, Event, Scheduler

HEARTBEAT_FILE = "HEARTBEAT"
HEARTBEAT_INTERVAL = datetime.timedelta(seconds=5*60)

def still_alive():
  os.utime(HEARTBEAT_FILE)

def _do_onLoggingStarted_first_heartbeat():
  # Check time of heartbeat file before the Event is schedules.
  try:
    stat = os.stat(HEARTBEAT_FILE)
    insteon_logging.info(
        'Last heartbeat before startup: %s' %
        datetime.datetime.fromtimestamp(stat.st_mtime).
          strftime(insteon_logging._time_format))
  except FileNotFoundError:
    pass
  still_alive()
  Event(still_alive, Every(HEARTBEAT_INTERVAL)).schedule()


