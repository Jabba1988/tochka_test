from django.conf.urls import url

from .views import historical, insider, insider_name, analytics, delta


app_name = 'dj_1'

urlpatterns = [

    url(r'^$', historical, name="historical"),
    url(r'^insider$', insider, name="insider"),
    url(r'^insider/(?P<insider_name>[A-Za-z0-9. ]+)$', insider_name, name="insider_name"),
    url(r'^analytics$', analytics, name="analytics"),
    url(r'^delta$', delta, name="delta"),
]