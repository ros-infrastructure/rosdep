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

# Author Tully Foote/tfoote@willowgarage.com, Ken Conley/kwc@willowgarage.com

import os
import sys

SOURCE_INSTALLER='source'

class RosdepContext:
    """
    RosdepContext manages the context of execution for rosdep as it
    relates to the installers, OS detectors, and other extensible
    APIs.
    """
    
    def __init__(self, os_detect):
        self.os_detect = os_detect
        self.installers = {}
        
    def register_installer(self, installer_key, installer):
        assert installer_key not in self.installers, "cannot register same installer multiple times"
        self.installers[installer_key] = installer
        
    def get_installer(self, installer_key):
        """
        @raise: KeyError
        """
        return self.installers[installer_key]

    def set_default_os_installer(self, os_key, installer_mode_key, installer_class=None):
        """
        Set the default OS installer to use for OS.
        """
        if installer_class is None:
            installer_class = get_installer(installer_mode_key)
        self.register_os_installer(os_key, 'default', installer_class)

    def register_os_installer(self, os_key, installer_mode_key, installer_class=None):
        """
        @param installer_class: (optional) specify installer class to
        use.  If None specified, will use the default installer class
        associated with installer_mode_key.

        @raise KeyError: if installer for installer_mode_key cannot be
        found.
        """
        if installer_class is None:
            installer_class = get_installer(installer_mode_key)
        raise NotImplemented

class OsInstallers:
    """
    Stores list of installers associated with OSes.
    """

    def __init__(self):
        self._installers = {}

    def add_installer(self, key, installer):
        self._installers[key] = installer
        
    def get_installer(self, mode='default'):
        """
        @param mode: installer key. e.g. 'default', 'apt', 'pip'.  The
        correct set of values is platform-dependent.
        @type  mode: str
        @return the correct installer for a given OS. from the
        self.installer dict.
        @raise KeyError: if requested installer not available
        """
        return self._installers[mode]

class Installer:

    def __init__(self, arg_dict):
        """
        Set all required fields here 
        """
        raise NotImplementedError("Base class __init__")
    
    def check_presence(self):
        """
        This script will return true if the rosdep is found on the
        system, otherwise false.
        """
        raise NotImplementedError("Base class check_presence")

    def generate_package_install_command(self, default_yes, execute = True, display = True):
        """
        If execute is True, install the rosdep, else if display = True
        print the script it would have run to install.
        @param default_yes  Pass through -y or equivilant to package manager
        """
        raise NotImplementedError("Base class generate_package_install_command")

    def get_depends(self): 
        """ 
        Return the dependencies, only necessary if the package manager
        doesn't handle the dependencies.
        """
        return [] # Default return empty list


class PackageManagerInstaller(Installer):
    """
    General form of a package manager installer implementation that assumes:

     - installer spec is a list of package names
     - a function exists that can return a list of packages that are installed
    """
    def __init__(self, packages, detect_fn):
        self.packages = packages
        self.detect_fn = detect_fn

    def get_packages_to_install(self):
        return list(set(self.packages) - set(self.detect_fn(self.packages)))

    def check_presence(self):
        return len(self.get_packages_to_install()) == 0

    def generate_package_install_command(self, default_yes = False, execute = True, display = True):
        raise NotImplementedError('subclasses must implement')
