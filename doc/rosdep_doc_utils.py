# Copyright 2016 Open Source Robotics Foundation, Inc.
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

from docutils import nodes
from docutils.parsers.rst import Directive
import re
import subprocess
import sys

from rosdep2.main import _usage


class RosdepCLIDirective(Directive):
    required_arguments = 1

    def run(self):
        if 'commands' in self.arguments:
            return [nodes.literal_block(text=_usage)]
        capitalized_usage = _usage[0].upper() + _usage[1:] + '\n'
        escaped_capitalized_usage = re.escape(capitalized_usage)
        py = sys.executable
        if 'options' in self.arguments:
            out = subprocess.check_output(
                [py, '-c', "from rosdep2.main import rosdep_main;rosdep_main(['-h'])"]
            )
            return [
                nodes.literal_block(text=re.sub(escaped_capitalized_usage, '', out.decode()))
            ]
        if 'install' in self.arguments:
            out = subprocess.check_output(
                [py, '-c', "from rosdep2.main import rosdep_main;rosdep_main(['install', '-h'])"]
            )
            return [
                nodes.literal_block(text=re.sub(escaped_capitalized_usage, '', out.decode()))
            ]


def setup(app):
    app.add_directive('rosdep_cli_help', RosdepCLIDirective)
