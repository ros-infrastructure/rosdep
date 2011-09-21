#!/usr/bin/env python
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Willow Garage, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Author Tully Foote/tfoote@willowgarage.com, Ken Conley

import os
import subprocess

from rospkg.os_detect import OS_OSX

from ..core import InstallFailed
from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import Installer, PackageManagerInstaller, TYPE_CODENAME
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

# add additional os names for brew, macports (TODO)
OSXBREW_OS_NAME = 'osxbrew'

BREW_INSTALLER = 'brew'
MACPORTS_INSTALLER = 'macports'

def register_installers(context):
    context.set_installer(MACPORTS_INSTALLER, MacportsInstaller())

def register_platforms(context):
    register_osx(context)
    #register_osxbrew(context)
    
def register_osx(context):
    context.add_os_installer_key(OS_OSX, MACPORTS_INSTALLER)
    context.add_os_installer_key(OS_OSX, PIP_INSTALLER)
    context.add_os_installer_key(OS_OSX, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_OSX, MACPORTS_INSTALLER)
    context.set_os_version_type(OS_OSX, TYPE_CODENAME)
    
def register_osxbrew(context):
    context.add_os_installer_key(OSXBREW_OS_NAME, PIP_INSTALLER)
    context.add_os_installer_key(OSXBREW_OS_NAME, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OSXBREW_OS_NAME, BREW_INSTALLER)
    context.set_os_version_type(OS_OSX, TYPE_CODENAME)
    raise NotImplemented

def is_port_installed():
    try:
        subprocess.Popen(['port'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except OSError:
        return False
    
def port_detect(packages, exec_fn=None):
    ret_list = []
    if not is_port_installed():
        return ret_list
    if exec_fn is None:
        exec_fn = read_stdout
    std_out = exec_fn(['port', 'installed']+pkgs)
    for pkg in std_out.split('\n'):
        pkg_row = pkg.split()
        if len(pkg_row) == 3 and pkg_row[0] in pkgs and pkg_row[2] =='(active)':
            ret_list.append(pkg_row[0])
    return ret_list

class MacportsInstaller(PackageManagerInstaller):
    """ 
    An implementation of the :class:`Installer` API for use on
    macports systems.
    """
    def __init__(self):
        super(MacportsInstaller, self).__init__(port_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        if not is_port_installed():
            raise InstallFailed((MACPORTS_INSTALLER, 'MacPorts is not installed'))
        packages = self.get_packages_to_install(resolved)
        if not packages:
            return []
        else:
            #TODO: interactive
            return ['sudo', 'port', 'install'] + packages

def brew_detect(package_resolutions, exec_fn=None):
    """ 
    Given a list of package, return the list of installed packages.

    :param packages: List of :class:`HomebrewResolution` instances
    """
        
    if exec_fn is None:
        exec_fn = read_stdout

    # extract package names from resolutions
    packages = []
    for r in package_resolutions:
        packages.extend(r.packages)
    ret_list = []
    std_out = exec_fn(['brew', 'list'])

    # we will basically create new resolution instances in order to
    # preserve the lists properly
    for package in std_out.split():
        matches = get_resolutions(package)
        ret_list.extend(matches)
    
    return ret_list

#TODOXXX: none of this code is correct
def _validate_homebrew_resolutions(resolutions):
    if len(resolutions) == 1:
        resolutions[0]
    args = resolutions[0].args
    for r in resolutions:
        if set(r.args) != set(args):
            raise InvalidRosdepData("conflicting args in homebrew specifications:\n%s"%('\n'.join([str(x) for x in resolutions])))
    else:
        return resolutions[0]

#TODOXXX: none of this code is correct
# what it should do: split all resolutions into single-package resolution, then just use equality tests
def validate_homebrew_resolutions(package, resolutions):
    """
    Validate :class:`HomebrewResolution` instances that contain the
    specified *package*.  To pass validation, all resolutions with the
    specified package must have the same arguments.
    
    """
    vals = [r for r in resolutions if package in r.packages]
    if vals:
        # make sure vals have same specs
        return _validate_homebrew_resolutions(val)
        if v.formula_uris:
            idx = v.packages.index(package)
            return HomebrewResolution([package], v.formula_uris[idx], v.args)
        else:
            return HomebrewResolution([package], [], v.args)
    else:
        return []

class HomebrewResolution(object):
    """Stores resolution information for a Homebrew rosdep"""

    def __init__(self, packages, formula_uris, args):
        """
        :param formula_uris: If specified, overrides packages, which will only be used for detection.
        :raises InvalidRosdepData: if formula_uris are specified and not the same length as packages
        """
        if formula_uris and len(packages) != len(formula_uris):
            raise InvalidRosdepData('When "formula_uris" are specified, they must be the same lengths as "packages": %s vs %s'%(str(packages), str(formula_uris)))
        self.packages = packages
        self.formula_uris = formula_uris
        self.args = args
        
    def __eq__(self, other):
        return other.packages == self.packages and \
               other.formula_uris == self.formula_uris and \
               other.args == self.args

    def __str__(self):
        return ' '.join(self.packages) + ' '.join(self.args)

#TODO: override unique()
class HomebrewInstaller(PackageManagerInstaller):

    """An implementation of Installer for use on homebrew systems."""

    def __init__(self):
        super(HomebrewInstaller, self).__init__(brew_detect, supports_depends=True)

    def resolve(self, rosdep_args):
        """
        See :meth:`Installer.resolve()`
        """
        packages = super(HomebrewInstaller, self).resolve(rosdep_args)
        #TODO: seems that args is superfluous
        args = rosdep_args.get("args", []) + rosdep_args.get("options", [])
        return HomebrewResolution(packages, args)

    def _validate_resolved(self):
        pass
        
    def get_install_command(self, resolved, interactive=True, reinstall=False):
        if not is_brew_installed():
            raise InstallFailed((BREW_INSTALLER, 'Homebrew is not installed'))
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        commands = []
        for r in packages:
            commands.append(['brew', 'install'] + r.args + r.packages)
        return commands
