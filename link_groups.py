class InsteonLinkGroup(object):
  groups = {}

  @classmethod
  def lookup(cls, link_group):
    if isinstance(link_group, int):
      link_group = translator.LinkGroup(link_group)
    assert isinstance(link_group, translator.LinkGroup)
    if link_group in cls.groups:
      return cls.groups[link_group]
    return None

  def __init__(self, link_group, devices=[]):
    if isinstance(link_group, int):
      link_group = translator.LinkGroup(link_group)
    assert isinstance(link_group, translator.LinkGroup)
    if self.__class__.lookup(link_group):
      raise GroupExists(link_group)
    self.link_group = link_group
    self.devices = devices
    self.__class__.groups[self.link_group] = self

  def add_device(self, device):
    assert isinstance(device, InsteonDevice)
    if device in self.devices:
      return
    self.devices.append(device)

  def __repr__(self):
    return '%s(%r, %r)' % (self.__class__.__name__, self.link_group, self.devices)
