# Simple testing of the insteon modem.

import abc
import serial
import time
from translator import *

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
    echoed, length = SendMessageCommand.interpret(response, response_index)
    response_index += length
     ### Should check echo.
    ack, length = AckNack.interpret(response, response_index)
    response_index += length
    return ack is Ack()

  def ping(self, modem):
    return self._simple_command(modem, PingCmd())

  def id_request(self, modem):
    return self._simple_command(modem, IdRequestCmd())

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

  def sendCommand(self, command):
    assert isinstance(command, bytearray)
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
      i, length = GetLinkResponse.interpret(response, 0)
      if debug: print("interpreted response: %r" % i)
      if not isinstance(i.AckNack, Ack):
        break
      record, length = LinkDBRecord.interpret(response, length)
      if debug: print(repr(record))
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

  pass


try:
  debug = False
  im = InsteonModem("/dev/ttyUSB0")
  im.load_devices()
  InsteonDevice.list_devices()
finally:
  debug = True

InsteonDevice.lookup(InsteonAddress(0x49, 0x93, 0xbf)).ping(im)  # modem
InsteonDevice.lookup(InsteonAddress(0x0f, 0x83, 0x8f)).ping(im)
InsteonDevice.lookup(InsteonAddress(0x0f, 0x82, 0x9e)).ping(im)

