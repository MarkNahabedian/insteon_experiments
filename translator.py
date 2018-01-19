

# encode:  sequence of objects to bytearray

# interpret:  pattern, bytearray to sequence of objects


# Each object might be a singleton instance representing a single
# bytecode and its meaning, or it might be something like a device
# address (three bytes).


# A Pattern has a sequence of types.  Pattern also implements
# encode and interpret.


import abc
from singleton import Singleton


class BitMask(object):
  def __init__(self, size, leftshift):
    self.size = size
    self.leftshift = leftshift
    self.mask = 0
    for i in range(self.size):
      self.mask = (self.mask << 1) | 1
    self.mask <<= self.leftshift

  def __repr__(self):
    return 'BitMask(%d, %d)' % (self.size, self.leftshift)

  def extract_from(self, bits):
    return (bits & (self.mask)) >> self.leftshift

  def align(self, value):
    return value << (self.leftshift) & self.mask


class NoMatch(Exception):
  '''NoMatch is raised when a Translator.interpret method fails to match
  the binary data.'''
  def __init__(self, trans, bytes, index):
    self.translator = trans
    self.bytearray = bytes
    self.start_index = index
  def __str__(self):
    return "%r, %r[%d]" % (self.translator, self.bytearray, self.start_index)


class Translator(object):
  __metaclass__ = abc.ABCMeta

  @classmethod
  def _showstr(cls):
    return _showstr_name(cls)

  # encode returns a sequence of bytes representing the interpretation.
  @abc.abstractmethod
  def encode(self):
    raise Exception("No encode method")

  # interpret extracts bytes from bytes starting at start_index and
  # returns an interpretation and the number of bytes consumed.
  # Raises NoMatch if the bytes could not be interpreted by this
  # Translator class.
  @classmethod
  @abc.abstractmethod
  def interpret(cls, bytes, start_index):
    raise Exception("No interpret method")
    pass


# See if the data can be interpreted as sone subclass of cls.
def _interpret_as_subclass(cls, bytes, start_index):
  for sc in cls.__subclasses__():
    try:
      return sc.interpret(bytes, start_index)
    except NoMatch as e:
      pass
  raise NoMatch(cls, bytes, start_index)


def show_translators():
  def walk(tc, level):
    print('%s%s' % ('  '*level, tc._showstr()))
    for sc in tc.__subclasses__():
      walk(sc, level + 1)
  walk(Translator, 0)

def _showstr_name(cls):
  if issubclass(cls, Singleton):
    return cls.__name__
  else:
    return '<%s>' % cls.__name__


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
  '''ByteCode is the superclass of all single byte codes that have a specific interpretation.'''
  @classmethod
  def _showstr(cls):
    bc = cls.__dict__.get('byte_code', None)
    if bc == None:
      return super(ByteCode, cls)._showstr()
    return '%s: \t 0x%02x' % (_showstr_name(cls), cls.byte_code)

  def encode(self):
    return (self.__class__.byte_code,)

  @classmethod
  def byte_code_match(cls, byte_code):
    ### Maybe this should use acceptable_bytes
    return byte_code == cls.byte_code

  @classmethod
  def interpret(cls, bytes, start_index):
    b = bytes[start_index]
    if not cls.byte_code_match(b):
      raise NoMatch(cls, bytes, start_index)
    return cls(), 1

  @classmethod
  def acceptable_bytes(cls):
    values = []
    def walk(cls):
      bc = cls.__dict__.get('byte_code', None)
      if bc != None:
        values.append(bc)
      for sc in cls.__subclasses__():
        walk(sc)
    walk(cls)
    return tuple(values)

  @classmethod
  def interpret(cls, bytes, start_index):
    if start_index >= len(bytes):
      raise NoMatch(cls, bytes, start_index)
    b = bytes[start_index]
    bc = cls.__dict__.get('byte_code', None)
    if bc == None:
      return _interpret_as_subclass(cls, bytes, start_index)
    elif b == bc: return cls(), 1
    else:
      raise NoMatch(cls, bytes, start_index)
    

  def __str__(self):
    return "%s-%02x" % (self.__class__.__name__, self.__class__.byte_code)

  def __repr__(self):
    return "%s()" % self.__class__.__name__


def bytecodes(family, **bytecodes):
  superclass = ByteCode
  # ***** Why are the classes defined with __module__ "abc" instead of here?
  if family:
    if globals().get(family):
      superclass = globals().get(family)
      assert issubclass(superclass, Translator)
    else:
      superclass = type(family, (superclass,), {})
      superclass.__metaclass__ = abc.ABCMeta
      globals()[family] = superclass
  for (name, bytecode) in bytecodes.items():
    c = type(name, (Singleton, superclass), {})
    globals()[name] = c
    c.byte_code = bytecode

bytecodes(None, StartByte=0x02)

bytecodes('AckNack',
          Ack=0x06,
          Nack=0x15)
  
# Ack.interpret(bytearray(b'\x06'), 0)   -> (Ack(), 1)

bytecodes('MessageOrigin',
          OriginModem=0x50,
          OriginHost=0x60)

bytecodes('CommandCode',
          # get information about the Insteon modem itself.
          GetModemInfoCmd=0x60,
          AllLinkCmd=0x61,
          SendMessageCmd=0x62
)

class GetLinkCmd(CommandCode):
  __metaclass__ = abc.ABCMeta

bytecodes('GetLinkCmd',
          Get1stLinkCmd=0x69,
          GetNextLinkCmd=0x6A)

          
bytecodes('ResponseCode',
          LinkingCompletedRsp=0x53,
          LinkDbRecordRsp=0x57,
          ButtonEvent=0x54)

class InsteonMessage(Translator):
  __metaclass__ = abc.ABCMeta

class InsteonStandardMessage(InsteonMessage):
  __metaclass__ = abc.ABCMeta

class InsteonExtendedMessage(InsteonMessage):
  __metaclass__ = abc.ABCMeta


bytecodes('StandardDirectCommand',
          AssignToGroupCmd=0x01,
          PingCmd=0x0F,
          BeepCmd=0x30,
          OnCmd=0x11,
          OffCmd=0x13,
          IdRequestCmd=0x10,
          StatusRequestCmd=0x19
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
      raise NoMatch(cls, bytes, start_index)
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
    if start_index + 3 >= len(bytes):
      raise NoMatch(cls, bytes, start_index)
    return InsteonAddress(bytes[start_index],
                          bytes[start_index + 1],
                          bytes[start_index + 2]), 3

  def __eq__(self, other):
    return (isinstance(other, InsteonAddress) and
            self.address1 == other.address1 and
            self.address2 == other.address2 and
            self.address3 == other.address3)

  def __ne__(self, other):
    return not (self == other)

  def __hash__(self):
    return (((self.address1<<8) | self.address2)<<8) | self.address3


class Pattern(Translator):
  __metaclass__ = abc.ABCMeta

  @classmethod
  def _showstr(cls):
    pat = cls.__dict__.get('pattern', None)
    if pat == None:
      return super(Pattern, cls)._showstr()
    return '%s: \t %s' % (_showstr_name(cls), ', '.join(
      [_showstr_name(p) for p in pat]))

  def __init__(self, *tokens):
    for i in range(len(self.__class__.pattern)):
      tt = self.__class__.pattern[i]
      if i > len(tokens) and issubclass(tt, Singleton):
        v = tt()
      else:
        v = tokens[i]
      assert isinstance(v, tt)
      if not issubclass(tt, Singleton):
        self.__dict__[tt.__name__] = a
    self.values = tokens
  
  def __str__(self):
    return "%s-()%s" % (self.__class__.__name__,
                        ",".join([ str(v) for v in self.values ]))

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__,
                     ', '.join([repr(v)
                                for v in self.values
                                # if len([pt
                                #         for pt in self.__class__.parameter_types
                                # if isinstance(v, pt)]) > 0
                                ]))

  def encode(self):
    msg = []
    for tt in self.values:
      msg.extend(tt.encode())
    return msg

  @classmethod
  def interpret(cls, bytes, start_index):
    # print('%s.interpret(%r, %d)' % (cls.__name__, bytes, start_index))
    index = start_index
    values = []
    pattern = cls.__dict__.get('pattern', None)
    if pattern == None:
      return _interpret_as_subclass(cls, bytes, start_index)
    for tt in pattern:
      v, advance = tt.interpret(bytes, index)
      values.append(v)
      index += advance
    return cls(*values), index - start_index


def pattern(name, superclasses, token_types):
  if len(superclasses) == 0:
    superclasses = (Pattern,)
  nonconstant_token_types = []
  # super_args = []
  for tt in token_types:
    assert issubclass(tt, Translator)
    if not issubclass(tt, Singleton):
      nonconstant_token_types.append(tt)
  # We can fully initialize a Pattern given only tokens from
  # nonconstant_token_types, but there are cases where we have a full
  # list of tokens that we want to initialize from without having to
  # filter out the constant ones, so our __init__ method should cope
  # witheither set of initargs.
  if not nonconstant_token_types:
    superclasses = (Singleton,) + superclasses
  pat = type(name, superclasses, {})
  pat.pattern = token_types
  pat.nonconstant_token_types = nonconstant_token_types
  def _init(self, *args):
    if len(args) == len(pat.pattern):
      self.values = args
    elif len(args) == len(pat.nonconstant_token_types):
      self.values = []
      argindex = 0
      for tt in self.pattern:
        if argindex < len(args) and isinstance(args[argindex], tt):
          v = args[argindex]
          argindex += 1
        else:
          assert issubclass(tt, Singleton), '%r is not a subclass of Singleton' % tt
          v = tt()
        self.values.append(v)
    else:
      raise Exception("Wrong number of arguments to __init__.  Expected %d or %d" % (
        len(pat.nonconstant_token_types), len(pat.pattern)))
    for i in range(len(self.pattern)):
      tt = self.pattern[i]
      v = self.values[i]
      if not issubclass(tt, Singleton):
        self.__dict__[tt.__name__] = v
  pat.__init__ = _init
  globals()[name] = pat


class Category(Byte): pass
class Subcategory(Byte): pass
class FirmwareVersion(Byte): pass

pattern('GetModemInfo', (), (StartByte, GetModemInfoCmd))
pattern('ModemInfoResponse', (), (
  GetModemInfo, # echoed command
  InsteonAddress,
  Category,
  Subcategory,
  FirmwareVersion,
  Ack))


class Flags (Translator):
  def __init__(self, **args):
    self.flags = 0
    for key, val in args.items():
      if key in self.__class__.FlagBits:
        bitmask = self.__class__.FlagBits[key]
        if bitmask.size == 1:
          if val == 1 or val == True:
            self.flags |= bitmask.mask
          else:
            self.flags &= ~bitmask.mask
        else:
          self.flags &= ~bitmask.mask
          self.flags |= bitmask.align(val)
      else:
        raise Exception(">Unsupported flag property: %s" % key)

  def __repr__(self):
    args = []
    for key, bitmask in self.__class__.FlagBits.items():
      val = bitmask.extract_from(self.flags)
      if bitmask.size == 1:
        val = val == 1
      args.append("%s=%r" % (key, val))
    return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

  def encode(self):
    return (self.flags,)

  @classmethod
  def interpret(cls, bytes, start_index):
    i = cls()
    i.flags = bytes[start_index]
    return i, 1

  
class LinkGroup(Byte): pass
class LinkData1 (Byte): pass
class LinkData2 (Byte): pass
class LinkData3 (Byte): pass

class LinkDBRecordFlags(Byte): pass

pattern('LinkDBRecord', (), (
  StartByte,
  LinkDbRecordRsp,
  LinkDBRecordFlags,
  LinkGroup,
  InsteonAddress,
  LinkData1, LinkData2, LinkData3
  ))

class ReadLinkDBCommand(Pattern):
  __metaclass__ = abc.ABCMeta

pattern('Get1stLinkCommand', (ReadLinkDBCommand,),
        (StartByte, Get1stLinkCmd))
pattern('GetNextLinkCommand', (ReadLinkDBCommand,),
        (StartByte, GetNextLinkCmd))
pattern('GetLinkResponse', (),
        (ReadLinkDBCommand, AckNack))


# rec = LinkDBRecord.interpret(bytearray(b'\x02\x6a\x06\x02\x57\xe2\x01\x0f\x82\x9e\x02\x09\x32'), 3)
# LinkDBRecord.encode(rec[0])

# bytecodes(OpenClosed, Closed=0x00, Open=0xff)

# pattern('SendAllLinkCommand', (
#   StartByte,
#   AllLinkCmd,
#   LinkGroup,
#   Command1,
#   Command2,
#   Byte ### what is this?
#   ))

class MessageFlags(Flags):
  FlagBits = {
    'max_hops':       BitMask(2, 0),
    'hops_remaining': BitMask(2, 2),
    'extended':       BitMask(1, 4),   # 1 -> extended command
    'acknowledge':    BitMask(1, 5),
    'group':          BitMask(1, 6),
    'broadcast_NACK': BitMask(1, 7)
    }


class Command2(Byte): pass

pattern('SendMessageCommand', (), (
  StartByte, SendMessageCmd, InsteonAddress,
  MessageFlags, StandardDirectCommand, Command2))

class FromAddress(InsteonAddress): pass
class ToAddress(InsteonAddress): pass

pattern('StandardMessageReceived', (), (
  StartByte, OriginModem, FromAddress, ToAddress,
  MessageFlags, StandardDirectCommand, Command2))
