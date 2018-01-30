# Simple testing of the insteon modem.

# This module sends pydispatch signals with the following names:
#
#   'MODEM_COMMAND'     for receivers that care about what messages
#                       are sent to the Insteon mode
#   'MODEM_RESPONSE'    for messages that are received back from
#                       the Insteon modem.


import actions
from pydispatch import dispatcher
import datetime
import serial
import time
from translator import *
import insteon_logging

debug = False

def hexdump(msg):
  s = ""
  for b in msg:
    if len(s) > 0: s += " "
    s += "%02x" % b
  return s


class DeviceExists(Exception):
  def __init__(self, id):
    self.id = id
  def __str__(self):
    return "%device %s already exists" % self.id


class UnexpectedResponse(Exception):
  def __init__(self, command, response):
    self.command = command
    self.response = response
  def __str__(self):
    return "Unexpected response: %s for command %s" % (
      hexdump(self.response),
      hexdump(self.command))


class Device(object):
  def __init__(self):
    self.name = ""
  pass


class InsteonDevice(Device):
  devices = {}

  @classmethod
  def lookup(cls, *args):
    if len(args) == 1 and isinstance(args[0], InsteonAddress):
      addr = args[0]
    elif len(args) == 3:
      addr = InsteonAddress(*args)
    else:
      raise Exception("Bad parameters %s" % repr(args))
    if addr in cls.devices:
      return cls.devices[addr]
    return None

  @classmethod
  def list_devices(cls):
    for d in cls.devices.values():
      print(str(d))

  def __init__(self, insteonAddress):
    assert isinstance(insteonAddress, InsteonAddress)
    super(InsteonDevice, self).__init__()
    if self.__class__.lookup(insteonAddress):
      raise DeviceExists(id)
    self.address = insteonAddress
    self.category = None
    self.subcategory = None
    self.firmware_version = None
    self.__class__.devices[self.address] = self

  def __repr__(self):
    return '%s(%r)' % (self.__class__.__name__, self.address)

  def _simple_command(self, modem, cmd):
    response_index = 0
    assert isinstance(modem, InsteonModem)
    assert isinstance(cmd, StandardDirectCommand)
    command = SendMessageCommand(self.address, MessageFlags(extended=False), IdRequestCmd(), Command2(0x01))
    modem.sendCommand(bytearray(command.encode()))
    response = modem.readResponse()
    echoed, length = ReadFromModem.interpret(response, response_index)
    response_index += length
     ### Should check echo.
    return echoed.AckNack is Ack(), response, response_index

  def ping(self, modem):
    return self._simple_command(modem, PingCmd())

  def id_request(self, modem):
    return self._simple_command(modem, IdRequestCmd())

  def status(self, modem):
    acked, response, response_index = self._simple_command(modem, StatusRequestCmd())

  def on(self, modem):
    return self._simple_command(modem, OnCmd())

  def off(self, modem):
    return self._simple_command(modem, OffCmd())


class InsteonModem (object):
  '''
  InsteonModem mediates communication with an Insteon serial modem.
  '''
  
  def __init__(self, port_path):
    self.port_path = port_path
    self.serial = serial.Serial(port_path)
    self.serial.bytesize = serial.EIGHTBITS
    self.serial.baudrate = 19200
    self.serial.timeout = 1
    self.devices = {}
    pass

  def __repr__(self):
    return 'InsteonModem(%r)' % (self.port_path,)

  def sendCommand(self, command):
    assert isinstance(command, bytearray)
    # dispatch results are ignored.
    dispatcher.send(signal='MODEM_COMMAND',
                    sender=self,
                    timestamp=datetime.datetime.now(),
                    bytes=command)
    if debug: print("sending command    %s" % hexdump(command))
    self.serial.write(command)

  def readResponse(self):
    msg = bytearray()
    while True:
      b = self.serial.read(1)
      if not b:
        break
      msg.append(b)
      if b in AckNack.acceptable_bytes():
        break
    if debug: print("receiving response %s" % hexdump(msg))
    if len(msg) > 0:
      # dispatch results are ignored.
      dispatcher.send(signal='MODEM_RESPONSE',
                      sender=self,
                      timestamp=datetime.datetime.now(),
                      bytes=msg)
    return msg

  def modeminfo(self):
    self.sendCommand(bytearray(GetModemInfo().encode()))
    response = self.readResponse()
    i, length = ModemInfoResponse.interpret(response, 0)
    device = InsteonDevice.lookup(i.InsteonAddress)
    if not device:
      device = InsteonDevice(i.InsteonAddress)
      device.category = i.Category
      device.subcategory = i.Subcategory
      device.firmware_version = i.FirmwareVersion
    return device

  def listen(self):
    global debug
    old_debug = debug
    debug = False
    try:
      while True:
        msg = self.readResponse()
        if len(msg) == 0:
          time.sleep(1)
          continue
        print(hexdump(msg))
    finally:
      debug = old_debug

  # Verify that the response echos the command
  def check_echo(self, command, response):
    for i in range(len(command)):
      if command[i] != response[i]:
        raise UnexpectedResponse(command, response)

  def read_link_db(self):
    links = []
    self.sendCommand(bytearray(Get1stLinkCommand().encode()))

    while True:
      response = self.readResponse()
      i, length = ReadFromModem.interpret(response, 0)
      if debug: print("interpreted response: %r" % i)
      if not isinstance(i.AckNack, Ack):
        break
      interpreted, length = AllLinkRecordResponse.interpret(response, length)
      if debug: print(repr(interpreted))
      record = interpreted.LinkDBRecord
      flags = record.LinkDBRecordFlags
      group = record.LinkGroup
      address = record.InsteonAddress
      device = InsteonDevice.lookup(address)
      if not device:
        device = InsteonDevice(address)
      if debug: print(repr(device))
      self.sendCommand(bytearray(GetNextLinkCommand().encode()))

  def load_devices(self):
    self.modeminfo()
    self.read_link_db()

  def groupOn(self, group_number):
    command = SendAllLinkCommand(LinkGroup(group_number), OnCmd(), Byte(0))
    im.sendCommand(bytearray(command.encode()))
    response = self.readResponse()

  def groupOff(self, group_number):
    command = SendAllLinkCommand(LinkGroup(group_number), OffCmd(), Byte(0))
    im.sendCommand(bytearray(command.encode()))
    response = self.readResponse()


