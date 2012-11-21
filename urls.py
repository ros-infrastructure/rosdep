from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('prerelease_website.rosinstall_gen.views',
    url(r'^generate/(?P<distro>.*)/(?P<packages>.*)$', 'index'),
)
