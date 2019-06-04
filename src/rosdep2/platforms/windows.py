# Copyright 2019 Open Source Robotics Foundation, Inc.
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

from rospkg.os_detect import OS_WINDOWS, OsDetect

from .pip import PIP_INSTALLER


def register_installers(context):
    pass


def register_platforms(context):
    context.add_os_installer_key(OS_WINDOWS, PIP_INSTALLER)
    context.set_default_os_installer_key(OS_WINDOWS, lambda self: PIP_INSTALLER)
    context.set_os_version_type(OS_WINDOWS, OsDetect.get_codename)
