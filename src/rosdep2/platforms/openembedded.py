# Copyright (c) 2019, LG Electronics, Inc.
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

# Author Andre Rosa/andre.rosa@lge.com

import subprocess
from rospkg.os_detect import OS_OPENEMBEDDED, OsDetect
from ..installers import PackageManagerInstaller
OPKG_INSTALLER = 'opkg'


def register_installers(context):
    context.set_installer(OPKG_INSTALLER, OpkgInstaller())


def register_platforms(context):
    register_oe(context)


def register_oe(context):
    context.add_os_installer_key(OS_OPENEMBEDDED, OPKG_INSTALLER)
    context.set_default_os_installer_key(OS_OPENEMBEDDED, lambda self: OPKG_INSTALLER)
    context.set_os_version_type(OS_OPENEMBEDDED, OsDetect.get_codename)


def opkg_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.
    NOTE: These are stubs currently and will be filled after semantics are fully defined.

    :param pkgs: list of package names, optionally followed by a fixed version (`foo=3.0`)
    :param exec_fn: function to execute Popen and read stdout (for testing)
    :return: list elements in *pkgs* that were found installed on the system
    """
    raise NotImplementedError("opkg_detect is not implemented yet")


class OpkgInstaller(PackageManagerInstaller):
    """
    An implementation of the Installer for use on oe systems.
    NOTE: These are stubs currently and will be filled after semantics are fully defined.
    """

    def __init__(self):
        super(OpkgInstaller, self).__init__(opkg_detect)

    def get_version_strings(self):
        output = subprocess.check_output(['opkg', '--version'])
        version = output.splitlines()[0].split(b' ')[2].decode()
        return [('opkg {}').format(version)]

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        raise NotImplementedError('get_install_command is not implemented yet')
