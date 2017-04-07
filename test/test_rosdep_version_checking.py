import nose
import os
from rosdep2.main import rosdep_main
from cStringIO import StringIO
import shutil
import sys
from nose.tools import with_setup





#This test is simply asking to rosdep to install a version of rospy than does not exist
#if rosdep print that rosdeps have been successfully met it will fail

package_str = """<?xml version="1.0"?>
<package format="2">
  <name>test</name>
  <version>0.0.1</version>

  <license>BSD</license>

  <description>
    This is a test...
  </description>

  <url type="repository">https://fixme.com</url>
  <url type="bugtracker">https://fixme.com</url>

  <author>Thomas Kostas</author>
  <author email="tkostas75@gmail.com">yota</author>
  <maintainer email="tkostas75@gmail.com">yota</maintainer>


  <depend version_gte="1984.3.14159265359">rospy</depend>

</package>
"""


def write_data(fd, data):
    if (fd != None):
        try:
            fd.write(data)
            fd.close()
        except:
            raise ValueError("TEST SETUP FAILURE]Failed to setup package file for testing")

def create_file(file_path):
    fd = None
    actual_path = os.path.abspath(__file__)
    directory = os.path.dirname(actual_path)
    abs_path = directory + file_path
    directory = os.path.dirname(abs_path)

    if (not os.path.exists(directory)):
        try:
            os.makedirs(directory)
        except:
            raise ValueError("Failed to setup package file for testing")
    try:
        fd = open(abs_path, "w")
    except:
        raise ValueError("[TEST SETUP FAILURE]Failed to setup package file for testing")
    return fd

def setup_function():
    fd = create_file('/src/package.xml')
    write_data(fd, package_str)

def teardown_function():
    actual_path = os.path.abspath(__file__)
    directory = os.path.dirname(actual_path)
    directory = directory + '/src'
    shutil.rmtree(directory)


@with_setup(setup_function, teardown_function)
def test_version_checking():
    opt = ['install', '--from-path', 'src']
    my_stdout = StringIO()
    sys.stdout = my_stdout
    rosdep_main(opt)
    sys.stdout = sys.__stdout__
    if (str(my_stdout.getvalue().strip()) == "#All required rosdeps installed successfully"):
        raise ValueError("[TEST FAILURE]Version checking has not correctly been done")
