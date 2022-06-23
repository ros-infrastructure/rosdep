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

# Author Tully Foote/tfoote@willowgarage.com

from __future__ import print_function
import subprocess
import sys

from rospkg.os_detect import OS_ARCH, OS_MANJARO

from ..installers import PackageManagerInstaller
from .source import SOURCE_INSTALLER
from .pip import PIP_INSTALLER

PACMAN_INSTALLER = 'pacman'


def register_installers(context):
    context.set_installer(PACMAN_INSTALLER, PacmanInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_ARCH, SOURCE_INSTALLER)
    context.add_os_installer_key(OS_ARCH, PACMAN_INSTALLER)
    context.add_os_installer_key(OS_ARCH, PIP_INSTALLER)
    context.set_default_os_installer_key(OS_ARCH, lambda self: PACMAN_INSTALLER)

    register_manjaro(context)


def register_manjaro(context):
    # Manjaro uses the same packages as Arch Linux. Override to Arch if detected
    (os_name, os_version) = context.get_os_name_and_version()
    if os_name == OS_MANJARO and not context.os_override:
        print('rosdep detected OS: [%s] aliasing it to: [%s]' %
              (OS_MANJARO, OS_ARCH), file=sys.stderr)
        context.set_os_override(OS_ARCH, context.os_detect.get_codename())


def pacman_detect_single(p):
    return not subprocess.call(['pacman', '-T', p], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def pacman_detect(packages):
    return [p for p in packages if pacman_detect_single(p)]


class PacmanInstaller(PackageManagerInstaller):

    def __init__(self):
        super(PacmanInstaller, self).__init__(pacman_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []

        command = ['pacman', '-S']

        if not interactive:
            command.append('--noconfirm')
        if not reinstall:
            command.append('--needed')
        if quiet:
            command.append('-q')

        return [self.elevate_priv(command + packages)]
