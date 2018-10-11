
# Read user curated information about insteon devices from a tab
# delimited text file.  The text file is expected to have a header
# that includes the fields "address" and "location".  A device address
# is three bytes expressed in hexadecimal and separated by a period.

import csv
import modem
import translator


def read_device_descriptions(filepath):
  '''Reads insteon device descriptions from the specified file and 
     associates it with the specified devices.'''
  with  open(filepath, "r") as f:
    reader = csv.DictReader(f, dialect='excel-tab')
    for record in reader:
      a = record.get('address')
      l = record.get('location')
      if (not a) or (not l): continue
      device = modem.InsteonDevice.lookup(
          *[ bytes.fromhex(b)[0] for b in a.split('.')])
      if not device:
        continue
      device.location = l

