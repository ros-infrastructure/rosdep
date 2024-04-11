# Copyright 2018 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

import os
import subprocess
import sys

import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    # flake8 doesn't have a stable public API as of ver 6.1.0.
    # See: https://flake8.pycqa.org/en/latest/user/python-api.html
    # Calling through subprocess is the most stable way to run it.

    # We still need to support Python 2.7, so we can't use run()
    ret_code = subprocess.call(
        [sys.executable, "-m", "flake8"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    assert 0 == ret_code, "flake8 found violations"
