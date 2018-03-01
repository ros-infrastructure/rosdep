import os
from setuptools import setup

exec(open(os.path.join(os.path.dirname(__file__), 'src', 'rosdep2', '_version.py')).read())

setup(
    name='rosdep',
    version=__version__,  # noqa:F821
    packages=['rosdep2', 'rosdep2.platforms'],
    package_dir={'': 'src'},
    install_requires=['catkin_pkg', 'rospkg >= 1.0.37', 'rosdistro >= 0.4.0', 'PyYAML >= 3.1'],
    test_suite='nose.collector',
    test_requires=['mock', 'nose >= 1.0'],
    scripts=['scripts/rosdep', 'scripts/rosdep-source'],
    author='Tully Foote, Ken Conley',
    author_email='tfoote@osrfoundation.org',
    url='http://wiki.ros.org/rosdep',
    download_url='http://download.ros.org/downloads/rosdep/',
    keywords=['ROS'],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License'],
    description='rosdep package manager abstraction tool for ROS',
    long_description='Command-line tool for installing system '
                     'dependencies on a variety of platforms.',
    license='BSD'
)
