# Copyright 2015 Open Source Robotics Foundation, Inc.
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

from .constants import RESOURCE_INDEX_SUBFOLDER

from .search_paths import get_search_paths


def get_resource(resource_type, resource_name):
    """
    Get the content of a specific resource and its prefix path.

    :param resource_type: the type of the resource
    :type resource_type: str
    :param resource_names: the name of the resource
    :type resource_name: str
    :returns: a tuple of the content (bytes) of the resource and its prefix path
    :raises: :exc:`EnvironmentError`
    :raises: :exc:`OSError`
    :raises: :exc:`LookupError`
    """
    assert resource_type, 'The resource type must not be empty'
    assert resource_name, 'The resource name must not be empty'
    for path in get_search_paths():
        resource_path = os.path.join(path, RESOURCE_INDEX_SUBFOLDER, resource_type, resource_name)
        if os.path.isfile(resource_path):
            try:
                with open(resource_path, 'r') as h:
                    content = h.read()
            except OSError as e:
                raise OSError(
                    "Could not open the resource '%s' of type '%s':\n%s"
                    % (resource_name, resource_type, e))
            return content, path
    raise LookupError(
        "Could not find the resource '%s' of type '%s'" % (resource_name, resource_type))


def get_resources(resource_type):
    """
    Get the resource names of all resources of the specified type.

    :param resource_type: the type of the resource
    :type resource_type: str
    :returns: dict of resource names to the prefix path they are in
    :raises: :exc:`EnvironmentError`
    """
    assert resource_type, 'The resource type must not be empty'
    resources = {}
    for path in get_search_paths():
        resource_path = os.path.join(path, RESOURCE_INDEX_SUBFOLDER, resource_type)
        if os.path.isdir(resource_path):
            for resource in os.listdir(resource_path):
                # Ignore subdirectories, and anything starting with a dot
                if os.path.isdir(os.path.join(resource_path, resource)) \
                        or resource.startswith('.'):
                    continue
                if resource not in resources:
                    resources[resource] = path
    return resources


def has_resource(resource_type, resource_name):
    """
    Check if a specific resource exists.

    :param resource_type: the type of the resource
    :type resource_type: str
    :param resource_names: the name of the resource
    :type resource_name: str
    :returns: The prefix path if the resource exists, False otherwise
    :raises: :exc:`EnvironmentError`
    """
    assert resource_type, 'The resource type must not be empty'
    assert resource_name, 'The resource name must not be empty'
    for path in get_search_paths():
        resource_path = os.path.join(path, RESOURCE_INDEX_SUBFOLDER, resource_type, resource_name)
        if os.path.isfile(resource_path):
            return path
    return False
