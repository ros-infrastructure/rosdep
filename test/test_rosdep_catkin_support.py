from rosdep2.catkin_support import get_apt_installer, get_catkin_view, resolve_for_apt, ValidationFailed

def test_workflow():
    try:
        installer = get_apt_installer()
        view = get_catkin_view('fuerte', 'ubuntu', 'lucid')
        resolved = resolve_for_apt('cmake', view, installer, 'ubuntu', 'lucid')
        assert ['cmake'] == resolved
        resolved = resolve_for_apt('python', view, installer, 'ubuntu', 'lucid')
        assert resolved == ['python-dev']
    except ValidationFailed:
        # tests fail on the server because 'rosdep init' has not been run
        pass
