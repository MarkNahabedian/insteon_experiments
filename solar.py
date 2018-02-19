# This module provides approvimate times for sunrise and sunset.

# The formulas used here come from
# https://www.mathworks.com/examples/matlab/community/21093-estimating-sunrise-and-sunset

import datetime
import math
import schedule


def day_of_year(t):
  assert isinstance(t, datetime.datetime)
  return t.timetuple().tm_yday


def sin(x):
  return math.sin(math.radians(x))

def cos(x):
  return math.cos(math.radians(x))

def tan(x):
  return math.tan(math.radians(x))

def asin(x):
  return math.degrees(math.asin(x))

def acos(x):
  return math.degrees(math.acos(x))


class Solar(object):
  def __init__(self, latitude, longitude):
    self.latitude = latitude
    self.longitude = longitude

  def __repr__(self):
    return 'Solar(%r, %r)' % (self.latitude, self.longitude)

  def utc_offset(self, t):
    '''Returns offset from UTC in hours.'''
    assert isinstance(t, datetime.datetime)
    td = t.utcoffset()
    return (24 * 60 * 60 * td.days + td.seconds) / 60 / 60

  def longitudinal_correction(self, t):
    '''Returns the longitudinal correction in minutes for the given day.'''
    assert isinstance(t, datetime.datetime)
    return 4 * (self.longitude - 15 * self.utc_offset(t))

  def eot_correction(self, t):
    '''Returns the Equation of Time correction in minutes for the given day.'''
    assert isinstance(t, datetime.datetime)
    B = 360 * (day_of_year(t) - 81) / 365
    return 9.87 * sin(2*B)- 7.53 * cos(B) - 1.5 * sin(B)

  def solar_correction(self, t):
    '''Returns the solar correction in minutes for the given day.'''
    assert isinstance(t, datetime.datetime)
    return self.longitudinal_correction(t) + self.eot_correction(t)

  def declination(self, t):
    assert isinstance(t, datetime.datetime)
    return asin(sin(23.45) *
                sin(((day_of_year(t) - 81)
                     * 360/365)))

  def solar_noon_offset(self, t):
    '''The difference between solar noon and sunrise or sunset.'''
    assert isinstance(t, datetime.datetime)
    return datetime.timedelta(hours=acos(-tan(self.latitude) *
                                         tan(self.declination(t))) / 15)

  def noon(self, t):
    '''Returns local conventional noon for the given date.'''
    assert isinstance(t, datetime.datetime)
    return datetime.datetime(t.year, t.month, t.day, 12, 0, 0, 0, t.tzinfo)

  def solar_noon(self, t):
    '''Returns local solar noon for the given date.'''
    return self.noon(t) - datetime.timedelta(minutes=self.solar_correction(t))

  def sunrise(self, t):
    return self.solar_noon(t) - self.solar_noon_offset(t)

  def sunset(self, t):
    return self.solar_noon(t) + self.solar_noon_offset(t)


# Event next_time_function
class SolarEvent(object):
  '''SolarEvent allows Events to be scheduled for sunrise or sunset.'''
  def __init__(self, s, solar_event):
    assert isinstance(s, Solar)
    self.solar = s
    if solar_event == 'sunrise':
      self.calc = self.solar.sunrise
    elif solar_event == 'sunset':
      self.calc = self.solar.sunset
    else:
      raise Exception('Unsupported: %s' % (solar_event,))
    self.solar_event = solar_event

  def __repr__(self):
    return 'SolarEvent(%r, %r)' % (self.solar, self.solar_event)

  def __call__(self, now=schedule.now(), previous=None):
    '''Returns the next time that this should occur.'''
    at = self.calc(now)
    if at > now:
      return at
    return self.calc(now + datetime.timedelta(days=1))

