# Copyright (c) 2019, Ben Wolsieffer
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

# Author Ben Wolsieffer/benwolsieffer@gmail.com
import subprocess

from rospkg.os_detect import OS_NIXOS

from ..installers import PackageManagerInstaller

NIX_INSTALLER = 'nix'


def register_installers(context):
    context.set_installer(NIX_INSTALLER, NixInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_NIXOS, NIX_INSTALLER)
    context.set_default_os_installer_key(OS_NIXOS, lambda self: NIX_INSTALLER)


def nix_detect(packages):
    # Say that all packages are installed, because Nix handles installation
    # automatically
    return packages


class NixInstaller(PackageManagerInstaller):

    def __init__(self):
        super(NixInstaller, self).__init__(nix_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        raise NotImplementedError('Nix does not support installing packages through ROS')

    def get_version_strings(self):
        return subprocess.check_output(('nix', '--version')).decode()
