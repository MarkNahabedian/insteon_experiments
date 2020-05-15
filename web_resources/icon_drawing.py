
import math
from yattag import Doc, indent

SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def path_step(s, *values):
  return s + " ".join([" %d" % v for v in values])


def on_off(on=False, width=64, height=64, ray_count = 7):
  doc, tag, text = Doc().tagtext()
  with tag("g", ("class", "on" if on else "off")):
    centerX = width / 2
    centerY = height / 2
    r = min(width, height) / 2
    bulb_radius = r * .4
    ray_inside = r * .6
    ray_outside = r * .9
    with tag("circle",
             ("class", "bulb"),
             cx = centerX,
             cy = centerY,
             r = bulb_radius):
      pass
    if on:
      d = ""
      for i in range(ray_count):
        a = 2 * math.pi * i / ray_count
        d += path_step("M",
                       centerX + ray_inside * math.cos(a),
                       centerY + ray_inside * math.sin(a))
        d += path_step("L",
                       centerX + ray_outside * math.cos(a),
                       centerY + ray_outside * math.sin(a))
      with tag("path", ("class", "ray"), d=d):
        pass
  return indent(doc.getvalue())


def ac_source(width=64, height=64):
  doc, tag, text = Doc().tagtext()
  with tag("g", ("class", "ac-source")):
    centerX = width / 2
    centerY = height / 2
    with tag("circle",
             cx = centerX,
             cy = centerY,
             r = min(width, height) / 2):
      pass
    wavelength = width * 0.6
    amplitude = height * 0.2
    d = "M"
    for i in range(17):
      f = (i - 8) / 16  # -1 to 1
      x = centerX + wavelength * f
      y = centerY + amplitude * math.sin(f * 2 * math.pi)
      d += " %.4f %.4f" % (x, y)
    with tag("path", ("d", d)):
      pass
  return indent(doc.getvalue())


def lamp(width=64, height=64):
  doc, tag, text = Doc().tagtext()
  with tag("g", ("class", "lamp")):
    centerX = width / 2
    centerY = height / 2
    with tag("circle",
             cx = centerX,
             cy = centerY,
             r = 0.9 * min(width, height) / 2):
      pass
    offset = width / 4
    ar = offset / 2
    with tag("path", (
        "d",
        path_step("M", centerX - offset, height) +
        path_step("V", centerY + ar / 2) +
        path_step("a", ar, ar, 0, 0, 1, offset, 0) +
        path_step("a", ar, ar, 0, 0, 1, offset, 0) +
        path_step("V", height))): pass
  return indent(doc.getvalue())
    

print(on_off(on=True))
print(on_off(on=False))

# print(ac_source())

# print(lamp())

