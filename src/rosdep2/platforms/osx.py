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

import subprocess
import re

from rospkg.os_detect import OS_OSX

from ..core import InstallFailed
from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller, TYPE_CODENAME
from ..shell_utils import read_stdout

# add additional os names for brew, macports (TODO)
OSXBREW_OS_NAME = 'osxbrew'

BREW_INSTALLER = 'homebrew'
MACPORTS_INSTALLER = 'macports'

def register_installers(context):
    context.set_installer(MACPORTS_INSTALLER, MacportsInstaller())
    context.set_installer(BREW_INSTALLER, HomebrewInstaller())
    
def register_platforms(context):
    context.add_os_installer_key(OS_OSX, BREW_INSTALLER)
    context.add_os_installer_key(OS_OSX, MACPORTS_INSTALLER)
    context.add_os_installer_key(OS_OSX, PIP_INSTALLER)
    context.add_os_installer_key(OS_OSX, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_OSX, BREW_INSTALLER)
    context.set_os_version_type(OS_OSX, TYPE_CODENAME)

def is_port_installed():
    try:
        subprocess.Popen(['port'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return True
    except OSError:
        return False
    
def port_detect(pkgs, exec_fn=None):
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
            return [['sudo', 'port', 'install', p] for p in packages]

def is_brew_installed():
    try:
        subprocess.Popen(['brew'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return True
    except OSError:
        return False

def brew_detect(formulas, exec_fn=None):
    """ 
    Given a list of formulas, return the list of installed formulas.

    :param formulas: List of homebrew formula names
    """
    if exec_fn is None:
        exec_fn = read_stdout
    ret_list = []
    std_out = exec_fn(['brew', 'list'])
    # preserve order
    clean_formulas = []
    for f in formulas:
        clean_formulas.append(f.split('/')[-1])
    for f in std_out.split():
        if f in clean_formulas:
            ret_list.append(formulas[clean_formulas.index(f)])
    return ret_list

class HomebrewInstaller(PackageManagerInstaller):

    """An implementation of Installer for use on homebrew systems."""

    def __init__(self):
        super(HomebrewInstaller, self).__init__(brew_detect, supports_depends=True)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        if not is_brew_installed():
            raise InstallFailed((BREW_INSTALLER, 'Homebrew is not installed'))
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        packages = self.remove_duplicate_dependencies(packages)
        # interactive switch doesn't matter
        if reinstall:
            commands = []
            for p in packages:
                commands.append(['brew', 'uninstall', '--force', p])
                commands.append(['brew', 'install', p])
            return commands
        else:
            return [['brew', 'install', p] for p in packages]

    def remove_duplicate_dependencies(self, packages):
        if not is_brew_installed():
            raise InstallFailed((BREW_INSTALLER, 'Homebrew is not installed'))

        # we'll remove dependencies from this copy and return it
        packages_copy = list(packages)

        # find all dependencies for each package
        for p in packages:
            sub_command = ['brew', 'info', p]
            output = subprocess.Popen(sub_command, stdout=subprocess.PIPE).communicate()[0]
            match = re.findall("Depends on: (.*)", output)
            if match:
                dependencies = re.split(',', match[0])
                for d in dependencies:
                    d = d.strip()
                    # remove duplicate dependency from package list
                    if d in packages:
                        packages_copy.remove(d)
        return packages_copy
