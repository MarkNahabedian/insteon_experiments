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

  @staticmethod
  def deviceID(byte1, byte2, byte3):
    return "%02x.%02x.%02x" % (byte1, byte2, byte3)

  @classmethod
  def lookup(cls, *args):
    if len(args) == 1 and isinstance(args[0], str):
      id = args[0]
    elif len(args) == 3:
      id = cls.deviceID(args[0], args[1], args[2])
    else:
      raise Exception("Bad parameters %s" % repr(args))
    if id in cls.devices:
      return cls.devices[id]
    return None

  @classmethod
  def list_devices(cls):
    for d in cls.devices.values():
      print(str(d))

  def __init__(self, address_byte1, address_byte2, address_byte3):
    super(InsteonDevice, self).__init__()
    id = self.deviceID(address_byte1, address_byte2, address_byte3)
    if self.__class__.lookup(id):
      raise DeviceExists(id)
    self.address_byte1 = address_byte1
    self.address_byte2 = address_byte2
    self.address_byte3 = address_byte3
    self.category = None
    self.subcategory = None
    self.firmware_version = None
    self.__class__.devices[id] = self

  def __str__(self):
    return "<insteon device %s %r/%r %r>" % (
      self.__class__.deviceID(self.address_byte1,
                              self.address_byte2,
                              self.address_byte3),
      self.category, self.subcategory, self.firmware_version)

  # def ping(self, modem):
  #   assert isinstance(modem, InsteonModem)
  #   command = modem.command(modem.CMD_PING)
  #   modem.sendCommand(command)
  #   response = modem.readResponse()
  #   im.check_echo(command, response)
  #   return response[2] == im.ACK

  # def id_request(self, modem):
  #   assert isinstance(modem, InsteonModem)
  #   command = modem.command(modem.CMD_ID_REQUEST)
  #   modem.sendCommand(command)
  #   response = modem.readResponse()
  #   im.check_echo(command, response)

  # def on(self, modem):
  #   assert isinstance(modem, InsteonModem)
  #   pass

  # def off(self, modem):
  #   assert isinstance(modem, InsteonModem)
  #   im.command(
      
  #     im.CMD_OFF)

pass


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

  ### Do we still need this?
  # def command(self, *cmdbytes):
  #   msg = bytearray()
  #   if cmdbytes[0] != self.CMD_1STBYTE:
  #     msg.append(self.CMD_1STBYTE)
  #   for b in cmdbytes:
  #     msg.append(b)
  #   return msg

  # def standardCommand(self):
  #   pass

  def sendCommand(self, command):
    isinstance(command, bytearray)
    if debug: print("sending command %s" % hexdump(command))
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

    # if response[0] != self.CMD_1STBYTE: return response
    # if response[1] != 0x60: return response
    # addr1 = response[2]
    # addr2 = response[3]
    # addr3 = response[4]
    # category = response[5]
    # subcategory = response[6]
    # firmware = response[7]
    # if response[8] != self.ACK: return response
    id = InsteonDevice.deviceID(addr1, addr2, addr3)
    device = InsteonDevice.lookup(id)
    if not device:
      device = InsteonDevice(addr1, addr2, addr3)
      device.category = category
      device.subcategory = subcategory
      device.firmware_version = firmware
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
    command = self.command(self.CMD_GET_1ST_LINK)
    self.sendCommand(command)
    while True:
      response = self.readResponse()
      self.check_echo(command, response)
      if response[2] != self.ACK:
        break
      response = response[4:]
      self.check_echo(self.command(self.ANS_LINK_DB_RECORD_RESPONSE)[1:],
                      response)
      flags = response[1]
      group = response[2]
      addr1 = response[3]
      addr2 = response[4]
      addr3 = response[5]
      data = response[6:9]
      if debug:
        print("%02x %d %s %s" % (
          flags, group,
          InsteonDevice.deviceID(addr1, addr2, addr3),
          hexdump(data)))
      id = InsteonDevice.deviceID(addr1, addr2, addr3)
      device = InsteonDevice.lookup(id)
      if not device:
        InsteonDevice(addr1, addr2, addr3)
      command = self.command(self.CMD_GET_NEXT_LINK)
      self.sendCommand(command)

  def load_devices(self):
    self.modeminfo()
    self.read_link_db()

  pass


try:
  im = InsteonModem("/dev/ttyUSB0")
  im.load_devices()
  InsteonDevice.list_devices()
finally:
  debug = True

InsteonDevice.lookup("49.93.bf").ping(im)  # modem
InsteonDevice.lookup("0f.82.9e").ping(im)
InsteonDevice.lookup("0f.83.8f").ping(im)
