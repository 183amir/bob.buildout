#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Mon  4 Feb 14:12:24 2013

"""Builds custom scripts with the right paths for external dependencies
installed on different prefixes.
"""

import os
import sys
import time
import logging
from zc.recipe.egg import Scripts

from . import tools
from .envwrapper import EnvironmentWrapper


class Recipe(Scripts):
  """Just creates a given script with the "correct" paths
  """

  def __init__(self, buildout, name, options):

    self.buildout = buildout
    self.name = name
    self.options = options

    self.logger = logging.getLogger(self.name)

    # Gets a personalized eggs list or the one from buildout
    self.eggs = tools.eggs(buildout['buildout'], options, name)

    # Gets a personalized prefixes list or the one from buildout
    self.prefixes = tools.get_prefixes(buildout['buildout'])

    # Builds an environment wrapper, in case dependent packages need to be
    # compiled
    self.envwrapper = EnvironmentWrapper(self.logger,
        tools.debug(buildout['buildout']), self.prefixes)

    # initializes the script infrastructure
    super(Recipe, self).__init__(buildout, name, options)


  def install_on_wrapped_env(self):
    return tuple(super(Recipe, self).install())


  def install(self):
    with self.envwrapper as ew:
      return self.install_on_wrapped_env()


  update = install
