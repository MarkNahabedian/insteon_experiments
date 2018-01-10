# This file provides a way of encoding and decoding insteon commands.



class Code(Object):
  def __init__(self, code, context, interpretation):
    assert isinstance(code, int)
    assert isinstance(context, str)
    assert isinstance(interpretation, str)
    self.code = code
    self.context = context
    self.interpretation = interpretation

  def __repr__(self):
    return "Code(%r, %r, %r)" % (self.code, self,context, self.interpretation)


class Registry(Object):
  def __init__(self):
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
        
    self.formats[name] = format

  def register(self, code):
    assert isinstance(code, Code)
    assert code.context in self.contexts
    assert isinstance(code.interpretation, str)
    self.code.append(code)

  def get_code(self, interpretation):
    for code in self.codes:
      if code.interpretation == interpretation:
        return code.code
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
          msg.append(code)
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

registry.register(Code(0x02, "start_byte", "start_byte"))

registry.register(Code(0x50, "message_origin", "insteon_modem"))
registry.register(Code(0x60, "message_origin", "host"))

registry.register(Code(0x06, "ack_nack", "ACK"))
registry.register(Code(0x15, "ack_nack", "NACK"))
                  
