# insteon_experiments
Experimenting with an Insteon modem and RaspberryPi.

Status: 
I've been using this package to control a few lights since late 2017.

My old Insteon controller flaked out on me, so I've replaced it with a
SmartHome PowerLinc serial modem (model #2413S) and a RaspberryPi.
This project is the python code I'm using to communicate with the
modem and to control things.


<h1>Dependencies</h1>

<pre>
pip install PyDispatcher
</pre>

<pre>
pip install pySerial
</pre>

<pre>
pip install tzlocal
</pre>


<h1>Files of General Use</h1>

<b>singleton.py</b> is a simple implementation of the singleton design pattern
copied from https://www.python.org/download/releases/2.2/descrintro/.

<b>actions.py</b> provides a cross-module initialization mechanism.  The
programmer identifies points in the lifecycle of the program that a
module might want to perform some action at.  Examples might include
at program startup or shutdown, or startup or teardown of a particular
service.  A module can define functions with styleized names, e.g.

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

<b>translator.py</b> implements a (incomplete) model of the messages sent to
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

<b>modem.py</b> implements communication with the modem.

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

<b>schedule.py</b> implements scheduling of modem commands and other events.

For example, to turn on all Link group 1 devices at 7:00pm every day:

<pre>
Event(InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))),
      DailyAt(19, 0)).schedule()
</pre>

<b>solar.py</b> implements a not very accurate model for sunrise and sunset.
It can also be used to schedule events:

<pre>
sun = solar.Solar(myLatitude, myLongitude)

Event(InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(1), OnCmd(), Byte(0))),
      solar.SolarEvent(sun, 'sunset')).schedule()
</pre>


<h1>Cataloging Devices</h1>

The call

<pre>
<i>insteon_modem</i>.read_link_db()
</pre>

queries to identify all link groups.


<h1>Web Server</h1>

The webserver module provides a very simple web interface on the
specified port.  It presents a page that lists the discovered link
groups and allows for each group's devices to be sent an on or an off
message.

<pre>
import webserver

webserver.run(<i>port</i>, <i>insteon_modem</i>)
</pre>


<h1>Example Configuration</h1>

<pre>
import actions
import insteon_logging
import modem
import pytz
import solar
import webserver
from schedule import DailyAt, TimeOffset, Event, Scheduler

im = modem.InsteonModem("/dev/ttyUSB0")

sun = solar.Solar(<i>latitude</i>, <i>longitude</i>)

im.read_link_db()

# Schedule turning the devices in link group 4 on and off.
Event(modem.InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(4), OnCmd(), Byte(0))),
      # On 20 minutes before calculated sunset
      TimeOffset(-20, solar.SolarEvent(sun, 'sunset'))).schedule()

Event(modem.InsteonCommandAction(im, SendAllLinkCommand(LinkGroup(4), OffCmd(), Byte(0))),
      # Off at 11pm.
      DailyAt(23, 0)).schedule()

webserver.run(8000, im)
</pre>


<h1>Automatic Startup after Reboot</h1>

I run Raspbian on my Raspberry Pi.  To start my home control
scheduling and web services system when Raspbian comes up in
multi-user mode, I add this line

<pre>
(cd /home/pi/insteon_experiments; PYTHONPATH='/home/pi/.local/lib/python3.5/site-packages'  /usr/bin/python3.5 /home/pi/insteon_experiments/main.py &) >/home/pi/insteon_experiments/STARTUP_LOG 2>&1
</pre>

to <tt>/etc/rc.local</tt>.


<h1>Insteaon Resources</h1>

- [http://www.madreporite.com/insteon/insteon.html](http://www.madreporite.com/insteon/insteon.html) provides a bunch of links to links and documentation.

- [Insteon FAQ](https://docs.google.com/document/pub?id=1XDrgT4RXY5CPzBJ9P2IgQ26Wk2pDuozrmaimeN_TlSo)

