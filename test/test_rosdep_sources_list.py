import rospkg.distro
import rosdep2.sources_list

def test_get_sources_list_dir():
    assert rosdep2.sources_list.get_sources_list_dir()

def test_get_sources_cache_dir():
    assert rosdep2.sources_list.get_sources_cache_dir()

def test_parse_sources_data():
    from rosdep2.sources_list import parse_sources_data
    
    parse_sources_data
    
def test_DataSource():
    data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', ['tag1', 'tag2'])
    assert data_source == rosdep2.sources_list.DataSource('yaml', 'http://fake/url', ['tag1', 'tag2'])
    assert 'yaml' == data_source.type
    assert 'http://fake/url' == data_source.url
    assert ['tag1', 'tag2'] == data_source.tags
    assert 'yaml http://fake/url tag1 tag2' == str(data_source)

    data_source_foo = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', ['tag1', 'tag2'], origin='foo')
    assert data_source_foo != data_source
    assert data_source_foo.origin == 'foo'
    assert '[foo]:\nyaml http://fake/url tag1 tag2' == str(data_source_foo), str(data_source_foo)
    
    assert repr(data_source)

def test_DataSourceMatcher():
    empty_data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', [])
    assert empty_data_source == rosdep2.sources_list.DataSource('yaml', 'http://fake/url', [])

    # matcher must match 'all' tags
    data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', ['tag1', 'tag2'])
    partial_data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', ['tag1'])

    # same tags as test data source
    matcher = rosdep2.sources_list.DataSourceMatcher(['tag1', 'tag2'])
    assert matcher.matches(data_source)
    assert matcher.matches(partial_data_source)
    assert matcher.matches(empty_data_source)

    # alter one tag
    matcher = rosdep2.sources_list.DataSourceMatcher(['tag1', 'tag3'])
    assert not matcher.matches(data_source)
    assert matcher.matches(empty_data_source)
    matcher = rosdep2.sources_list.DataSourceMatcher(['tag1'])
    assert not matcher.matches(data_source)

def test_download_rosdep_data():
    from rosdep2.sources_list import download_rosdep_data, SourceListDownloadFailure
    url = 'https://raw.github.com/ros/rosdep_rules/master/rosdep.yaml'
    data = download_rosdep_data(url)
    assert 'python' in data #sanity check

    # try with a bad URL
    try:
        data = download_rosdep_data('http://badhost.willowgarage.com/rosdep.yaml')
        assert False, "should have raised"
    except SourceListDownloadFailure as e:
        pass
    # try to trigger both non-dict clause and YAMLError clause
    for url in [
        'https://code.ros.org/svn/release/trunk/distros/',
        'https://code.ros.org/svn/release/trunk/distros/manifest.xml',
        ]:
        try:
            data = download_rosdep_data(url)
            assert False, "should have raised"
        except SourceListDownloadFailure as e:
            pass
    
def test_parse_sources_data():
    from rosdep2.sources_list import parse_sources_data
    pass

def test_create_default_matcher():
    distro_name = rospkg.distro.current_distro_codename()
    os_detect = rospkg.os_detect.OsDetect()
    os_name, os_version, os_codename = os_detect.detect_os()

    matcher = rosdep2.sources_list.create_default_matcher()

    # matches full
    os_data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', [distro_name, os_name, os_codename])
    assert matcher.matches(os_data_source)

    # matches against current os
    os_data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', [os_name, os_codename])
    assert matcher.matches(os_data_source)
    
    # matches against current distro
    distro_data_source = rosdep2.sources_list.DataSource('yaml', 'http://fake/url', [distro_name])
    assert matcher.matches(distro_data_source)


def test_SourcesListLoader():
    from rosdep2.sources_list import SourcesListLoader
    loader = SourcesListLoader()
    
    assert [SourcesListLoader.RESOURCE_KEY] == loader.get_loadable_resources()    
    assert [SourcesListLoader.VIEW_KEY] == loader.get_loadable_views()
    assert SourcesListLoader.VIEW_KEY == loader.get_view_key(SourcesListLoader.RESOURCE_KEY)
