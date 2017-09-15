"""deadliner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin
from myapp import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.Home.as_view()),
    url(r'^login/?$', views.Login.as_view()),
    url(r'^signup/?$', views.Signup.as_view()),
    url(r'^logout/?$', views.logout),
    url(r'^org/?$', views.OrgForm.as_view()),
    url(r'^org/(?P<org>[A-Za-z0-9\-\+\_\.]+)/?$', views.ViewOrg.as_view()),
    url(r'^org/(?P<org>[A-Za-z0-9\-\+\_.]+)/(?P<proj>[A-Za-z0-9\-\+\_.]+)/?$', views.ViewProject.as_view()),
    url(r'^org/(?P<org>[A-Za-z0-9\-\+\_\.]+)/(?P<proj>[A-Za-z0-9\-\+\_.]+)/(?P<job>[A-Za-z0-9\-\+\_/.]+)/?$', views.ViewJob.as_view()),
    url(r'^commit/?', views.ViewCommit.as_view()),
    url(r'^member/(?P<org>[A-Za-z0-9\-\+\_]+)/?$', views.ViewMember.as_view()),
    url(r'^request/(?P<id>[0-9]*)/?$', views.ViewRequest.as_view()),
    url(r'^task/?(?P<org>[A-Za-z0-9\-\+\_\.]*)?/?$', views.ViewTask.as_view()),
    url(r'^expense/?(?P<org>[A-Za-z0-9\-\+\_\.]*)?/?$', views.ViewExpense.as_view()),
]
