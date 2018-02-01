# insteon_experiments
Experimenting with an Insteon modem and RaspberryPi.

You won't find anything of general utility here yet.  This project is
under development and is no where near useful yet.

My old Insteon controller flaked out on me, so I'm replacing it with a
SmartHome PowerLinc serial modem (model #2413S) and a RaspberryPi.
This project is the python code I'm using to communicate with the
modem and control things.

<h1>Generally USeful</h1>

singleton.py is a smple implementation of the singleton design pattern
copied from https://www.python.org/download/releases/2.2/descrintro/.

actions.py provides a cross-module initialization mechanism.  The
programmer identifies points in the lifecycle of the program that a
module might want to perform some action at.  Examples might include
at program startup or shutdown.  A module can define functions with
styleized names, e.g.

<pre>
def _do_onStartup_logging():
  logging.basicConfig(filename='modem.log', level=logging.INFO)
  global _logger
  _logger = logging.getLogger(__name__)

</pre>

The main function of the application would call

</pre>
actions.run('onStartup')
</pre>

to execute all "onStartup" actions defined in any imported module.


<h1>Modeling Insteon Messages</h1>

translator.py implements a (incomplete) model of the messages sent to
and from the Insteon modem.  It includes methods for translatiing
between a human and program readable representation of a message to
the list of bytes to communicate with the modem.

For example, the programatic representation of a command to turn on
the devices in AllLink group 1 is

<pre>
SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))
</pre>

The byte representation of that command is

<pre>
from translator import *
cmd = SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))
cmd.encode()
[2, 97, 1, 17, 0]
</pre>


<h1>Communicating with the Modem</h1>

modem.py implements communication with the modem.

<pre>
import modem
from translator import *

im = modem.InsteonModem("/dev/ttyUSB0")

cmd = SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))
im.sendCommand(bytearray(cmd.encode()))
rsp = im.readResponse()
interpret_all(rsp, ReadFromModem)[0]
[Echo(SendAllLinkCommand(StartByte(), AllLinkCmd(), LinkGroup(0x01), OnCmd(), Byte(0x00)), Ack())]
</pre>

ReadFromModem is the subclass of Translator that serves as the
superclass for all messages that could be read from the modem.  In
this case we just get the command we sent echoed back to us along with
an Ack.


<h1>Scheduling Events</h1>

schedule.py implements scheduling of modem commands and other events.

For example, to turn on all Link group 1 devices at 7:00pm every day:

<pre>
Event(InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))),
      DailyAt(19, 0)).schedule()
</pre>

solar.py implements a not very accurate model for sunrise and sunset.
It can also be used to schedule events:

<pre>
sun = solar.Solar(myLatitude, myLongitude)

Event(InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))),
      solar.SolarEvent(sun, 'sunset')).schedule()
</pre>
