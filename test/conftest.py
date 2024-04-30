# Copyright 2024 Open Source Robotics Foundation, Inc.
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

import functools
import os

try:
    from urllib.parse import urljoin
    from urllib.request import pathname2url
except ImportError:
    from urlparse import urljoin
    from urllib import pathname2url

import pytest


def path_to_url(path):
    return urljoin('file:', pathname2url(path))


def _restore_env_vars(old_vars):
    for k, v in old_vars.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def fake_sources_list_d(tmpdir):
    sources_list_d = str(tmpdir)

    fake_rosdep_dir = os.path.join(os.path.dirname(__file__), 'fake_rosdistro', 'rosdep')
    default_sources_list = os.path.join(sources_list_d, '20-default.list')
    f = open(default_sources_list, 'w')
    f.write('\n'.join([
        'yaml ' + path_to_url(os.path.join(fake_rosdep_dir, 'base.yaml')),
        'yaml ' + path_to_url(os.path.join(fake_rosdep_dir, 'python.yaml')),
    ]))
    f.close()

    return sources_list_d


@pytest.fixture
def fake_rosdep_source(fake_sources_list_d, request):
    restore_env_vars = {
        'ROSDEP_SOURCE_PATH': os.environ.get('ROSDEP_SOURCE_PATH'),
    }
    request.addfinalizer(functools.partial(_restore_env_vars, restore_env_vars))
    rosdep_source = fake_sources_list_d
    os.environ['ROSDEP_SOURCE_PATH'] = rosdep_source
    return rosdep_source


@pytest.fixture
def fake_ros_home(tmpdir, request):
    ros_home = str(tmpdir)
    restore_env_vars = {
        'ROS_HOME': os.environ.get('ROS_HOME'),
    }
    request.addfinalizer(functools.partial(_restore_env_vars, restore_env_vars))
    os.environ['ROS_HOME'] = ros_home
    return ros_home


@pytest.fixture
def fake_rosdistro_index(request):
    restore_env_vars = {
        'ROSDISTRO_INDEX_URL': os.environ.get('ROSDISTRO_INDEX_URL'),
    }
    request.addfinalizer(functools.partial(_restore_env_vars, restore_env_vars))
    rosdistro_index_url = path_to_url(
        os.path.join(os.path.dirname(__file__), 'fake_rosdistro', 'index-v4.yaml'))
    os.environ['ROSDISTRO_INDEX_URL'] = rosdistro_index_url
    return rosdistro_index_url


@pytest.fixture
def fake_rosdep(fake_ros_home, fake_rosdep_source, fake_rosdistro_index):
    from rosdep2.sources_list import update_sources_list
    assert update_sources_list()
