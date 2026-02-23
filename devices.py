class Device(object):
  def __init__(self):
    self.name = ""
  pass


class InsteonDevice(Device):
  devices = {}

  @classmethod
  def lookup(cls, *args):
    addr = InsteonAddress(*args)
    if addr in cls.devices:
      return cls.devices[addr]
    return None

  @classmethod
  def list_devices(cls):
    for d in cls:
      print(str(d))

  @staticmethod
  # If this method is called explicitly one can use the resulting
  # iterator.  For some reason, the iter built-in function raises a
  # TypeError rather than calling this method.
  def __iter__():
    return iter(InsteonDevice.devices.values())

  def __init__(self, insteonAddress):
    assert isinstance(insteonAddress, InsteonAddress)
    super(InsteonDevice, self).__init__()
    if self.__class__.lookup(insteonAddress):
      raise DeviceExists(id)
    self.address = insteonAddress
    self.location = ''
    self.category = None
    self.subcategory = None
    self.firmware_version = None
    # Most recently received responses from this device
    self.cmd1 = None
    self.cmd2 = None
    self.received_timestamp = None
    self.__class__.devices[self.address] = self

  def __repr__(self):
    return '%s(%r)' % (self.__class__.__name__, self.address)

  def process_message_from_me(self, msg):
    assert isinstance(msg, Translator)
    pattern1 = StandardMessageReceived(
      StartByte(), StandardMessageReceivedCode(),
      FromAddress(self.address), MatchVariable("to_address"),
      MatchVariable("message_flags"),
      MatchVariable("cmd1"), MatchVariable("cmd2"))
    m = match(msg, pattern1)
    if m == False:
      return
    self.received_timestamp = config.now()
    self.cmd1 = m["cmd1"]
    self.cmd2 = m["cmd2"]

  def _simple_command(self, modem, cmd, cmd2):
    response_index = 0
    assert isinstance(modem, InsteonModem)
    assert isinstance(cmd, StandardDirectCommand)
    command = SendMessageCommand(self.address,
                                 MessageFlags(extended=False,
                                              max_hops=3,
                                              hops_remaining=3),
                                 cmd, cmd2)
    modem.sendCommand(bytearray(command.encode()))
    response = modem.readResponse()
    echoed, length = ReadFromModem.interpret(response, response_index)
    response_index += length
     ### Should check echo.
    return echoed.AckNack is Ack(), response, response_index

  def ping(self, modem):
    return self._simple_command(modem, PingCmd(), Command2(0x01))

  def id_request(self, modem):
    return self._simple_command(modem, IdRequestCmd(), Command2(0x01))

  def status(self, modem):
    acked, response, _ = self._simple_command(modem, StatusRequestCmd(), Command2(0x00))
    if not acked:
      return
    rfm, length1 = ReadFromModem.interpret(response, 0)
    smr, length2 = StandardMessageReceived.interpret(response, length1)
    assert len(response) == length1 + length2
    return smr.Byte.byte

  def on(self, modem):
    return self._simple_command(modem, OnCmd(), Command2(0x01))

  def off(self, modem):
    return self._simple_command(modem, OffCmd(), Command2(0))

