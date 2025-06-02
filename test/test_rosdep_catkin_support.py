from rosdep2.catkin_support import get_installer, get_catkin_view, ValidationFailed, resolve_for_os

from rosdep2.platforms.debian import APT_INSTALLER
import pytest


@pytest.mark.usefixtures('fake_rosdep')
def test_workflow():
    installer = get_installer(APT_INSTALLER)
    view = get_catkin_view('fuerte', 'ubuntu', 'lucid')
    resolved = resolve_for_os('cmake', view, installer, 'ubuntu', 'lucid')
    assert ['cmake'] == resolved
    resolved = resolve_for_os('python', view, installer, 'ubuntu', 'lucid')
    assert resolved == ['python-dev']
