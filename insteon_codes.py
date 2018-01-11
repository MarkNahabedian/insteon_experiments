# This file provides a way of encoding and decoding insteon commands.

import abc


class Code(object):
  # Code is an abstract base class for going back and forth between
  # byte codes and their interpretations or meanings in the Insteon
  # world.
  __metaclass__ = abc.ABCMeta

  # encode returns a seq1uence of bytes representing the interpretation.
  @abc.abstractmethod
  def encode(self):
    ...

  # interpret extracts bytes from bytes starting at start_index and
  # returns an interpretation and the number of bytes consubed.
  @classmethod
  @abc.abstractmethod
  def interpret(cls, bytes, start_iindex):
    ...


class ByteCode(Code):
  def __init__(self, code, context, interpretation):
    assert isinstance(code, int)
    assert isinstance(context, str)
    assert isinstance(interpretation, str)
    self.code = code
    self.context = context
    self.interpretation = interpretation

  def __repr__(self):
    return "%s(%r, %r, %r)" % (self.__class__.__name__,
                               self.code, self.context, self.interpretation)

  def encode(self):
    return (self.code,)

  @classmethod
  def interpret(cls, bytes, start_index):
    assert bytes[start_index] == self.code
    return (self.interpretation, 1)


class InsteonAddress(Code):
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
                          


class Registry(object):
  def __init__(self):
    self.contexts = []
    self.codes = []
    self.formats = {}

  def define_context(self, context):
    assert isinstance(context, str)
    if context in self.contexts: return
    self.contexts.append(context)

  def define_format(self, name, *tokens):
    format = []
    for token in tokens:
      if isinstance(token, int):
        pass
      elif isinstance(token, str):
        pass
      elif isinstance(token, Code):
        pass
      else:
        raise Exception("invalid format token: %r" % token)
    self.formats[name] = format

  def register(self, code):
    assert isinstance(code, Code)
    assert code.context in self.contexts
    assert isinstance(code.interpretation, str)
    self.codes.append(code)

  def get_code(self, interpretation):
    for code in self.codes:
      if code.interpretation == interpretation:
        return code
    return None

  def encode(self, *tokens):
    msg = bytearray()
    for token in tokens:
      if isinstance(token, int):
        if token >= 0 and token <= 0xFF:
          msg.append(token)
          continue
        else:
          pass
      elif isinstance(token, str):
        code = self.get_code(token)
        if code:
          msg.extend(code.encode())
          continue
      raise Exception("Bad token %r" % token)
    return msg

  def interpret(self, bytes):
    for b in bytes:
      pass

registry = Registry()
registry.define_context("start_byte")
registry.define_context("ack_nack")
registry.define_context("command_code")
registry.define_context("message_origin")

registry.register(ByteCode(0x02, "start_byte", "start_byte"))

registry.register(ByteCode(0x50, "message_origin", "insteon_modem"))
registry.register(ByteCode(0x60, "message_origin", "host"))

registry.register(ByteCode(0x06, "ack_nack", "ACK"))
registry.register(ByteCode (0x15, "ack_nack", "NACK"))
                  
registry.register(ByteCode(0x0F, "command_code", "ping")

# registry.encode("start_byte", "ping")

