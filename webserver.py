
import logging
import sys
import http.server

assert sys.version_info >= (3, 0)

class ResponseHandler(http.server.BaseHTTPRequestHandler):
  def __init__(self):
    pass
  def do_GET(self):
    _logger.info("GET")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.wfile.write("<html><head><title>foo</title></head><body>Hello.</body></html>")


def run(server_class=http.server.HTTPServer,
        handler_class=ResponseHandler):
  server_address = ('', 8000)
  httpd = server_class(server_address, handler_class)
  httpd.serve_forever()


if __name__ == '__main__':
  global _logger
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  _logger = logging.getLogger(__name__)
  _logger.info("Starting Webserver.")
  try:
    run()
  finally:
    _logger.info("Webserver Exited.")
  logging.shutdown()


