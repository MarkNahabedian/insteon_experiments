
import unittest
from translator import *

class TestTranslatorMatching (unittest.TestCase):
  def test_primitive(self):
    self.assertNotEqual(match("foo", "foo"), False)
    self.assertFalse(match(1, 2))

  def test_variable(self):
    m = match(4, MatchVariable("four"))
    self.assertNotEqual(m, False)
    self.assertEqual(m["four"], 4)

  def test_match_variable_and_slot(self):
    m = match(Byte(1), Byte(MatchVariable("value")))
    self.assertNotEqual(m, False)
    self.assertEqual(m["value"], 1)

  def test_start_byte(self):
    m = match(StartByte(), StartByte())
    self.assertNotEqual(m, False)

  def test_same_message(self):
    m = match(
      StandardMessageReceived(
        StartByte(),
        StandardMessageReceivedCode(),
        InsteonAddress(0x0f, 0x82, 0x9e),
        InsteonAddress(0x49, 0x93, 0xbf),
        MessageFlags(extended=False, max_hops=1,
                     group=True, response=True,
                     hops_remaining=1,
                     broadcast_NACK=False),
        OffCmd(),
        Byte(0x01)),
      StandardMessageReceived(
        StartByte(),
        StandardMessageReceivedCode(),
        InsteonAddress(0x0f, 0x82, 0x9e),
        InsteonAddress(0x49, 0x93, 0xbf),
        MessageFlags(extended=False, max_hops=1,
                     group=True, response=True,
                     hops_remaining=1,
                     broadcast_NACK=False),
        OffCmd(),
        Byte(0x01)))
    self.assertNotEqual(m, False)

  def test_pattern(self):
    msg = StandardMessageReceived(
      StartByte(),
      StandardMessageReceivedCode(),
      InsteonAddress(0x0f, 0x82, 0x9e),
      InsteonAddress(0x49, 0x93, 0xbf),
      MessageFlags(extended=False, max_hops=1,
                   group=True, response=True,
                   hops_remaining=1,
                   broadcast_NACK=False),
      OffCmd(),
      Byte(0x01))
    pattern = StandardMessageReceived(
      StartByte(),
      StandardMessageReceivedCode(),
      MatchVariable("from_address"),
      InsteonAddress(MatchVariable("to_address1"),
                     MatchVariable("to_address2"),
                     MatchVariable("to_address3")),
      MatchVariable("message_flags"),
      MatchVariable("cmd"),
      Byte(MatchVariable("value")))
    m = match(msg, pattern)
    self.assertNotEqual(m, False)
    self.assertEqual(m["cmd"], OffCmd())
    self.assertEqual(m["value"], 1)
    self.assertEqual(m["from_address"],
                     InsteonAddress(0x0f, 0x82, 0x9e))
    self.assertEqual(m["to_address1"], 0x49)
    self.assertEqual(m["to_address2"], 0x93)
    self.assertEqual(m["to_address3"], 0xbf)


if __name__ == '__main__':
  unittest.main()
