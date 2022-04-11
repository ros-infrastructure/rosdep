# Copyright (c) 2018, SEQSENSE, Inc.
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

# Author Atsushi Watanabe/atsushi.w@ieee.org

import os

from rospkg.os_detect import OS_ALPINE

from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

APK_INSTALLER = 'apk'


def register_installers(context):
    context.set_installer(APK_INSTALLER, ApkInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_ALPINE, APK_INSTALLER)
    context.add_os_installer_key(OS_ALPINE, PIP_INSTALLER)
    context.add_os_installer_key(OS_ALPINE, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_ALPINE, lambda self: APK_INSTALLER)
    context.set_os_version_type(OS_ALPINE, lambda self: ".".join(self.get_version().split('.')[:2]))


def apk_detect(pkgs, exec_fn=read_stdout):
    """
    Given a list of packages, return a list of which are already installed.

    :param exec_fn: function to execute Popen and read stdout (for testing)
    """

    if not pkgs:
        return []

    # Get installed package names:
    cmd_installed = ['apk', 'info', '--installed']
    cmd_installed.extend(pkgs)
    origin_packages = exec_fn(cmd_installed).splitlines()

    # Resolve alias names of replaced packages.
    cmd_replaces = ['apk', 'info', '--installed', '--replaces']
    cmd_replaces.extend(pkgs)
    # This command will respond like:
    #
    #    $ apk info --installed --replaces boost-atomic boost-filesystem
    #    boost1.76-atomic-1.76.0-r0 replaces:
    #    boost-atomic
    #
    #    boost1.76-filesystem-1.76.0-r0 replaces:
    #    boost-filesystem
    #
    #    $
    replaced_packages = []
    reading = False
    for line in exec_fn(cmd_replaces).splitlines():
        if line.endswith(' replaces:'):
            reading = True
        elif line == '':
            reading = False
        elif reading:
            replaced_packages.append(line.strip())

    return origin_packages + replaced_packages


class ApkInstaller(PackageManagerInstaller):

    def __init__(self):
        super(ApkInstaller, self).__init__(apk_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        pkgs = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not pkgs:
            return []

        cmd = self.elevate_priv(['apk', 'add'])

        if interactive:
            cmd.append('--interactive')
        if quiet:
            cmd.append('--quiet')

        cmd.extend(pkgs)

        return [cmd]
