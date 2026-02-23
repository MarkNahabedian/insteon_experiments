#!python3

import logging
import actions
import config
import heartbeat
import modem
import mylogging
import pytz
import schedule
import solar
import plumbing
import webserver
import argparse
from pydispatch import dispatcher
from read_device_descriptions import read_device_descriptions
from schedule import DailyAt, TimeOffset, Event, Scheduler
from translator import *


logging.getLogger(schedule.__name__).addFilter(schedule.ScheduleLogFilter(
  exclude_schedule_operations=['EVENT_ACTION',
                               'SCHEDULED_ACTION_DONE',
                               'EVENT_SCHEDULED']))

# Command line arguments
parser = argparse.ArgumentParser(description='Run my home control system.')
parser.add_argument('--no-web', dest='no_web', default=False, action='store_true')
parsed = parser.parse_args()


# Initialize the packages that want to be initialized.
actions.run('onStartup')

# Connect to the modem.
im = modem.InsteonModem("/dev/ttyUSB0")    ### REPLACE WITH CORRECT PATH

sun = solar.Solar(42.37, -71.10)

# Read the link database and associated user curated data for the web service.
im.read_link_db()
read_device_descriptions('insteon.txt')

# Event(modem.InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))),
#       DailyAt(18, 29)).schedule()

# Probe current device status
# WE SHOULD DO THIS ONCE WE FIGURE OUT HOW.

# Schedule the lights

### Add Events here.


# Read the modem status and link database once a day
Event(modem.InsteonCommandAction(im, GetModemInfo()),
      DailyAt(12, 0)).schedule()
Event(im.read_link_db,
      DailyAt(12, 2),
      "Read link database").schedule()

def on():
  im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0)).encode()))

def off():
  im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(1), OffCmd(), Byte(0)).encode()))

with open("translators.txt", "w") as f:
  print("This file is written by the show_translators function.\n", file=f)
  show_translators(f)

if not parsed.no_web:
  webserver.run(8000, im)

# actions.run('onShutdown')

