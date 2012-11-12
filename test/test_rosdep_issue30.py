import os
import subprocess
import tempfile
import unittest

class Issue30TestCase(unittest.TestCase):
    def testIssue30(self):
        d = make_temp_dir()
        try:
            cd(d)
            script = '''#!/bin/bash
mkdir ws
mkdir ws/src
mkdir ws/devel
cd ws/src
catkin_init_workspace > /dev/null
cd ..
cd devel
cmake ../src > /dev/null
source develspace/setup.bash
cd ../src
git clone git://github.com/ros-drivers/joystick_drivers.git > /dev/null
rosdep keys spacenav_node
'''
            output = run_script(script)
            self.maxDiff = None
            self.assertEqual('libspnav-dev libx11-dev spacenavd'.split(),
                             sorted(output.split()))
        finally:
            subprocess.call(['rm', '-rf', d])

def make_temp_dir():
    return tempfile.mkdtemp()

def cd(d):
    os.chdir(d)

def write_file(filename, contents):
    with open(filename, 'w') as f:
        f.write(contents)

def run_script(contents):
    filename = 'commands.bash'
    write_file(filename, contents)
    os.chmod(filename, 0x755)
    p = subprocess.Popen([os.path.join('.', filename)], stdout=subprocess.PIPE)
    p.wait()
    return p.stdout.read()

