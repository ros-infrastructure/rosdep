#!/usr/bin/env python

from __future__ import print_function

import subprocess

from rospkg.os_detect import OS_YOCTO_EDISON

from .pip import PIP_INSTALLER
from ..core import InstallFailed
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

def register_platforms(context):
    context.add_os_installer_key(OS_YOCTO_EDISON, PIP_INSTALLER)
