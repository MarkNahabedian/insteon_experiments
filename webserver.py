
import sys
assert sys.version_info >= (3, 2)

import datetime
import logging
import http.server
import html
import modem
from translator import *
from urllib.parse import urlparse, parse_qs


def logger():
  return logging.getLogger(__name__)


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
      if self.path.startswith("/favicon.ico"):
        self.send_error(404, "Resource not found")
      elif self.path.startswith('/group/on'):
        self.group_on()
      elif self.path.startswith('/group/off'):
        self.group_off()
      else:
        self.default()
    except Exception as e:
      logger().info("exception " + str(e))
      # Callees are responsible for their own error responses.
      pass

  def check_modem(self):
    if not self.server.insteon_modem:
      logger().info("No Insteon modem")
      self.send_error(404, "No Insteon modem")
      raise Exception("No Insteon modem")
    return self.server.insteon_modem

  def default(self):
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()
    self.wfile.write(bytes(link_groups_page(),
                           "utf8"))
    self.wfile.flush()

  def group_on(self):
    im = self.check_modem()
    if not modem: return
    group = self.get_group_number()
    im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(group), OnCmd(), Byte(0)).encode()))
    self.default()

  def group_off(self):
    self.check_modem()
    im = self.check_modem()
    if not modem: return
    group = self.get_group_number()
    im.sendCommand(bytearray(SendAllLinkCommand(LinkGroup(group), OffCmd(), Byte(0)).encode()))
    self.default()

  def get_group_number(self):
    u = urlparse(self.path)
    q = parse_qs(u.query)
    g = q.get('link_group')
    if not g:
      self.send_error(404, "No link_group query parameter")
      raise Exception("No link_group query parameter")
    g = g[0]
    return int(g)


LINK_GROUPS_PAGE_TEMPLATE = '''<html>
  <head>
    <title>Home Control</title>
    <base href="/" target="_top" <base />
  </head>
  <body>
    <h1>Home Control</h1>
    <p>Controller local time: {TIME}</p>
    <table margin="4">{LINK_GROUP_ROWS}</table>
  </body>
</html>'''

LINK_GROUP_ROW_TEMPLATE = '''
<tr>
  <td margin="4" valign="top" rowspan="{GROUP_DEVICE_COUNT}">group {GROUP_NUMBER}</td>
  <td margin="4" >{DEVICES}</td>
  <td margin="4" valign="center" rowspan="{GROUP_DEVICE_COUNT}">
    <a href="/group/on?link_group={GROUP_NUMBER}">On</href>
  </td>
  <td margin="4" valign="center" rowspan="{GROUP_DEVICE_COUNT}">
    <a valign="center" href="/group/off?link_group={GROUP_NUMBER}">Off</href>
  </td>
</tr>
'''


def link_groups_page():
  def group_device(device):
    return '{ADDRESS} {LOCATION} <br />'.format(**{
      'ADDRESS': str(device.address),
      'LOCATION': device.location
      })
  def lg_row(link_group):
    return LINK_GROUP_ROW_TEMPLATE.format(**{
      'GROUP_DEVICE_COUNT': str(len(link_group.devices)),
      'GROUP_NUMBER': str(link_group.link_group.byte),
      'DEVICES': '\n'.join([group_device(d) for d in link_group.devices])
      })
  return LINK_GROUPS_PAGE_TEMPLATE.format(**{
    'TIME': datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p %z"),
    'LINK_GROUP_ROWS': '\n'.join([lg_row(g) for g in modem.InsteonLinkGroup.groups.values()])
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

