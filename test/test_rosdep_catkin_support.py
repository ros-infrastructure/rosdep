from rosdep2.catkin_support import get_installer, get_catkin_view, ValidationFailed, resolve_for_os

from rosdep2.platforms.debian import APT_INSTALLER
from rosdep2.cache_tools import CACHE_PATH_ENV
from rosdep2.sources_list import SOURCE_PATH_ENV
import pytest
import os
from tempfile import mkdtemp


def get_test_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_cache_dir():
    # get_catkin_view calls update(), so we need a writable location
    return mkdtemp()


def get_source_list_dir():
    p = os.path.join(get_test_dir(), "sources.list.d.good")
    assert os.path.isdir(p)
    return p


@pytest.mark.online
def test_workflow():
    old_cpe = os.getenv(CACHE_PATH_ENV, None)
    old_spe = os.getenv(SOURCE_PATH_ENV, None)
    try:
        os.environ[CACHE_PATH_ENV] = get_cache_dir()
        os.environ[SOURCE_PATH_ENV] = get_source_list_dir()
        installer = get_installer(APT_INSTALLER)
        view = get_catkin_view('noetic', 'ubuntu', 'focal')
        resolved = resolve_for_os('cmake', view, installer, 'ubuntu', 'focal')
        assert ['cmake'] == resolved
        resolved = resolve_for_os('python3', view, installer, 'ubuntu', 'focal')
        assert resolved == ['python3-dev']
    except ValidationFailed:
        # tests fail on the server because 'rosdep init' has not been run
        pass
    finally:
        if old_cpe is None:
            del os.environ[CACHE_PATH_ENV]
        else:
            os.environ[CACHE_PATH_ENV] = old_cpe
        if old_spe is None:
            del os.environ[SOURCE_PATH_ENV]
        else:
            os.environ[SOURCE_PATH_ENV] = old_spe
