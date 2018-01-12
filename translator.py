

# encode:  sequence of objects to bytearray

# interpret:  pattern, bytearray to sequence of objects


# Each object might be a singleton instance representing a single
# bytecode and its meaning, or it might be something like a device
# address (three bytes).


# A Pattern has a sequence of types.  Pattern also implements
# encode and interpret.


import abc
from singleton import Singleton


class Translator(object):
  __metaclass__ = abc.ABCMeta

  # encode returns a sequence of bytes representing the interpretation.
  @abc.abstractmethod
  def encode(self):
    pass

  # interpret extracts bytes from bytes starting at start_index and
  # returns an interpretation and the number of bytes consubed.
  @classmethod
  @abc.abstractmethod
  def interpret(cls, bytes, start_index):
    pass


class Byte(Translator):
  '''Byte represents a single byte of any value.'''
  def __init__(self, value):
    self.byte = value

  def __str__(self):
    return "Byte-%02x" % self.byte

  def __repr__(self):
    return "%s(0x%02x)" % (self.__class__.__name__, self.byte)

  def encode(self):
    return (self.byte,)

  @classmethod
  def interpret(cls, bytes, start_index):
    return cls(bytes[start_index]), 1


class ByteCode(Translator):
  def encode(self):
    return (self.__class__.byte_code,)

  @classmethod
  def byte_code_match(cls, byte_code):
    return byte_code == cls.byte_code

  @classmethod
  def interpret(cls, bytes, start_index):
    b = bytes[start_index]
    if not cls.byte_code_match(b):
      return None, 0
    return cls(), 1

  def __str__(self):
    return "%s-%02x" % (self.__class__.__name__, self.__class__.byte_code)

  def __repr__(self):
    return "%s()" % self.__class__.__name__


def _find_byte_code_in_family(cls, byte_code):
  # Depth first search.
  for sc in cls.__subclasses__():
    if cls.byte_code_match(byte_code):
      return sc
    found = _find_byte_code_in_family(sc, byte_code)
    if found:
      return found
  return None


def bytecodes(family, **bytecodes):
  superclass = ByteCode
  # ***** Why are the classes defined with __module__ "abc" instead of here?
  if family:
    if not globals().get(family):
      superclass = type(family, (superclass,), {})
      superclass.__metaclass__ = abc.ABCMeta
      globals()[family] = superclass
      ### We would like for interpret() on a byte code family to look
      ### through all of the subclasses of the family for a match.
      def _interpret(cls, bytes, start_index):
        f = _find_byte_code_in_family(cls, bytes[start_index])
        if f: return f(), 1
        return None, 0
      superclass.interpret = _interpret
  for (name, bytecode) in bytecodes.items():
    c = type(name, (Singleton, superclass), {})
    globals()[name] = c
    c.byte_code = bytecode

bytecodes(None, StartByte=0x02)

bytecodes('AckNack',
          Ack=0x06,
          Nack=0x15)
  
bytecodes('MessageOrigin',
          OriginModem=0x50,
          OriginHost=0x60)

bytecodes('CommandCode',
          PingCmd=0x0F,
          BeepCmd=0x30,
          OnCmd=0x11,
          OffCmd=0x13,
          IdRequestCmd=0x10,
          StatusRequestCmd=0x19,
          # get information about the Insteon modem itself.
          GetModemInfoCmd=0x60,
          # initiate reading the modem's link database
          Get1stLinkCmd=0x69,
          GetNextLinkCmd=0x6A,
)

bytecodes('ResponseCode',
          LinkingCompletedRsp=0x53,
          LinkDbRecordRsp=0x57,
          ButtonEvent=0x54
)


bytecodes('ButtonAction',
          ButtonTapped=0x02,
          ButtonPressAndHold=0x03,
          ButtonReleased=0x04)

class ButtonEvent(Translator):
  button_numbers = (1, 2, 3)

  def __init__(self, button_number, button_action):
    assert button_number in self.__class__.button_numbers
    assert isinstance(button_action, ButtonAction)
    self.button_number = button_number
    self.button_action = button_action

  def __str__(self):
    return "%s-button%d-%s" % (
      self.__class__.__name__,
      self.button_number,
      self.button_action.__class__.__name__)

  def encode(self):
    return ((self.button_bumber << 4) | (self.button_action.byte_code),)

  @classmethod
  def interpret(cls, bytes, start_index):
    b = bytes[start_index]
    bn = b >> 4
    act = b and 0x0F
    if bn in self.__class__.button_numbers:
      return None, 0
    # TODO: serify that act is a valid ButtonAction
    return ButtonEvent(bn, act), 1


class InsteonAddress(Translator):
  def __init__(self, address1, address2, address3):
    self.address1 = address1
    self.address2 = address2
    self.address3 = address3

  def __str__(self):
    return "%s-%02x.%02x.%02x" % (
        self.__class__.__name__,
        self.address1, self.address2, self.address3)

  def __repr__(self):
    return "%s(0x%02x, 0x%02x, 0x%02x)" % (
        self.__class__.__name__,
        self.address1, self.address2, self.address3)

  def encode(self):
    return (self.address1, self.address2, self.address3)

  @classmethod
  def interpret(cls, bytes, start_index):
    return InsteonAddress(bytes[start_index],
                          bytes[start_index + 1],
                          bytes[start_index + 2]), 3


class Pattern(Translator):
  __metaclass__ = abc.ABCMeta

  def __init__(self, *tokens):
    for i in range(len(self.__class__.pattern)):
      tt = self.__class__.pattern[i]
      v = tokens[i]
      assert isinstance(v, tt)
    self.values = tokens
  
  def __str__(self):
    return "%s-()%s" % (self.__class__.__name__,
                        ",".join([ str(v) for v in self.values ]))

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__,
                     ', '.join([repr(v) for v in self.values]))

  def encode(self):
    msg = []
    for tt in self.values:
      msg.extend(tt.encode())
    return msg

  @classmethod
  def interpret(cls, bytes, start_index):
    index = start_index
    values = []
    for tt in cls.pattern:
      v, advance = tt.interpret(bytes, index)
      if v == None:
        return None, 0
      values.append(v)
      index += advance
    return cls(*values), index - start_index


def pattern(name, token_types):
  for tt in token_types:
    assert issubclass(tt, Translator)
  pat = type(name, (Singleton, Pattern), {})
  pat.pattern = token_types
  globals()[name] = pat

pattern('LinkDBRecord', (
  StartByte,
  Byte, # flags
  Byte, # link group
  InsteonAddress,
  Byte, Byte, Byte # data
  ))


# rec = LinkDBRecord.interpret(bytearray(b'\x02\x6a\x06\x02\x57\xe2\x01\x0f\x82\x9e\x02\x09\x32'), 3)
# LinkDBRecord.encode(rec)

