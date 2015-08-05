#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Mon  4 Feb 14:12:24 2013

"""Builds a custom python script interpreter
"""

import os
import sys
import time
import logging

import zc.recipe.egg


class Recipe(object):
  """Just creates a python interpreter with the "correct" paths
  """

  def __init__(self, buildout, name, options):

    # Preprocess some variables
    self.buildout = buildout
    self.name = name
    self.options = options
    self.options.setdefault('interpreter', 'python')
    self.egg = zc.recipe.egg.Scripts(buildout, name, options)

    self.logger = logging.getLogger(name.capitalize())

    # Python interpreter script template
    self.template = """#!%(interpreter)s
# Automatically generated on %(date)s

'''Booting interpreter - starts a new one with a proper environment'''

import os

# builds a new path taking into considerating the user settings
path = os.environ.get("PYTHONPATH", "") + os.pathsep + "%(paths)s"
os.environ['PYTHONPATH'] = path.lstrip(os.pathsep) #in case PYTHONPATH is empty

# this will start a new Python process
import sys
os.execvp("%(interpreter)s", ["%(interpreter)s"] + sys.argv[1:])
"""


  def set_template(self, template):
    """Overwrites the currently used template for other installers"""
    self.template = template


  def __write_executable_file(self, name, content):
    f = open(name, 'w')
    current_umask = os.umask(0o022) # give a dummy umask
    os.umask(current_umask)
    perms = 0o777 - current_umask
    try:
      f.write(content)
    finally:
      f.close()
      os.chmod(name, perms)


  def install(self):

    requirements, ws = self.egg.working_set()
    retval = os.path.join(self.buildout['buildout']['bin-directory'], self.options['interpreter'])
    self.__write_executable_file(retval, self.template % {
      'date': time.asctime(),
      'paths': os.pathsep.join(ws.entries),
      'interpreter': sys.executable,
      })
    self.logger.info("Generated script '%s'." % retval)
    return (retval,)
