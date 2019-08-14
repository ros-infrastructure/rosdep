# Copyright 2017 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from .resources import get_resource
from .resources import get_resources
from .search_paths import get_search_paths


class PackageNotFoundError(KeyError):
    pass


def get_packages_with_prefixes():
    """
    Return a dict of package names to the prefixes in which they are found.

    :returns: dict of package names to their prefixes
    :rtype: dict
    """
    return get_resources('packages')


def get_package_prefix(package_name):
    """
    Return the installation prefix directory of the given package.

    For example, if you install the package 'foo' into
    '/home/user/ros2_ws/install' and you called this function with 'foo' as the
    argument, then it will return that directory.

    :param str package_name: name of the package to locate
    :returns: installation prefix of the package
    :raises: :exc:`PackageNotFoundError` if the package is not found
    """
    try:
        content, package_prefix = get_resource('packages', package_name)
    except LookupError:
        raise PackageNotFoundError(
            "package '{}' not found, searching: {}".format(package_name, get_search_paths()))
    return package_prefix


def get_package_share_directory(package_name):
    """
    Return the share directory of the given package.

    For example, if you install the package 'foo' into
    '/home/user/ros2_ws/install' and you called this function with 'foo' as the
    argument, then it will return '/home/user/ros2_ws/install/share/foo' as
    the package's share directory.

    :param str package_name: name of the package to locate
    :returns: share directory of the package
    :raises: :exc:`PackageNotFoundError` if the package is not found
    """
    return os.path.join(get_package_prefix(package_name), 'share', package_name)
