# the config module defines configuration parameters used by other
# modules.

import datetime
from tzlocal import get_localzone

TIME_FORMAT = '%Y-%m-%d_%H:%M:%S_%Z'

def now():
  '''Returns the current time as a datetime.datetime, with local timezone.'''
  return datetime.datetime.now(get_localzone())

