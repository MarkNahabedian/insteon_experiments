# Scheduling events for home automation.

import datetime
import modem
import threading
import translator
import insteon_logging
from pydispatch import dispatcher
from singleton import Singleton
from Queue import PriorityQueue, Empty
from tzlocal import get_localzone


def now():
  '''Returns the current time as a datetime.datetime, with local timezone.'''
  return datetime.datetime.now(get_localzone())


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
    self.schedule_queue.put((when, action))
    dispatcher.send(signal='EVENT_SCHEDULED',
                    sender=self,
                    timestamp=now(),
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
        e = self.schedule_queue.get_nowait()
      except Empty:
        self.event.wait(timedelta_to_seconds(self.__class__.empty_queue_wait_time))
        continue
      if e[0] <= now():
        success = False
        now_ = now()
        try:
          e[1]()
          success = True
        except e:
          dispatcher.send(signal='SCHEDULED_ACTION_FAILED',
                          sender=self,
                          timestamp=now_,
  	                    when=e[0],
                          action=e[1])
        if success:
          dispatcher.send(signal='SCHEDULED_ACTION_DONE',
                          sender=self,
                          timestamp=now_,
  	                  when=e[0],
                          action=e[1])
        self.schedule_queue.task_done()
      else:
        # Not ripe yet, put it back.
        self.schedule_queue.put(e)
        self.event.wait(timedelta_to_seconds(e[0] - now()))
        

class DailyAt(object):
  '''DailyAt is a function that returns the next datetime (after now)
     having the specified hour anmd minute.'''
  delta = datetime.timedelta(days=1)

  def __init__(self, hour, minute):
    self.hour = hour
    self.minute = minute

  def __repr__(self):
    return 'DailyAt(%r, %r)' % (self.hour, self.minute)

  def __call__(self):
    '''Returns the next time that this should occur.'''
    now_ = now()
    at = datetime.datetime(now_.year, now_.month, now_.day,
                           self.hour, self.minute,
                           now_.second, 0, now_.tzinfo)
    if at > now_:
      return at
    return at + self.__class__.delta


class InsteonCommandAction(object):
  '''InsteonCommandAction is a callable, which, when called, sends the
     specified command to the specified InsteonModem.  It can be used
     as the action_function of an Event.'''
  def __init__(self, modem_, command):
    assert isinstance(modem_, modem.InsteonModem)
    assert isinstance(command, translator.Command), repr(command)
    self.modem = modem_
    self.command = command

  def __call__(self):
    self.modem.sendCommand(bytearray(self.command.encode()))
    self.modem.readResponse()

  def __repr__(self):
    return 'InsteonCommandAction(%r, %r)' % (self.modem, self.command)


class Event(object):
  '''Event is an action that can be scheduled.'''
  
  def __init__(self, action_function, next_time_function):
    self.action_function = action_function
    self.next_time_function = next_time_function

  def schedule(self):
    next = self.next_time_function()
    if next:
      Scheduler().schedule(next, self)

  def __call__(self):
    self.doAction()

  def doAction(self):
    dispatcher.send(signal='EVENT_ACTION',
                    sender=self,
                    timestamp=now())
    self.action_function()
    self.schedule()

  def __repr__(self):
    return('Event(%r, %r)' % (self.action_function, self.next_time_function))


def _format_scheduler_message(signal, sender, timestamp, when, action):
  return '%s: %s: %r @ %s' % (
    timestamp.strftime(insteon_logging._time_format),
    signal, action,
    when.strftime(insteon_logging._time_format))


def _log_scheduler_message(**args):
  insteon_logging._logger.info(_format_scheduler_message(**args))


def _log_scheduler_error(**args):
  insteon_logging._logger.info(_format_scheduler_message(**args))

                               
def _do_onStartup_DispatchRegistration():
  dispatcher.connect(_log_scheduler_message, signal='EVENT_SCHEDULED')
  dispatcher.connect(_log_scheduler_message, signal='SCHEDULED_ACTION_DONE')
  dispatcher.connect(_log_scheduler_error, signal='SCHEDULED_ACTION_FAILED')

