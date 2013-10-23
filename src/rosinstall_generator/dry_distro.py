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
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError
import yaml

from rosdistro.loader import load_url

logger = logging.getLogger('rosinstall_generator.dry')


def get_distro(distro_name):
    return rosdistro.load_distro(rosdistro.distro_uri(distro_name))


def get_stack_names(distro):
    released_names = []
    unreleased_names = []
    for stack_name, stack in distro.stacks.items():
        if stack.version:
            released_names.append(stack_name)
        else:
            unreleased_names.append(stack_name)
    return released_names, unreleased_names


def get_recursive_dependencies(distro, stack_names, excludes=None):
    excludes = set(excludes or [])
    dry_dependencies = set(stack_names)
    wet_dependencies = set([])
    traverse_stacks = set(stack_names)
    while traverse_stacks:
        stack_name = traverse_stacks.pop()
        info = _get_stack_info(distro, stack_name)
        if 'depends' in info:
            for depend in info['depends']:
                if depend in excludes:
                    continue
                if depend in distro.stacks:
                    if depend not in dry_dependencies:
                        dry_dependencies.add(depend)
                        traverse_stacks.add(depend)
                else:
                    wet_dependencies.add(depend)
    return dry_dependencies, wet_dependencies


def get_recursive_dependencies_on(distro, stack_names, excludes=None, limit=None):
    excludes = set(excludes or [])
    limit = set(limit or [])

    # to improve performance limit search space if possible
    if limit:
        released_names, _ = get_stack_names(distro)
        excludes.update(set(released_names) - limit - set(stack_names))

    depends_on = set([])
    stacks_to_check = set(stack_names)
    while stacks_to_check:
        next_stack_to_check = stacks_to_check.pop()
        deps = _get_dependencies_on(distro, next_stack_to_check, ignore_stacks=excludes)
        new_deps = deps - depends_on
        stacks_to_check |= new_deps
        depends_on |= new_deps
    return depends_on


def _get_dependencies_on(distro, stack_name, ignore_stacks=None):
    ignore_stacks = ignore_stacks or []
    depends_on = set([])
    for name, stack in distro.stacks.items():
        if name in ignore_stacks or not stack.version:
            continue
        info = _get_stack_info(distro, name)
        if 'depends' in info:
            if stack_name in info['depends']:
                depends_on.add(name)
    return depends_on


_stack_info = {}


def _get_stack_info(distro, stack_name):
    global _stack_info
    if stack_name not in _stack_info:
        stack = distro.stacks[stack_name]
        version = stack.version
        url = 'http://ros-dry-releases.googlecode.com/svn/download/stacks/%(stack_name)s/%(stack_name)s-%(version)s/%(stack_name)s-%(version)s.yaml' % locals()
        logger.debug('Load dry package info from "%s"' % url)
        try:
            data = load_url(url)
        except URLError as e:
            raise RuntimeError("Could not fetch information for stack '%s' with version '%s': %s" % (stack_name, version, e))
        _stack_info[stack_name] = yaml.load(data)
    return _stack_info[stack_name]


def generate_rosinstall(distro, stack_names):
    rosinstall_data = []
    for stack_name in stack_names:
        rosinstall_data.extend(distro.stacks[stack_name].vcs_config.to_rosinstall(stack_name, branch='release-tar', anonymous=True))
    return rosinstall_data
