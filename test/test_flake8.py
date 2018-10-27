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
import sys

from flake8.api.legacy import get_style_guide


def test_flake8():
    style_guide = get_style_guide(
        exclude=['conf.py'],
        ignore=[
            'C402',  # ignore presence of unnecessary generators
            'C405',  # ignore presence of unnecessary literals
            'C407',  # ignore presence of unnecessary comprehensions
            'C408',  # ignore presence of unnecessary tuple/list/dict
            'D',  # ignore documentation related warnings
            'F401',  # ignore presence of unused imports
            'F841',  # ignore presence of unused variables
            'I',  # ignore import order related warnings
            'N802',  # ignore presence of upper case in function names
            'W504',  # ignore line breaks after binary operator (new rule added in 2018)
        ],
        max_line_length=200,
        max_complexity=10,
        show_source=True,
    )

    stdout = sys.stdout
    sys.stdout = sys.stderr
    # implicitly calls report_errors()
    report = style_guide.check_files([
        os.path.dirname(os.path.dirname(__file__)),
    ])
    sys.stdout = stdout

    if report.total_errors:
        # output summary with per-category counts
        print()
        report._application.formatter.show_statistics(report._stats)
        print(
            'flake8 reported {report.total_errors} errors'
            .format(**locals()), file=sys.stderr)

    assert not report.total_errors, \
        'flake8 reported {report.total_errors} errors'.format(**locals())
