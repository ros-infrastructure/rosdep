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

# Author Nikolay Nikolov/niko.b.nikolov@gmail.com

import subprocess
import os

from ..core import InstallFailed
from .pip import PIP_INSTALLER
from ..installers import PackageManagerInstaller
from .source import SOURCE_INSTALLER
from ..shell_utils import read_stdout

SLACKWARE_OS_NAME = 'slackware'
SBOTOOLS_INSTALLER = 'sbotools'
SLACKPKG_INSTALLER = 'slackpkg'


def register_installers(context):
    context.set_installer(SBOTOOLS_INSTALLER, SbotoolsInstaller())
    context.set_installer(SLACKPKG_INSTALLER, SlackpkgInstaller())


def register_platforms(context):
    context.add_os_installer_key(SLACKWARE_OS_NAME, SBOTOOLS_INSTALLER)
    context.add_os_installer_key(SLACKWARE_OS_NAME, PIP_INSTALLER)
    context.add_os_installer_key(SLACKWARE_OS_NAME, SOURCE_INSTALLER)
    context.add_os_installer_key(SLACKWARE_OS_NAME, SLACKPKG_INSTALLER)
    context.set_default_os_installer_key(SLACKWARE_OS_NAME, lambda self: SBOTOOLS_INSTALLER)


def sbotools_available():
    if not os.path.exists('/usr/sbin/sboinstall'):
        return False
    return True


def sbotools_detect_single(p):
    pkg_list = read_stdout(['ls', '/var/log/packages'])
    p = subprocess.Popen(['grep', '-i', '^' + p], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate(pkg_list)
    return not p.returncode


def sbotools_detect(packages):
    return [p for p in packages if sbotools_detect_single(p)]


class SbotoolsInstaller(PackageManagerInstaller):

    def __init__(self):
        super(SbotoolsInstaller, self).__init__(sbotools_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        if not sbotools_available():
            raise InstallFailed((SBOTOOLS_INSTALLER, 'sbotools is not installed'))

        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []

        cmd = ['sboinstall']

        return [self.elevate_priv(cmd + [p] + ['-j']) for p in packages]


def slackpkg_available():
    if not os.path.exists('/usr/sbin/slackpkg'):
        return False
    return True


def slackpkg_detect_single(p):
    return not subprocess.call(['slackpkg', 'search', p], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def slackpkg_detect(packages):
    return [p for p in packages if slackpkg_detect_single(p)]


class SlackpkgInstaller(PackageManagerInstaller):

    def __init__(self):
        super(SlackpkgInstaller, self).__init__(slackpkg_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        # slackpkg does not provide non-interactive mode
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        else:
            return [self.elevate_priv(['slackpkg', 'install', p]) for p in packages]
