# Scheduling events for home automation.

import datetime
import logging
import numbers
import sys
import threading
import config
import translator
from singleton import Singleton

logging.getLogger(__name__).propagate = True

if sys.version_info < (3,):
  from Queue import PriorityQueue, Empty
else:
  from queue import PriorityQueue, Empty


def timedelta_to_seconds(td):
  return td.seconds + td.days * 60 * 60 * 24 + td.microseconds/1000000


class Scheduler(Singleton):
  empty_queue_wait_time = datetime.timedelta(minutes=5)
  
  def __init__(self):
    if 'schedule_queue' in self.__dict__:
      return
    self.schedule_queue = PriorityQueue()
    self.event = threading.Event()
    self.action_thread = threading.Thread(name='Scheduler Thread',
                                          target=self)
    self.action_thread.daemon = True,
    self.event.set()
    self.action_thread.start()

  def schedule(self, when, action):
    '''schedule causes action to be performed according to the specified when.'''
    self.schedule_queue.put((when, action))
    _log_scheduler_message(scheduler_operation='EVENT_SCHEDULED',
                           sender=self,
                           timestamp=config.now(),
    	                   when=when,
                           action=action)
    # wake up the consumer thread.
    self.event.set()

  def __call__(self):
    self.consumer()
    
  def consumer(self):
    # Is it time to perform the next Event?
    self.event.clear()
    while True:
      try:
        event = self.schedule_queue.get_nowait()
      except Empty:
        self.event.wait(timedelta_to_seconds(self.__class__.empty_queue_wait_time))
        continue
      if event[0] <= config.now():
        success = False
        now_ = config.now()
        try:
          event[1]()
          event[1].schedule(previous=event[0])
          success = True
        except Exception as e:
          # TODO Include the error in the log.
          _log_scheduler_message(scheduler_operation='SCHEDULED_ACTION_FAILED',
                                 sender=self,
                                 timestamp=now_,
  	                         when=event[0],
                                 action=event[1])
        if success:
          _log_scheduler_message(scheduler_operation='SCHEDULED_ACTION_DONE',
                                 sender=self,
                                 timestamp=now_,
  	                         when=event[0],
                                 action=event[1])
        self.schedule_queue.task_done()
      else:
        # Not ripe yet, put it back.
        self.schedule_queue.put(event)
        self.event.wait(timedelta_to_seconds(event[0] - config.now()))
        

# Event next_time_function
class Every(object):
  '''Every provides an Event next_time_function that schedules a periodic
      event with a fixed timedelta in between Events.'''
  def __init__(self, interval):
    if not isinstance(interval, datetime.timedelta):
      raise Exception('%r is not a timedelta.' % interval)
    self.interval = interval

  def __repr__(self):
    return 'Every(%r)' % self.interval

  def __call__(self, now=config.now(), previous=None):
    '''Returns the next time that this should occur.'''
    if previous:
      return previous + self.interval
    return now


# Event next_time_function
class DailyAt(object):
  '''DailyAt is a function that returns the next datetime (after now)
     having the specified hour and minute.'''
  delta = datetime.timedelta(days=1)

  def __init__(self, hour, minute):
    self.hour = hour
    self.minute = minute

  def __repr__(self):
    return 'DailyAt(%r, %r)' % (self.hour, self.minute)

  def __call__(self, now=config.now(), previous=None):
    '''Returns the next time that this should occur.'''
    if previous:
      assert previous <= now
    at = datetime.datetime(now.year, now.month, now.day,
                           self.hour, self.minute,
                           now.second, 0, now.tzinfo)
    if at > now:
      return at
    return at + self.__class__.delta


# Event next_time_function
class TimeOffset(object):
  '''TimeOffset is a function that adds an offset (in pinutes) to
     the result of another scheduling function.  It can be used to add
     an offset to another computed time like sunrise or sunset.
     minutes can either be a number of minutes or a function returning
     a number of minutes.  That function will be called once each time
     the related event is scheduled.'''

  def __init__(self, minutes, wrapped):
    self.offset = minutes
    self.wrapped = wrapped

  def __repr__(self):
    return 'TimeOffset(%r, %r' % (self.offset, self.wrapped)

  def __call__(self, now=config.now(), previous=None):
    if isinstance(self.offset, numbers.Number):
      offset = self.offset
    else:
      offset = self.offset()
    delta = datetime.timedelta(minutes=offset)
    next = self.wrapped(now=now-delta, previous=previous)
    return next + delta


class Event(object):
  '''Event is an action that can be scheduled.'''
  
  def __init__(self, action_function, next_time_function):
    """next_time_function is called with two keyword arguments:
         now is the current time as a datetime,
         previous is ether None or the previous datetime this
             event was scheduled for.
       action_function is a function to be called (with no
         arguments) when it's time for the event to occur.
    """
    self.action_function = action_function
    self.next_time_function = next_time_function

  def schedule(self, previous=None):
    # It is expected that the next_time_function will not return a time
    # in the past.
    now_ = config.now()
    next = self.next_time_function(now=now_, previous=previous)
    if next:
      if next < now_:
        _log_scheduler_message(scheduler_operation='SCHEDULED_NEXT_BEFORE_NOW',
                               # action would be the same as sender in this case.
                               sender=self,
                               timestamp=now_,
	                       when=next)
      else:
        Scheduler().schedule(next, self)

  def __call__(self):
    self.doAction()

  def doAction(self):
    _log_scheduler_message(scheduler_operation='EVENT_ACTION',
                           sender=self,
                           timestamp=config.now())
    self.action_function()

  def __repr__(self):
    return('Event(%r, %r)' % (self.action_function, self.next_time_function))


SCHEDULE_OPERAATION_LOG_LEVEL = {
  'EVENT_ACTION': logging.INFO,
  'EVENT_SCHEDULED': logging.INFO,
  'SCHEDULED_ACTION_DONE': logging.INFO,
  'SCHEDULED_ACTION_FAILED': logging.ERROR,
  'SCHEDULED_NEXT_BEFORE_NOW': logging.WARNING
}

def _log_scheduler_message(**args):
  lvl = SCHEDULE_OPERAATION_LOG_LEVEL.get(args.get('scheduler_operation')) or logging.ERROR
  when = args.get('when')
  if when:
    when = when.strftime(config.TIME_FORMAT)
    d = {
      'scheduler_operation': args.get('scheduler_operation'),
      'action': args.get('action'),
      'scheduled_at': when
    }
  logging.getLogger(__name__).log(
    lvl,
    '%s: %r @ %s',
    d.get('scheduler_operation'),
    d.get('action'),
    d.get('scheduled_at'),
    extra=d)


class ScheduleLogFilter(logging.Filter):
  def __init__(self, log_level=logging.DEBUG, exclude_schedule_operations=[]):
    self.log_level = log_level
    self.exclude_schedule_operations = exclude_schedule_operations

  def filter(self, log_record):
    if log_record.module != __name__:
      return True
    if log_record.levelno < self.log_level:
      return False
    if log_record.__dict__.get('scheduler_operation') in self.exclude_schedule_operations:
      return False
    return True

