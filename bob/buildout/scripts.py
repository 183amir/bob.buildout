#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.dos.anjos@gmail.com>
# Mon  4 Feb 14:12:24 2013

"""Builds custom interpreters with the right paths for external Bob
"""

import logging
import copy

import pip
import oset
import distutils
import zc.recipe.egg
import syseggrecipe.recipe

from . import tools
from .envwrapper import EnvironmentWrapper
from .python import Recipe as PythonRecipe


class Recipe(object):
  """Just creates a given script with the "correct" paths
  """

  def __init__(self, buildout, name, options):

    self.buildout = buildout
    self.name = name
    self.options = options.copy()

    self.logger = logging.getLogger(name.capitalize())

    # Are we in debug mode?
    self.debug = tools.debug(buildout['buildout'])

    # Gets a personalized eggs list or the one from buildout
    self.eggs = oset.oset(tools.eggs(buildout['buildout'], options, name))

    # Gets a personalized prefixes list or the one from buildout
    prefixes = tools.get_prefixes(buildout['buildout'])

    # Builds an environment wrapper, if dependent packages need to be compiled
    self.envwrapper = EnvironmentWrapper(self.logger, self.debug, prefixes)

    # Does not install the python interpreter from zc.egg.recipe (use ours)
    if 'interpreter' in self.options: del self.options['interpreter']

    # Does not install dependent scripts by default
    self.options.setdefault('dependent-scripts', 'false')


  def install(self):

    # gets a list (from pip), of what is currently available on the system
    # and are not in edition mode
    system_eggs = oset.oset(pip.get_installed_distributions(
        include_editables=False))

    # excludes packages which are currently installed on this buildout
    bdir = self.buildout['buildout']['directory']
    local_eggs = oset.oset([k for k in system_eggs if \
            k.location.startswith(bdir)])
    system_eggs -= local_eggs

    # installs system eggs using syseggrecipe
    options = {
            'eggs': '\n'.join([k.key for k in system_eggs]),
            'force-sysegg': 'true',
            }
    name = self.name + '-system-eggs'
    recipe = syseggrecipe.recipe.Recipe(self.buildout, name, options)
    retval = recipe.install()

    # this will effectively build our eggs for the current buildout
    with self.envwrapper as ew:

      name = self.name + '-user-scripts'
      options = self.options.copy()
      eggs = copy.deepcopy(self.eggs)
      # boost environment with more executables we always use
      eggs.add('sphinx')
      eggs.add('nose')
      eggs.add('coverage')
      options['eggs'] = '\n'.join(eggs)
      egg_recipe = zc.recipe.egg.Scripts(self.buildout, name, options)
      retval += tuple(egg_recipe.install())

    # installs python interpreter
    options = self.options.copy()
    options['eggs'] = '\n'.join(self.eggs)
    name = self.name + '-python'
    python_recipe = PythonRecipe(self.buildout, name, options)
    retval += tuple(python_recipe.install())

    # installs a gdb-powered python interpreter
    if self.debug:
      from .gdbpy import Recipe as GdbPythonRecipe
      options = self.options.copy()
      options['eggs'] = '\n'.join(self.eggs)
      name = self.name + '-gdb-python'
      gdbpy_recipe = GdbPythonRecipe(self.buildout, name, options)
      retval += tuple(gdbpy_recipe.install())

    # if ipython is available as a system package, install an interpreter
    all_eggs = pip.get_installed_distributions()
    ipython_egg = [k for k in all_eggs if k.key == 'ipython']
    if ipython_egg:

      options = self.options.copy()
      eggs = copy.deepcopy(self.eggs)
      eggs.add('ipython')
      options['eggs'] = '\n'.join(eggs)
      if 'interpreter' in options:
        options['scripts'] = 'i' + options['interpreter']
        del options['interpreter']
      else:
        options['scripts'] = 'ipython'
      options['dependent-scripts'] = 'false'

      ipython_version = distutils.version.LooseVersion(ipython_egg[0].version)
      if ipython_version > distutils.version.LooseVersion('3.0.0a0'):
        ipython_app = 'IPython.terminal.ipapp:launch_new_instance'
      else: #version 2 or less
        ipython_app = 'IPython.frontend.terminal.ipapp:launch_new_instance'

      options['entry-points'] = '%s=%s' % (options['scripts'], ipython_app)
      name = self.name + '-ipython'
      ipython_recipe = zc.recipe.egg.Scripts(self.buildout, name, options)
      retval += tuple(ipython_recipe.install())

    return retval

  update = install
