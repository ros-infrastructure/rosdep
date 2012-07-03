from rosdep2.catkin_support import get_installer, get_catkin_view, resolve_for_apt, ValidationFailed

def test_workflow():
    try:
        installer = get_installer(APT_INSTALLER)
        view = get_catkin_view('fuerte', 'ubuntu', 'lucid')
        resolved = resolve_for_os('cmake', view, installer, 'ubuntu', 'lucid')
        assert ['cmake'] == resolved
        resolved = resolve_for_os('python', view, installer, 'ubuntu', 'lucid')
        assert resolved == ['python-dev']
    except ValidationFailed:
        # tests fail on the server because 'rosdep init' has not been run
        pass
