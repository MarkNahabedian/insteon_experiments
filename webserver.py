
import sys
assert sys.version_info >= (3, 2)

import sys
import os.path
import logging
import http.server
import html
import modem
from config import now, TIME_FORMAT, WEB_TIME_FORMAT
from schedule import Scheduler
from translator import *
from urllib.parse import urlparse, parse_qs


logging.getLogger(__name__).propagate = True

def logger():
  return logging.getLogger(__name__)


def file_resource_path(filename):
  base = os.path.dirname(sys.modules[__name__].__file__)
  return os.path.join(base, 'web_resources', filename)


class MyRequestHandler(http.server.BaseHTTPRequestHandler):
  def do_HEAD(self):
    logger().info("HEAD")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()

  def do_GET(self):
    self.error_message_format = "eRRoR"
    logger().info("GET " + self.path)
    try:
      if self.path == '/favicon.ico':
        self.send_error(404, 'Resource not found')
      elif self.path == '/stylesheet.css':
        self.send_file(file_resource_path('stylesheet.css'))
      elif self.path.startswith('/group/on'):
        self.group_on()
      elif self.path.startswith('/group/off'):
        self.group_off()
      elif self.path == '/':
        self.main_page()
      else:
        self.send_error(404, "Resource not found: %s" % self.path)
    except Exception as e:
      logger().exception("exception " + str(e))
      # Callees are responsible for their own error responses.
      pass

  def check_modem(self):
    if not self.server.insteon_modem:
      logger().info("No Insteon modem")
      self.send_error(404, "No Insteon modem")
      raise Exception("No Insteon modem")
    return self.server.insteon_modem

  def main_page(self):
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()
    self.wfile.write(bytes(main_page(),
                           "utf8"))
    self.wfile.flush()

  def send_file(self, path):
    try:
      with open(path) as f:
        contents = f.read()
        self.send_response(200, "Ok")
        self.send_header('Content-type','text/css')
        self.end_headers()
        self.flush_headers()
        self.wfile.write(bytes(contents, "utf8"))
        self.wfile.flush()
    except Exception as e:
      self.send_error(404, str(e))
        
  def group_on(self):
    im = self.check_modem()
    if not modem: return
    group = self.get_group_number()
    im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(group), OnCmd(), Byte(0)).encode()))
    self.main_page()

  def group_off(self):
    self.check_modem()
    im = self.check_modem()
    if not modem: return
    group = self.get_group_number()
    im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(group), OffCmd(), Byte(0)).encode()))
    self.main_page()

  def get_group_number(self):
    u = urlparse(self.path)
    q = parse_qs(u.query)
    g = q.get('link_group')
    if not g:
      self.send_error(404, "No link_group query parameter")
      raise Exception("No link_group query parameter")
    g = g[0]
    return int(g)


DEFAULT_PAGE_TEMPLATE = '''<html>
  <head>
    <title>Home Control</title>
    <base href="/" target="_top" <base />
    <link rel="stylesheet" href="stylesheet.css" type="text/css" />
  </head>
  <body>
    <h1>Home Control</h1>
    <p>Controller local time: {TIME}</p>
    <h2>Link Groups</h2>
    <table class="link-groups">{LINK_GROUP_ROWS}</table>
    <h2>Devices</h2>
    <table class="devices">{DEVICE_ROWS}</table>
    <h2>Schedule</h2>
    <table class="schedule">{SCHEDULE_ROWS}</table>
  </body>
</html>'''

LINK_GROUP_ROW_TEMPLATE = '''
<tr>
  <td margin="4" valign="top" rowspan="{GROUP_DEVICE_COUNT}">group {GROUP_NUMBER}</td>
  <td margin="4" >{DEVICE_ROWS}</td>
  <td margin="4" valign="center" rowspan="{GROUP_DEVICE_COUNT}">
    <a href="/group/on?link_group={GROUP_NUMBER}">On</href>
  </td>
  <td margin="4" valign="center" rowspan="{GROUP_DEVICE_COUNT}">
    <a valign="center" href="/group/off?link_group={GROUP_NUMBER}">Off</href>
  </td>
</tr>
'''

INSTEON_DEVICE_ROW_TEMPLATE = '''
<tr>
  <td class="address">{ADDRESS}</td>
  <td class="caregory">{CATEGORY}</td>
  <td class="subcategory">{SUBCATEGORY}</td>
  <td class="firmware_version">{FIRMWARE_VERSION}</td>
  <td class="location">{LOCATION}</td>
</tr>
'''

SCHEDULE_ROW_TEMPLATE = '''
<tr>
  <td valign="top">{NEXT_TIME}</td>
  <td valign="top">{ACTION}</td>
</tr>
'''

def main_page():
  def group_device(device):
    return '{ADDRESS} {LOCATION} <br />'.format(**{
      'ADDRESS': html.escape(str(device.address)),
      'LOCATION': html.escape(device.location)
      })
  def lg_row(link_group):
    return LINK_GROUP_ROW_TEMPLATE.format(**{
      'GROUP_DEVICE_COUNT': str(len(link_group.devices)),
      'GROUP_NUMBER': str(link_group.link_group.byte),
      'DEVICE_ROWS': '\n'.join([group_device(d) for d in link_group.devices])
      })
  def device_row(device):
    return INSTEON_DEVICE_ROW_TEMPLATE.format(**{
      'ADDRESS': device.address,
      'CATEGORY': device.category or '',
      'SUBCATEGORY': device.subcategory or '',
      'FIRMWARE_VERSION': device.firmware_version or '',
      'LOCATION': device.location or ''
      })
  def schedule_row(event):
    return SCHEDULE_ROW_TEMPLATE.format(**{
      'NEXT_TIME': html.escape(event.when.strftime(WEB_TIME_FORMAT)) if event.when else '',
      'ACTION': html.escape("%r" % event.action_function)
    })
  return DEFAULT_PAGE_TEMPLATE.format(**{
    'TIME': now().strftime(WEB_TIME_FORMAT),
    'LINK_GROUP_ROWS': '\n'.join([lg_row(g) for g in modem.InsteonLinkGroup.groups.values()]),
    'DEVICE_ROWS': '\n'.join([device_row(d) for d in modem.InsteonDevice.devices.values()]),
    'SCHEDULE_ROWS': '\n'.join([schedule_row(e) for e in Scheduler().queued_events()])
  })


def run(port, insteon_modem):
  server_address = ('', port)
  httpd = http.server.HTTPServer(server_address, MyRequestHandler)
  httpd.insteon_modem = insteon_modem
  try: 
    logger().info("Starting Webserver.")
    httpd.serve_forever()
  finally:
    logger().info("Webserver Exited.")


if __name__ == '__main__':
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  run(8000)
  logging.shutdown()

