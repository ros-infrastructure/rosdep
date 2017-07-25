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

# Author Tully Foote, Ken Conley

from __future__ import print_function
import subprocess
import sys
import re

from rospkg.os_detect import OS_DEBIAN, OS_LINARO, OS_UBUNTU, OS_ELEMENTARY, OsDetect

from .pip import PIP_INSTALLER
from .gem import GEM_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

# apt package manager key
APT_INSTALLER='apt'


def register_installers(context):
    context.set_installer(APT_INSTALLER, AptInstaller())

def register_platforms(context):
    register_debian(context)
    register_linaro(context)
    register_ubuntu(context)
    register_elementary(context)
    
def register_debian(context):
    context.add_os_installer_key(OS_DEBIAN, APT_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, PIP_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, GEM_INSTALLER)
    context.add_os_installer_key(OS_DEBIAN, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_DEBIAN, lambda self: APT_INSTALLER)
    context.set_os_version_type(OS_DEBIAN, OsDetect.get_codename)
    
def register_linaro(context):
    # Linaro is an alias for Ubuntu. If linaro is detected and it's not set as an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_LINARO and not context.os_override:
        print("rosdep detected OS: [%s] aliasing it to: [%s]" % (OS_LINARO, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())

def register_elementary(context):
    # Elementary is an alias for Ubuntu. If elementary is detected and it's not set as an override force ubuntu.
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_ELEMENTARY and not context.os_override:
        print("rosdep detected OS: [%s] aliasing it to: [%s]" % (OS_ELEMENTARY, OS_UBUNTU), file=sys.stderr)
        context.set_os_override(OS_UBUNTU, context.os_detect.get_codename())

def register_ubuntu(context):
    context.add_os_installer_key(OS_UBUNTU, APT_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, PIP_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, GEM_INSTALLER)
    context.add_os_installer_key(OS_UBUNTU, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_UBUNTU, lambda self: APT_INSTALLER)
    context.set_os_version_type(OS_UBUNTU, OsDetect.get_codename)

def get_apt_cache():
    import apt
    return apt.Cache()

class AptInstaller(PackageManagerInstaller):
    """
    An implementation of the Installer for use on debian style
    systems.
    """
    def __init__(self):
        super(AptInstaller, self).__init__(self.apt_detect)

    def is_pkg_installed(self, name, version='', cache=None):
        """
        Given a package name and an option version, return if package is installed.

        :param name: package name
        :param version (optional): package version, e.g. 1.0.0
        :return: True if package is installed
        """
        if cache is None:
            cache = get_apt_cache()

        try:
            # check if package is known, package is installed and package version matches
            if cache[name].installed.version.startswith(version):
                return True
        except:
            if cache.is_virtual_package(name):
                for p in cache.get_providing_packages(name):
                    if self.is_pkg_installed(p.name, version, cache):
                        return True
        return False

    def apt_detect(self, pkgs):
        """
        Given a list of package, return the list of installed packages.

        :param pkgs: list of package names, optionally followed by a fixed version (`foo=3.0`)
        :return: list elements in *pkgs* that were found installed on the system
        """
        installed_packages = []
        cache = get_apt_cache()

        for p in pkgs:
            parts = p.split('=')
            name = parts[0]
            version = parts[1] if len(parts) > 1 else ''
            if self.is_pkg_installed(name, version, cache):
                installed_packages.append(p)

        return installed_packages


    def get_version_strings(self):
        output = subprocess.check_output(['apt-get', '--version'])
        version = output.splitlines()[0].split(' ')[1]
        return ['apt-get {}'.format(version)]

    def _get_install_commands_for_package(self, base_cmd, package, reinstall, cache):
        def pkg_command(p):
            return self.elevate_priv(base_cmd + [p])

        if cache.is_virtual_package(package):
            providers = [p.name for p in cache.get_providing_packages(package)]
            if reinstall:
                for p in providers:
                    if self.is_pkg_installed(p):
                        return pkg_command(p)
            return [pkg_command(p) for p in providers]

        return pkg_command(package)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        cache = get_apt_cache()

        if not packages:
            return []
        if not interactive and quiet:
            base_cmd = ['apt-get', 'install', '-y', '-qq']
        elif quiet:
            base_cmd = ['apt-get', 'install', '-qq']
        if not interactive:
            base_cmd = ['apt-get', 'install', '-y']
        else:
            base_cmd = ['apt-get', 'install']
        return [self._get_install_commands_for_package(base_cmd, p, reinstall, cache) for p in packages]
