from django.shortcuts import render, redirect
from myapp.models import *
from django.http import HttpResponse
import datetime
from django.template.context_processors import csrf
from django.views.generic.base import TemplateView
from django.views.generic import FormView
import hashlib
import secrets
import uuid
# Create your views here.


class Home(TemplateView):
    """home page"""
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        return super(Home,self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context["message"] = "message"
        return context


class Login(TemplateView):
    template_name = "login.html"

    def get_context_data(self, **kwargs):
        context = super(Login, self).get_context_data(**kwargs)
        message = self.request.GET.get("err")
        context["message"] = message
        return context

    def post(self, request, *args, **kwargs):
        password_low = request.POST.get("password").encode("utf-8")
        print(password_low)
        email = request.POST.get("email")
        users = User.objects.filter(email = email)
        if not len(users):
            return redirect("/login", err="E-mail or password is wrong")
        user = users[0]
        salt = user.salt
        sha512 = hashlib.sha512()
        sha512.update(password_low)
        sha512.update(salt)
        password_hashed = sha512.digest()
        print("1")
        if(not user.password == password_hashed):
            print("err")
            return redirect("/login", err="E-mail or password is wrong")

        # Cookie
        now = datetime.datetime.now()
        expires = datetime.datetime(now.year, (now.month + 3), now.day)
        uuid = user.getUUID()
        resp = redirect("/")
        print("2")
        resp.set_cookie("user_session", uuid.uuid,
                        max_age=(1000 * 60 * 60 * 24 * 30 * 3),
                        expires=expires, path='/',
                        domain=None,
                        secure=False,
                        httponly=True)
        return resp


class Signup(TemplateView):
    template_name = "signup.html"

    def get_context_data(self, **kwargs):
        context = super(Signup, self).get_context_data(**kwargs)
        message = self.request.GET.get("err")
        context["message"] = message
        return context

    def post(self, request, *args, **kwargs):
        password_low = self.request.POST.get("password").encode("utf-8")
        email = self.request.POST.get("email")
        name = self.request.POST.get("name")
        salt = secrets.token_bytes(16)
        sha512 = hashlib.sha512()
        sha512.update(password_low)
        sha512.update(salt)
        password_hashed = sha512.digest()

        newUser = User(email=email, password=password_hashed,
                       salt=salt, name=name)
        newUser.save()
        return redirect("/login")

def logout(request):
    resp = redirect("/login")
    resp.delete_cookie("user_session")
    return resp

class OrgForm(TemplateView):
    template_name = "orgform.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        return super(OrgForm,self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrgForm, self).get_context_data(**kwargs)
        message = self.request.GET.get("err")
        context["message"] = message
        return context

    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        name = request.POST.get("name")
        img = request.POST.get("img")
        homepage = request.POST.get("homepage")
        print(name, img, homepage)

        user = User.objects.get(id=request.session["user_id"])
        if len(Organization.objects.filter(name=name)):
            return redirect('/org/?err=This organization name already exists')
        newOrg = Organization(name=name, author=user.id, color=secrets.token_hex(3), link_img=img, link_homepage=homepage)
        newOrg.save()
        newMember(organization_id=newOrg.id, user_id=user.id)
        return redirect("/")
