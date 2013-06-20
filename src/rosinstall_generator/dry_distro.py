# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import logging
import rospkg.distro as rosdistro
import urllib
import yaml

logger = logging.getLogger('rosinstall_generator')


def get_distro(distro_name):
    return rosdistro.load_distro(rosdistro.distro_uri(distro_name))


def get_recursive_dependencies(distro, stack_names):
    dry_dependencies = set(stack_names)
    wet_dependencies = set([])
    traverse_stacks = set(stack_names)
    while traverse_stacks:
        stack_name = traverse_stacks.pop()
        info = _get_stack_info(distro, stack_name)
        if 'depends' in info:
            depends = set(info['depends'])
            for depend in depends:
                if depend in distro.stacks:
                    if depend not in dry_dependencies:
                        dry_dependencies.add(depend)
                        traverse_stacks.add(depend)
                else:
                    wet_dependencies.add(depend)
    return dry_dependencies, wet_dependencies


def _get_stack_info(distro, stack_name):
    stack = distro.stacks[stack_name]
    version = stack.version
    url = 'https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(stack_name)s-%(version)s/%(stack_name)s-%(version)s.yaml' % locals()
    logger.debug('Load dry package info from "%s"' % url)
    y = urllib.urlopen(url)
    return yaml.load(y.read())


def generate_rosinstall(distro, stack_names):
    rosinstall_data = []
    for stack_name in stack_names:
        rosinstall_data.extend(distro.stacks[stack_name].vcs_config.to_rosinstall(stack_name, branch='release-tar', anonymous=True))
    return rosinstall_data
