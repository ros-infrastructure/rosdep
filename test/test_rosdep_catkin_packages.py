import contextlib
import os
import tempfile

from rosdep2.catkin_packages import find_catkin_packages_in


@contextlib.contextmanager
def directory(path):
    cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(cwd)


def create_package_xml(path, version='0.1.0'):
    path = os.path.abspath(path)
    os.makedirs(path)

    template = """\
<?xml version="1.0"?>
<package>
  <name>{0}</name>
  <version>{1}</version>
  <description>Package {0}</description>
  <license>BSD</license>

  <maintainer email="foo@bar.com">Foo Bar</maintainer>
</package>
""".format(path.split('/')[-1], version)

    with open(os.path.join(path, 'package.xml'), 'w+') as f:
        f.write(template)


def test_find_catkin_packages_in():
    tmp_dir = tempfile.mkdtemp()
    with directory(tmp_dir):
        create_package_xml('src/foo', '0.2.0')
        create_package_xml('src/bar', '0.3.0')
        create_package_xml('src/baz', '0.2.0')
        pkgs = find_catkin_packages_in('src')
        assert sorted(pkgs) == sorted(['foo', 'bar', 'baz']), \
               'actually: ' + str(sorted(pkgs))
