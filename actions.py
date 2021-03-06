# This module supports the ability for other modules to register
# actions that should be performed at specified times durinng the
# lifecycle of the application.  It's meant to provide functionality
# similar to that of "initialization lists" in the MIT Lisp Machine
# system.

import logging
import re
import sys


ACTION_NAME_PATTERN = re.compile('^_do_(?P<actionname>[0-9A-Za-z]+)(_(?P<extension>[0-9A-Za-z_]+))?$')


def _find_actions_for_module(m, actionname):
  '''Returns a list of all of the actions for actionname in the specified
     module in the order they are to be run.'''
  found = []
  for key, val in m.__dict__.items():
    m = ACTION_NAME_PATTERN.match(key)
    if not m:
      continue
    if not actionname == m.group('actionname'):
      continue
    found.append((m.group('extension'), val))
  # Now sort the results
  # The builtin cmp function sorts None before '', which is what we want.
  found = sorted(found, key=lambda f: f[0])
  return [f[1] for f in found]


def run(actionname, **action_specific_kwargs):
  '''run runs all of the actions for actionname, across all imported modules.'''
  for m in sys.modules.values():
    if not m:    # Could be None.
      continue
    actions = _find_actions_for_module(m, actionname)
    for a in actions:
      logging.getLogger(__name__).info('Running action %s %r %r' % (actionname, m, a)) 
      a(**action_specific_kwargs)


def list_action_names():
  '''list_action_names returns a dict associating action names with
  modules that implement behavior for that action.
  It's used to see all actions that are defined.'''
  result = {}
  for module in sys.modules.values():
    if not module:    # Could be None.
      continue
    for key in  module.__dict__.keys():
      m = ACTION_NAME_PATTERN.match(key)
      if not m:
        continue
      actionname = m.group('actionname')
      if actionname:
        if not actionname in result:
          result[actionname] = []
        if not module in result[actionname]:
          result[actionname].append(module)
  return result
