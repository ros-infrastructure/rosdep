# Copyright (c) 2010, Willow Garage, Inc.
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

# Original from cygwin.py by Tingfan Wu tingfan@gmail.com
# Modified for FreeBSD by Rene Ladan rene@freebsd.org
# Updated for FreeBSD with pkg by Trenton Schulz trentonw@ifi.uio.no

from rospkg.os_detect import OS_FREEBSD

from .pip import PIP_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

PKG_INSTALLER = 'pkg'


def register_installers(context):
    context.set_installer(PKG_INSTALLER, PkgInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_FREEBSD, PKG_INSTALLER)
    context.add_os_installer_key(OS_FREEBSD, PIP_INSTALLER)
    context.set_default_os_installer_key(OS_FREEBSD, lambda self: PKG_INSTALLER)


def pkg_detect_single(p, exec_fn):
    if p == "builtin":
        return True

    cmd = ['/usr/sbin/pkg', 'query', '%n', p]
    std_out = exec_fn(cmd)
    return std_out.split() != []


def pkg_detect(packages, exec_fn=None):
    if exec_fn is None:
        exec_fn = read_stdout
    return [p for p in packages if pkg_detect_single(p, exec_fn)]


class PkgInstaller(PackageManagerInstaller):
    """
    An implementation of the Installer for use on FreeBSD-style
    systems.
    """

    def __init__(self):
        super(PkgInstaller, self).__init__(pkg_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        else:
            return [self.elevate_priv(['/usr/sbin/pkg', 'install', '-y']) + packages]
