#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Mon  4 Feb 14:12:24 2013

"""Builds custom interpreters with the right paths for external Bob
"""

import logging

import pip
import oset
import distutils
import zc.recipe.egg

from . import tools
from .envwrapper import EnvironmentWrapper
from .python import Recipe as PythonRecipe
from .extension import DEV_EGGS


class Recipe(object):
  """Just creates a given script with the "correct" paths
  """

  def __init__(self, buildout, name, options):

    self.buildout = buildout
    self.name = name
    self.options = options.copy()

    self.logger = logging.getLogger(name.capitalize())

    # Are we in debug mode?
    self.debug = tools.debug(buildout)

    # Gets a personalized eggs list or the one from buildout
    self.eggs = oset.oset(tools.eggs(buildout, options, name))

    # Gets a personalized prefixes list or the one from buildout
    prefixes = tools.get_prefixes(buildout)

    # Builds an environment wrapper, if dependent packages need to be compiled
    self.envwrapper = EnvironmentWrapper(self.logger, self.debug, prefixes)

    # Does not install the python interpreter from zc.egg.recipe (use ours)
    if 'interpreter' in self.options: del self.options['interpreter']

    # Does not install dependent scripts by default
    self.options.setdefault('dependent-scripts', 'false')


  def install(self):

    retval = tuple()

    # this will effectively build our eggs for the current buildout
    with self.envwrapper as ew:

      name = self.name + '-user-scripts'
      options = self.options.copy()
      eggs = list(self.eggs)
      # boost environment with more executables we always use
      extras = ['Sphinx', 'nose', 'coverage']
      satisfied, linked = tools.link_system_eggs(self.buildout, extras)
      retval += linked
      eggs += extras
      options['eggs'] = '\n'.join(oset.oset(DEV_EGGS + eggs + extras))
      egg_recipe = zc.recipe.egg.Scripts(self.buildout, name, options)
      retval += tuple(egg_recipe.install())

    # installs a python interpreter
    options = self.options.copy()
    options['eggs'] = '\n'.join(oset.oset(DEV_EGGS + list(self.eggs)))
    name = self.name + '-python'
    python_recipe = PythonRecipe(self.buildout, name, options)
    retval += tuple(python_recipe.install())

    # installs a gdb-powered python interpreter
    if self.debug:
      from .gdbpy import Recipe as GdbPythonRecipe
      options = self.options.copy()
      options['eggs'] = '\n'.join(oset.oset(DEV_EGGS + list(self.eggs)))
      name = self.name + '-gdb-python'
      gdbpy_recipe = GdbPythonRecipe(self.buildout, name, options)
      retval += tuple(gdbpy_recipe.install())

    # if ipython is available as a system package, install an interpreter
    all_eggs = pip.get_installed_distributions(local_only=False)
    ipython_egg = [k for k in all_eggs if k.key == 'ipython']
    if ipython_egg:

      options = self.options.copy()
      eggs = list(self.eggs)
      extras = ['ipython']
      satisfied, linked = tools.link_system_eggs(self.buildout, extras)
      retval += linked
      options['eggs'] = '\n'.join(oset.oset(DEV_EGGS + eggs + extras))
      if 'interpreter' in options:
        options['scripts'] = 'i' + options['interpreter']
        del options['interpreter']
      else:
        options['scripts'] = 'ipython'
      options['dependent-scripts'] = 'false'

      ipython_version = distutils.version.LooseVersion(ipython_egg[0].version)
      if ipython_version > distutils.version.LooseVersion('2.0.0a0'):
        ipython_app = 'IPython.terminal.ipapp:launch_new_instance'
      else: #version 1 or less
        ipython_app = 'IPython.frontend.terminal.ipapp:launch_new_instance'

      options['entry-points'] = '%s=%s' % (options['scripts'], ipython_app)
      name = self.name + '-ipython'
      ipython_recipe = zc.recipe.egg.Scripts(self.buildout, name, options)
      retval += tuple(ipython_recipe.install())

    return retval

  update = install
