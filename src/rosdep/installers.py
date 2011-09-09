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

from collections import defaultdict
from rospkg.os_detect import OsDetect

# This class is basically just a bunch of dictionaries with defined lookup methods

class InstallerContext:
    """
    :class:`InstallerContext` manages the context of execution for rosdep as it
    relates to the installers, OS detectors, and other extensible
    APIs.
    """
    
    def __init__(self, os_detect=None):
        """
        :param os_detect: (optional)
        :class:`rospkg.os_detect.OsDetect` instance to use for
        detecting platforms.  If `None`, default instance will be
        used.
        """
        if os_detect is None:
            os_detect = OsDetect()
        self.os_detect = os_detect
        self.installers = defaultdict(list)
        self.default_os_installer = {}
        
    def get_os_detect(self):
        """
        :returns os_detect: :class:`OsDetect` instance to use for detecting platforms.
        """
        return self.os_detect

    def set_installer(self, installer_key, installer):
        assert installer_key not in self.installers, "cannot set same installer multiple times"
        self.installers[installer_key] = installer
        
    def get_installer(self, installer_key):
        """
        :raises: :exc:`KeyError`
        """
        return self.installers[installer_key]

    def get_installer_keys(self):
        """
        :returns: list of registered installer keys
        """
        return self.installers.keys()

    def add_os_installer(self, os_key, installer_mode_key):
        """
        Register an installer for the specified OS.  This will fail
        with a :exc:`KeyError` if no :class:`Installer` can be found
        with the associated *installer_mode_key*.
        
        :param os_key: Key for OS
        :param installer_mode_key: Key for installer to add to OS
        :raises: :exc`KeyError`: if installer for *installer_mode_key*
        is not set.
        """
        # validate, will throw KeyError
        installer_class = self.get_installer(installer_mode_key)
        self.os_installers[os_key].append(installer_mode_key)

    def get_os_installer_keys(self, os_key):
        """
        Get list of installer keys registered for the specified OS.
        These keys can be resolved by calling
        :meth:`InstallerContext.get_installer`.
        
        :param os_key: Key for OS
        :raises: :exc`KeyError`: if no information for OS *os_key* is registered.
        """
        return self.os_installers[os_key][:]

    def set_default_os_installer(self, os_key, installer_mode_key):
        """
        Set the default OS installer to use for OS.

        :param os_key: Key for OS
        :param installer_mode_key: Key for installer to add to OS
        :raises: :exc`KeyError`: if installer for *installer_mode_key*
        is not set.
        """
        # validate, will throw KeyError
        installer_class = self.get_installer(installer_mode_key)
        self.default_os_installer[os_key] = installer_mode_key

    def get_default_os_installer_key(self, os_key):
        """
        Get the default OS installer key to use for OS, or `None` if
        there is no default.

        :param os_key: Key for OS
        :returns: :class:`Installer`
        :raises: :exc`KeyError`: if no information for OS *os_key* is registered.
        """
        if not os_key in self.os_installers:
            raise KeyError("unknown OS: %s"%(os_key))
        try:
            return self.default_os_installer[os_key]
        except KeyError:
            return None

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

        :param default_yes:  Pass through ``-y`` or equivalant to package manager
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
