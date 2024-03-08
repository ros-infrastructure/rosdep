from rosdep2.catkin_support import get_installer, get_catkin_view, ValidationFailed, resolve_for_os

from rosdep2.platforms.debian import APT_INSTALLER
import pytest


@pytest.mark.online
def test_workflow():
    try:
        installer = get_installer(APT_INSTALLER)
        view = get_catkin_view('noetic', 'ubuntu', 'focal')
        resolved = resolve_for_os('cmake', view, installer, 'ubuntu', 'focal')
        assert ['cmake'] == resolved
        resolved = resolve_for_os('python3', view, installer, 'ubuntu', 'focal')
        assert resolved == ['python3-dev']
    except ValidationFailed:
        # tests fail on the server because 'rosdep init' has not been run
        pass
