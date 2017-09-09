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
from django.db.utils import IntegrityError
# Create your views here.


class Home(TemplateView):
    """home page"""
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        return super(Home,self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        user = User.objects.get(id=self.request.session["user_id"])
        orgs = user.getOrganization()
        context = super(Home, self).get_context_data(**kwargs)
        context["message"] = "message"
        context["orgs"] = orgs
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
        try:
            newUser.save()
        except:
            return redirect("/login/?err=Invalid form data")
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
        try:
            newOrg.save()
        except:
            return redirect("/org/?err=Invalid form data")
        newMember = Member(organization_id=newOrg.id, user_id=user.id)
        newMember.save()
        return redirect("/")

class ViewOrg(TemplateView):
    template_name = "organization.html"
    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        print(self.kwargs["org"])
        org = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(org)):
            return redirect("/")
        return super(ViewOrg,self).get(request, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ViewOrg, self).get_context_data(**kwargs)

        orgs = Organization.objects.filter(name=self.kwargs["org"])
        org = orgs[0]

        message = self.request.GET.get("err")
        context["message"] = message
        context["org"] = org
        context["projects"] = org.getProjects()
        context["commits"] = org.getCommits()
        context["deadlines"] = org.getDeadlines()
        return context
    
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return redirect("/")
        org = orgs[0]
        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newProject = Project(title=title, description=description, date_deadline=date_deadline, org_id=org.id, completed=False)
        try:
            newProject.save()
        except IntegrityError:
            return redirect("/org/" + self.kwargs["org"] + "/?err=project name already exists")
        except :
            return redirect("/org/" + self.kwargs["org"] + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + title)

class ViewProject(TemplateView):
    template_name = "project.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        org = Organization.objects.filter(name=self.kwargs["org"])
        project = Project.objects.filter(title=self.kwargs["proj"])
        if not(len(org)) or not(len(project)):
            return redirect("/")
        return super(ViewProject,self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ViewProject, self).get_context_data(**kwargs)

        orgs = Organization.objects.filter(name=self.kwargs["org"])
        org = orgs[0]
        projects = Project.objects.filter(title=self.kwargs["proj"])
        project = projects[0]

        message = self.request.GET.get("err")
        context["message"] = message
        context["org"] = org
        context["project"] = project
        context["jobs"] = project.getChildlen()
        context["commits"] = project.getCommits()
        context["deadlines"] = project.getDeadlines()
        return context
    
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        projects = Project.objects.filter(title=self.kwargs["proj"])
        if not(len(orgs)) or not(len(projects)):
            return redirect("/")
        org = orgs[0]
        project = projects[0]
        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newJob = Job(title=title, description=description, date_deadline=date_deadline, project_id=project.id, parent_id=None, completed=False)
        try:
            newJob.save()
        except IntegrityError:
            return redirect("/org/" + self.kwargs["org"] +  "/" + self.kwargs["proj"] +"/?err=project name already exists")
        except :
            return redirect("/org/" + self.kwargs["org"] +  "/" + self.kwargs["proj"] + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + "/" + title)
    
class ViewJob(TemplateView):
    template_name = "job.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        projects = Project.objects.filter(title=self.kwargs["proj"])
        if not(len(orgs)) or not(len(projects)):
            return redirect("/")
        # get job <- jobgetter <- 最強 <- 最上 <- もがみ <- 神?
        project = projects[0]
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            print(parent_id, project.id, )
            jobs = Job.objects.filter(parent_id=parent_id, project_id=project.id,title=data)
            if not(len(jobs)):
                return redirect("/")
            parent_id = jobs[0].id
        job = jobs[0]
        return super(ViewJob,self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ViewJob, self).get_context_data(**kwargs)

        orgs = Organization.objects.filter(name=self.kwargs["org"])
        org = orgs[0]
        projects = Project.objects.filter(title=self.kwargs["proj"])
        project = projects[0]

        # jobGetter
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            jobs = Job.objects.filter(parent_id=parent_id, project_id=project.id)
            if not(len(jobs)):
                return redirect("/")
            parent_id = jobs[0].id
        job = jobs[0]

        message = self.request.GET.get("err")
        context["message"] = message
        context["org"] = org
        context["project"] = project
        context["job"] = job
        context["children"] = job.getChildlen()
        context["commits"] = job.getCommits()
        context["deadlines"] = job.getDeadlines()
        context["job_url"] = self.kwargs["job"]
        return context
    
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        projects = Project.objects.filter(title=self.kwargs["proj"])

        # jobGetter
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            jobs = Job.objects.filter(parent_id=parent_id, project_id=project.id)
            if not(len(jobs)):
                return redirect("/")
            parent_id = jobs[0].id
        job = jobs[0]

        if not(len(orgs)) or not(len(projects)):
            return redirect("/")
        org = orgs[0]
        project = projects[0]
        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newJob = Job(title=title, description=description, date_deadline=date_deadline, project_id=project.id, parent_id=None, completed=False)
        try:
            newJob.save()
        except IntegrityError:
            return redirect("/org/" + self.kwargs["org"] +  "/" + self.kwargs["proj"] +"/?err=project name already exists")
        except :
            return redirect("/org/" + self.kwargs["org"] +  "/" + self.kwargs["proj"] + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + "/" + title)

class ViewCommit(TemplateView):
    def get(self, request, *args, **kwargs):
        return redirect("/")
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        path = request.POST.get("url")
        body = request.POST.get("body")
        path_ary = path.split("/")
        if not(len(path_ary)) or not path:
            return redirect("org/" + path + "/?err=Invalid form")
        if len(path_ary) == 1:
            orgs = Organization.objects.filter(name=path_ary[0])
            if not(len(orgs)):
                return redirect("org/" + path + "/?err=organization not found")
            org = orgs[0]
            newCommit = Commit(org_id=org.id, project_id=None, user_id=request.session["user_id"], parent_id=None, body=body)
            try:
                newCommit.save()
            except:
                return redirect("org/" + path + "/?err=Internal server error")
        if len(path_ary) == 2:
            orgs = Organization.objects.filter(name=path_ary[0])
            if not(len(orgs)):
                return redirect("org/" + path + "/?err=organization not found")
            org = orgs[0]
            projects = Project.objects.filter(org_id=org.id, title=path_ary[1])
            if not(len(projects)):
                return redirect("org/" + path + "/?err=Project not found")
            project = projects[0]
            newCommit = Commit(org_id=org.id, project_id=project.id, user_id=request.session["user_id"], parent_id=None, body=body)
            try:
                newCommit.save()
            except:
                return redirect("org/" + path + "/?err=Internal server error")

        if len(path_ary) >= 3:
            orgs = Organization.objects.filter(name=path_ary[0])
            if not(len(orgs)):
                return redirect("org/" + path + "/?err=organization not found")
            org = orgs[0]
            projects = Project.objects.filter(org_id=org.id, title=path_ary[1])
            if not(len(projects)):
                return redirect("org/" + path + "/?err=Project not found")
            project = projects[0]
            parent_id = None
            jobs = None
            for data in path_ary[2:]:
                jobs = Job.objects.filter(parent_id=parent_id, project_id=project.id)
                if not(len(jobs)):
                    return redirect("org/" + path + "/?err=Job not found")
                parent_id = jobs[0].id
            job = jobs[0]
            newCommit = Commit(org_id=org.id, project_id=project.id, user_id=request.session["user_id"], parent_id=job.id, body=body)
            try:
                newCommit.save()
            except:
                return redirect("org/" + path + "/?err=Internal server error")

        return redirect("org/" + path)