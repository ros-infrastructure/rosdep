# Copyright (c) 2011, Willow Garage, Inc.
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

"""
Script for installing rdmanifest-described resources
"""

from __future__ import print_function

import os
import sys
from optparse import OptionParser

from rosdep2 import InstallFailed
from rosdep2.platforms import source

NAME = 'rosdep-source'


def install_main():
    parser = OptionParser(usage="usage: %prog install <rdmanifest-url>", prog=NAME)
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("please specify one and only one rdmanifest url")
    if args[0] != 'install':
        parser.error("currently only support the 'install' command")
    rdmanifest_url = args[1]
    try:
        if os.path.isfile(rdmanifest_url):
            source.install_from_file(rdmanifest_url)
        else:
            source.install_from_url(rdmanifest_url)
    except InstallFailed as e:
        print("ERROR: installation failed:\n%s" % e, file=sys.stderr)
        sys.exit(1)
