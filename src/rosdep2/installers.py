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

from __future__ import print_function

import os
import sys
import traceback

from collections import defaultdict
from rospkg.os_detect import OsDetect

from .core import rd_debug, RosdepInternalError, InstallFailed
from .model import InvalidRosdepData

# use OsDetect.get_version() for OS version key
TYPE_VERSION = 'version'
# use OsDetect.get_codename() for OS version key
TYPE_CODENAME = 'codename'

# kwc: InstallerContext is basically just a bunch of dictionaries with
# defined lookup methods.  It really encompasses two facets of a
# rosdep configuration: the pluggable nature of installers and
# platforms, as well as the resolution of the operating system for a
# specific machine.  It is possible to decouple those two notions,
# though there are some touch points over how this interfaces with the
# rospkg.os_detect library, i.e. how platforms can tweak these
# detectors and how the higher-level APIs can override them.
class InstallerContext(object):
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
        # platform configuration
        self.installers = {}
        self.os_installers = defaultdict(list)
        self.default_os_installer = {}

        # stores configuration of which value to use for the OS version key (version number or codename)
        self.os_version_type = {}

        # OS detection and override
        if os_detect is None:
            os_detect = OsDetect()
        self.os_detect = os_detect
        self.os_override = None

        self.verbose = False
        
    def set_verbose(self, verbose):
        self.verbose = verbose
        
    def set_os_override(self, os_name, os_version):
        """
        Override the OS detector with *os_name* and *os_version*.  See
        :meth:`InstallerContext.detect_os`.

        :param os_name: OS name value to use, ``str``
        :param os_version: OS version value to use, ``str``
        """
        if self.verbose:
            print("overriding OS to [%s:%s]"%(os_name, os_version))
        self.os_override = os_name, os_version

    def get_os_version_type(self, os_name):
        return self.os_version_type.get(os_name, TYPE_VERSION)

    def set_os_version_type(self, os_name, version_type):
        if version_type not in (TYPE_VERSION, TYPE_CODENAME):
            raise ValueError("version type not TYPE_VERSION or TYPE_CODENAME")
        self.os_version_type[os_name] = version_type
        
    def get_os_name_and_version(self):
        """
        Get the OS name and version key to use for resolution and
        installation.  This will be the detected OS name/version
        unless :meth:`InstallerContext.set_os_override()` has been
        called.

        :returns: (os_name, os_version), ``(str, str)``
        """
        if self.os_override:
            return self.os_override
        else:
            os_name = self.os_detect.get_name()
            if self.get_os_version_type(os_name) == TYPE_CODENAME:
                os_version = self.os_detect.get_codename()
            else:
                os_version = self.os_detect.get_version()
            return os_name, os_version
        
    def get_os_detect(self):
        """
        :returns os_detect: :class:`OsDetect` instance used for
          detecting platforms.
        """
        return self.os_detect

    def set_installer(self, installer_key, installer):
        """
        Set the installer to use for *installer_key*.  This will
        replace any existing installer associated with the key.
        *installer_key* should be the same key used for the
        ``rosdep.yaml`` package manager key.

        :param installer_key: key/name to associate with installer, ``str``
        :param installer: :class:`Installer` implementation, ``class``.
        :raises: :exc:`TypeError` if *installer* is not a subclass of
          :class:`Installer`
        """
        if not isinstance(installer, Installer):
            raise TypeError("installer must be a instance of Installer")
        if self.verbose:
            print("registering installer [%s]"%(installer_key))
        self.installers[installer_key] = installer
        
    def get_installer(self, installer_key):
        """
        :returns: :class:`Installer` class associated with *installer_key*.
        :raises: :exc:`KeyError`
        """
        return self.installers[installer_key]

    def get_installer_keys(self):
        """
        :returns: list of registered installer keys
        """
        return self.installers.keys()

    def get_os_keys(self):
        """
        :returns: list of OS keys that have registered with this context, ``[str]``
        """
        return self.os_installers.keys()
    
    def add_os_installer_key(self, os_key, installer_key):
        """
        Register an installer for the specified OS.  This will fail
        with a :exc:`KeyError` if no :class:`Installer` can be found
        with the associated *installer_key*.
        
        :param os_key: Key for OS
        :param installer_key: Key for installer to add to OS
        :raises: :exc:`KeyError`: if installer for *installer_key*
          is not set.
        """
        # validate, will throw KeyError
        installer_class = self.get_installer(installer_key)
        if self.verbose:
            print("add installer [%s] to OS [%s]"%(installer_key, os_key))
        self.os_installers[os_key].append(installer_key)

    def get_os_installer_keys(self, os_key):
        """
        Get list of installer keys registered for the specified OS.
        These keys can be resolved by calling
        :meth:`InstallerContext.get_installer`.
        
        :param os_key: Key for OS
        :raises: :exc:`KeyError`: if no information for OS *os_key* is registered.
        """
        return self.os_installers[os_key][:]

    def set_default_os_installer_key(self, os_key, installer_key):
        """
        Set the default OS installer to use for OS.
        :meth:`InstallerContext.add_os_installer` must have previously
        been called with the same arguments.

        :param os_key: Key for OS
        :param installer_key: Key for installer to add to OS
        :raises: :exc:`KeyError`: if installer for *installer_key*
          is not set or if OS for *os_key* has no associated installers.
        """
        if not os_key in self.os_installers:
            raise KeyError("unknown OS: %s"%(os_key))
        if not installer_key in self.os_installers[os_key]:
            raise KeyError("installer [%s] is not associated with OS [%s]. call add_os_installer_key() first"%(installer_key, os_key))

        # validate, will throw KeyError
        installer_class = self.get_installer(installer_key)
        if self.verbose:
            print("set default installer [%s] for OS [%s]"%(installer_key, os_key))
        self.default_os_installer[os_key] = installer_key

    def get_default_os_installer_key(self, os_key):
        """
        Get the default OS installer key to use for OS, or ``None`` if
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

class Installer(object):
    """
    The :class:`Installer` API is designed around opaque *resolved*
    parameters. These parameters can be any type of sequence object,
    but they must obey set arithmetic.  They should also implement
    ``__str__()`` methods so they can be pretty printed.
    """

    def is_installed(self, resolved):
        """
        :param resolved: resolved installation items
        :returns: ``True`` if all of the *resolved* items are installed on
          the local system
        """
        raise NotImplementedError("is_installed")        
        
    def get_install_command(self, resolved, interactive=True):
        """
        :param resolved: resolved installation items
        :param interactive: If `False`, disable interactive prompts,
          e.g. Pass through ``-y`` or equivalant to package manager.
        """
        raise NotImplementedError("get_package_install_command")

    def get_depends(self, rosdep_args): 
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

    def unique(self, *resolved_rules):
        """
        Combine the resolved rules into a unique list.  This
        is meant to combine the results of multiple calls to
        :meth:`PackageManagerInstaller.resolve`.

        Example::

            resolved1 = installer.resolve(args1)
            resolved2 = installer.resolve(args2)
            resolved = installer.unique(resolved1, resolved2)

        :param *resolved_rules: resolved arguments.  Resolved
          arguments must all be from this :class:`Installer` instance.
        """
        raise NotImplementedError("Base class unique")
    
class PackageManagerInstaller(Installer):
    """
    General form of a package manager :class:`Installer`
    implementation that assumes:

     - installer rosdep args spec is a list of package names stored with the key "packages"
     - a detect function exists that can return a list of packages that are installed

    Also, if *supports_depends* is set to ``True``:
    
     - installer rosdep args spec can also include dependency specification with the key "depends"
    """

    def __init__(self, detect_fn, supports_depends=False):
        """
        @param supports_depends:
        """
        self.detect_fn = detect_fn
        self.supports_depends = supports_depends

    def resolve(self, rosdep_args):
        """
        See :meth:`Installer.resolve()`
        """
        packages = None
        if type(rosdep_args) == dict:
            packages = rosdep_args.get("packages", [])
            if type(packages) == type("string"):
                packages = packages.split()
        elif type(rosdep_args) == type('str'):
            packages = rosdep_args.split(' ')
        elif type(rosdep_args) == list:
            packages = rosdep_args
        else:
            raise InvalidRosdepData("Invalid rosdep args: %s"%(rosdep_args))
        return packages

    def unique(self, *resolved_rules):
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

    def get_depends(self, rosdep_args): 
        """ 
        :returns: list of dependencies on other rosdep keys.  Only
          necessary if the package manager doesn't handle
          dependencies.
        """
        if self.supports_depends and type(rosdep_args) == dict:
            return rosdep_args_dict.get('depends', [])
        return [] # Default return empty list

class RosdepInstaller(object):

    def __init__(self, installer_context, lookup):
        self.installer_context = installer_context
        self.lookup = lookup
        
    def get_uninstalled(self, packages, verbose=False):
        """
        Get list of system dependencies that have not been installed
        as well as a list of errors from performing the resolution.
        This is a bulk API in order to provide performance
        optimizations in checking install state.

        :param packages: List of ROS package names, ``[str]]``

        :returns: (uninstalled, errors), ``({str: [opaque]}, {str: ResolutionError})``.
          Uninstalled is a dictionary with the installer_key as the key.
        :raises: :exc:`RosdepInternalError`
        """
        
        installer_context = self.installer_context

        # resolutions have been unique()d
        if verbose:
            print("resolving for packages [%s]"%(', '.join(packages)))
        resolutions, errors = self.lookup.resolve_all(packages, installer_context)
        
        # for each installer, figure out what is left to install
        uninstalled = {}
        for installer_key, resolved in resolutions.items(): #py3k
            if verbose:
                print("resolution: %s [%s]"%(installer_key, ', '.join(resolved)))
            try:
                installer = installer_context.get_installer(installer_key)
            except KeyError as e:
                rd_debug(traceback.format_exc())
                raise RosdepInternalError(e)
            try:
                uninstalled[installer_key] = installer.get_packages_to_install(resolved)
                if verbose:
                    print("uninstalled: [%s]"%(', '.join(uninstalled[installer_key])))
            except Exception as e:
                rd_debug(traceback.format_exc())
                raise RosdepInternalError(e)
        
        return uninstalled, errors
    
    def install(self, uninstalled, interactive=True, simulate=False, continue_on_error=False):
        """
        Install the uninstalled rosdeps.  This API is for the bulk
        workflow of rosdep (see example below).  For a more targeted
        install API, see :meth:`RosdepInstaller.install_resolved`.

        :param uninstalled: uninstalled value from
          :meth:`RosdepInstaller.get_uninstalled`.  Value is a
          dictionary mapping installer key to a opaque resolution
          list, ``{str: [opaque]}``
        :param interactive: (optional) If ``False``, suppress
          interactive prompts (e.g. by passing '-y' to ``apt``).
        :param simulate: (optional) If ``False`` simulate installation
          without actually executing.
        :raises: :exc:`InstallFailed` if any rosdeps fail to install
          and *continue_on_error* is ``False``.
        :raises: :exc:`MultipleInstallsFailed` If *continue_on_error*
          is set and one or more installs failed.
        :raises: :exc:`KeyError` If *uninstalled* value has invalid
          installer keys
        
        Example::

            uninstalled, errors = installer.get_uninstalled(packages)
            installer.install(uninstalled)
        """
        failures = []
        for installer_key, resolved in uninstalled.items(): #py3k:
            if verbose:
                print("processing rosdeps for installer [%s]"%(intsaller_key))
            try:
                self.install_resolved(installer_key, resolved, simulate=simulate, verbose=verbose)
            except InstallFailed as e:
                if not continue_on_error:
                    raise
                else:
                    failures.append(e)
        if failures:
            raise MultipleInstallsFailed(failures)

    def install_resolved(self, rosdep_key, installer_key, resolved, simulate=False, interactive=True, verbose=False):
        """
        Lower-level API for installing a rosdep dependency.  The
        *rosdep_key* have already been resolved to *installer_key* and
        *resolved* via :exc:`RosdepLookup` or other means.
        
        :param rosdep_key: Key of rosdep being installed (for debugging only), ``str``
        :param installer_key: Key for installer to apply to *resolved*, ``str``
        :param resolved: Opaque resolution list from :class:`RosdepLookup`.
        :param interactive: If ``True``, allow interactive prompts (default ``True``)
        :param simulate: If ``True``, don't execute installation commands, just print to screen.
        :param verbose: If ``True``, print verbose output to screen (default ``False``)
        
        :raises: :exc:`InstallFailed` if *resolved* fail to install.
        """
        installer_context = self.installer_context
        installer = installer_context.get_installer(installer_key)
        command = installer.get_install_command(resolved, interactive=interactive)
        if not command:
            if verbose:
                print("[%s] no packages to install"%(rosdep_key))
            return

        if simulate or verbose:
            print("[%s] Installation command/script:\n"%(rosdep_key)+80*'='+str(command)+80*'=')
        if not simulate:
            result = create_tempfile_from_string_and_execute(command)
            if result:
                if verbose:
                    print("successfully installed %s"%(rosdep_key))
                if not my_installer.is_installed(resolved):
                    raise InstallFailed("rosdep %s failed check-presence-script after installation.\nResolved packages were %s"%(rosdep_key, resolved))
