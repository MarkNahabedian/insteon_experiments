# Implementation of the singleton pattern.  Taken from
# https://www.python.org/download/releases/2.2/descrintro/.
#
# Recomendation:  Add a guard to any __init__ method to return
# immediately if the singleton instance has already been initialized.

class Singleton(object):
  def __new__(cls, *args, **kwds):
    it = cls.__dict__.get("__it__")
    if it is not None:
      return it
    cls.__it__ = it = object.__new__(cls)
    it.init(*args, **kwds)
    return it

  def init(self, *args, **kwds):
    pass

