

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
    ...

  # interpret extracts bytes from bytes starting at start_index and
  # returns an interpretation and the number of bytes consubed.
  @classmethod
  @abc.abstractmethod
  def interpret(cls, bytes, start_iindex):
    ...


class ByteCode(Translator):
  def encode(self):
    return self.__class__.byte_code

  @classmethod
  def interpret(cls, bytes, start_iindex):
    return cls(), 1


class StartByte(Singleton, ByteCode):
  # singleton
  byte_code = 0x02


claSS AckNack(ByteCode):
  @abc.abstractmethod


class Ack(Singleton, AckNack):
  byte_code = 0x06


class Nack(Singleton, AckNack):
  byte_code = 0x15


class Command(ByteCode):
  @abc.abstractmethod


class PingCmd(Singleton, Command):
  byte_code = 0x0F


class InsteonAddress(Translator):
  def __init__(self, address1, address2, address3):
    self.address1 = address1
    self.address2 = address2
    self.address3 = address3

  def encode(self):
    return (self.address1, self.address2, self.address3)

  @classmethod
  def interpret(cls, bytes, start_index):
    return InsteonAddress(bytes[start_index],
                          bytes[start_index + 1],
                          bytes[start_index + 2]), 3

  def __str__(self):
    return "%s-%02x.%02x.%02x" % (
        self.__class__.__name__,
        self.address1, self.address2, self.address3)


# class Pattern(Translator):
#   patterns = {}

#   @classmethod
#   def lookup(cls, name):
#     return cls.patterns.get(name, None)

#   def __init__(self, name, token_types):
#     assert isinstance(name, str)
#     for tt in token_types:
#       assert issubclass(tt, Translator)
#     self.name = name
#     patterns[self.name] = self


