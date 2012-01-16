from distutils.core import setup

setup(name='rosdep',
      version= '0.2.1',
      packages=['rosdep2', 'rosdep2.platforms'],
      package_dir = {'':'src'},
      data_files=[('man/man1', ['doc/man/rosdep.1'])],
      scripts = ['scripts/rosdep', 'scripts/rosdep-source'],
      author = "Tully Foote, Ken Conley", 
      author_email = "foote@willowgarage.com, kwc@willowgarage.com",
      url = "http://www.ros.org/wiki/rosdep",
      download_url = "http://pr.willowgarage.com/downloads/rosdep/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      description = "rosdep system dependency installation tool", 
      long_description = """\
Command-line tool for installing system dependencies on a variety of platforms.
""",
      license = "BSD"
      )
