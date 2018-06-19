
import logging
import sys
import http.server

assert sys.version_info >= (3, 0)

class MyRequestHandler(http.server.BaseHTTPRequestHandler):
  def do_HEAD(self):
    _logger.info("HEAD")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()

  def do_GET(self):
    _logger.info("GET")
    self.send_response(200, "Ok")
    self.send_header('Content-type','text/html')
    self.end_headers()
    self.flush_headers()
    self.wfile.write(bytes("<html><head><title>foo</title></head><body>Hello.</body></html>", "utf8"))
    self.wfile.flush()


def run():
  server_address = ('', 8000)
  httpd = http.server.HTTPServer(server_address, MyRequestHandler)
  try: 
    _logger.info("Starting Webserver.")
    httpd.serve_forever()
  finally:
    _logger.info("Webserver Exited.")


if __name__ == '__main__':
  global _logger
  logging.basicConfig(filename='webserver.log', level=logging.INFO)
  _logger = logging.getLogger(__name__)
  run()
  logging.shutdown()

