from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('prerelease_website.rosinstall_gen.views',
    url(r'^generate/dry/raw/(?P<distro>.*)/(?P<variant>.*)$', 'dry_raw'),
    url(r'^generate/dry/(?P<distro>.*)/(?P<packages>.*)$', 'dry_index'),
    url(r'^generate/raw/(?P<distro>.*)/(?P<packages>.*)$', 'raw'),
    url(r'^generate/(?P<distro>.*)/(?P<packages>.*)$', 'index'),
)
