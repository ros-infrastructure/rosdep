# Copyright (c) 2009, Willow Garage, Inc.
# Copyright (c) 2019, Kei Okada
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

from __future__ import print_function

import os
import subprocess

from ..core import InstallFailed
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

# npm package manager key
NPM_INSTALLER = 'npm'


def register_installers(context):
    context.set_installer(NPM_INSTALLER, NpmInstaller())


def is_npm_installed():
    try:
        subprocess.Popen(['npm'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return True
    except OSError:
        return False


class NpmInstaller(PackageManagerInstaller):
    """
    :class:`Installer` support for npm.
    """

    def __init__(self):
        super(NpmInstaller, self).__init__(self.npm_detect, supports_depends=True)

    def npm_detect(self, pkgs, exec_fn=None):
        """
        Given a list of package, return the list of installed packages.

        :param exec_fn: function to execute Popen and read stdout (for testing)
        """
        if exec_fn is None:
            exec_fn = read_stdout

        # npm list -parseable returns [dir, dir/node_modules/path, dir/node_modules/path, ...]
        if self.as_root:
            cmd = ['npm', 'list', '-g']
        else:
            cmd = ['npm', 'list']
        pkg_list = exec_fn(cmd + ['-parseable']).split('\n')

        ret_list = []
        for pkg in pkg_list[1:]:
            pkg_row = pkg.split('/')
            if pkg_row[-1] in pkgs:
                ret_list.append(pkg_row[-1])
        return ret_list

    def get_version_strings(self):
        npm_version = subprocess.check_output(['npm', '--version']).strip().decode()
        return ['npm {}'.format(npm_version)]

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        if not is_npm_installed():
            raise InstallFailed((NPM_INSTALLER, 'npm is not installed'))
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        if self.as_root:
            cmd = ['npm', 'install', '-g']
        else:
            cmd = ['npm', 'install']

        return [self.elevate_priv(cmd + [p]) for p in packages]
