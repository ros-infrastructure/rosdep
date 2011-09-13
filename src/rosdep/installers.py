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

# InstallerContext: This class is basically just a bunch of
# dictionaries with defined lookup methods
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
        :raises: :exc:`KeyError`: if installer for *installer_mode_key*
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
        :raises: :exc:`KeyError`: if no information for OS *os_key* is registered.
        """
        return self.os_installers[os_key][:]

    def set_default_os_installer(self, os_key, installer_mode_key):
        """
        Set the default OS installer to use for OS.

        :param os_key: Key for OS
        :param installer_mode_key: Key for installer to add to OS
        :raises: :exc:`KeyError`: if installer for *installer_mode_key*
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
        :raises: :exc:`KeyError`: if no information for OS *os_key* is registered.
        """
        if not os_key in self.os_installers:
            raise KeyError("unknown OS: %s"%(os_key))
        try:
            return self.default_os_installer[os_key]
        except KeyError:
            return None

class Installer:

    def is_installed(self, resolved):
        """
        :param resolved: resolved installation items
        :returns: True if all of the *resolved* items are installed on
          the local system
        """
        raise NotImplementedError("is_installed")        
        
    def get_install_command(self, interactive=True):
        """
        :param interactive: If `False`, disable interactive prompts,
          e.g. Pass through ``-y`` or equivalant to package manager.
        """
        raise NotImplementedError("get_package_install_command")

    def get_depends(self, rosdep_args_dict): 
        """ 
        :returns: list of dependencies on other rosdep keys.  Only
          necessary if the package manager doesn't handle
          dependencies.
        """
        return [] # Default return empty list

    def resolve(self, rosdep_args_dict):
        """
        :param rosdep_args_dict: argument dictionary to the rosdep rule for this package manager
        """
        raise NotImplementedError("Base class resolve")

    def unique(self, resolved_rules):
        """
        Combine the list of resolved rules into a unique list.  This
        is meant to combine the results of multiple calls to
        :meth:`PackageManagerInstaller.resolve`.

        Example::

            resolved1 = installer.resolve(args1)
            resolved2 = installer.resolve(args2)
            resolved = installer.unique([resolved1, resolved2])

        :param resolved_rules: list of resolved arguments.  Resolved
          arguments must all be from this :class:`Installer` instance.
        """
        raise NotImplementedError("Base class unique")
    
class PackageManagerInstaller(Installer):
    """
    General form of a package manager :class:`Installer`
    implementation that assumes:

     - installer rosdep args spec is a list of package names stored with the key "packages"
     - a function exists that can return a list of packages that are installed
    """

    def __init__(self, detect_fn):
        self.detect_fn = detect_fn

    def resolve(self, rosdep_args_dict):
        """
        See :meth:`Installer.resolve()`
        """
        packages = rosdep_args_dict.get("packages", [])
        if type(packages) == type("string"):
            packages = packages.split()
        #TODOXXX: return type needs to be wrapped so it can be recombined/printed, etc...
        return packages

    def unique(self, resolved_rules):
        """
        See :meth:`Installer.unique()`
        """
        s = set()
        for resolved in resolved_rules:
            s.update(resolved)
        return sorted(list(s))
        
    def get_packages_to_install(self, resolved):
        return list(set(resolved) - set(self.detect_fn(resolved)))

    def is_installed(self, resolved):
        return not self.get_packages_to_install(resolved)

    def get_install_command(self, resolved, interactive=True):
        raise NotImplementedError('subclasses must implement')
