from rosdep2.catkin_support import get_apt_installer, get_catkin_view, resolve_for_apt

def test_workflow():
    installer = get_apt_installer()
    view = get_catkin_view('fuerte', 'ubuntu', 'lucid')
    resolved = resolve_for_apt('cmake', view, installer, 'ubuntu', 'lucid')
    assert ['cmake'] == resolved
    resolved = resolve_for_apt('python', view, installer, 'ubuntu', 'lucid')
    assert resolved == ['python-dev']
