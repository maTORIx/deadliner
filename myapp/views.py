from django.shortcuts import render, redirect
from myapp.models import *
from django.http import HttpResponse
import datetime
from django.template.context_processors import csrf
from django.views.generic.base import TemplateView
from django.views.generic import FormView
from django.http import Http404
import hashlib
import secrets
import uuid
from django.db.utils import IntegrityError
# Create your views here.

def handler404(request):
    return render(request, "404.html", status=404)

def isMember(org, user_id):
    users = org.getUsers().filter(id=user_id)
    return not not len(users)

class Home(TemplateView):
    """home page"""
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        return super(Home, self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        user = User.objects.get(id=self.request.session["user_id"])
        orgs = user.getOrganization()
        commits = user.getCommits()
        org_requests = user.getRequests()
        data_requests = []
        for data in org_requests:
            data_requests.append({
                "data": data,
                "org": data.getOrg(),
            })
        print(data_requests)
        context["message"] = "message"
        context["orgs"] = orgs
        context["org_requests"] = data_requests
        context["commits"] = commits
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
        users = User.objects.filter(email=email)
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
        return super(OrgForm, self).get(request, **kwargs)

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
        newOrg = Organization(name=name, author=user.id,
                              color="#" + secrets.token_hex(3),
                              link_img=img, link_homepage=homepage)
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
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not len(orgs):
            return render(request, "404.html", status=404)
        return super(ViewOrg, self).get(request, **kwargs)

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
            return render(request, "404.html", status=404)
        org = orgs[0]
        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newProject = Project(title=title, description=description,
                             date_deadline=date_deadline, org_id=org.id,
                             completed=False)
        try:
            newProject.save()
        except IntegrityError:
            return redirect("/org/"
                            + self.kwargs["org"]
                            + "/?err=project name already exists")
        except:
            return redirect("/org/"
                            + self.kwargs["org"]
                            + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + title)

    def put(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return render(request, "404.html", status=404)
        org = orgs[0]
        description = self.request.PUT.get("description")
        homepage = self.request.PUT.get("homepage")
        img_link = self.request.PUT.get("img")
        color = self.request.PUT.get("color")
        org.description = description
        org.link_homepage = homepage
        org.link_img = img_link
        org.color = color
        try:
            org.save()
        except:
            return redirect("/org/" + org.name + "/?err=Invalid form data")
        return redirect("/org/" + org.name)


class ViewProject(TemplateView):
    template_name = "project.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return render(request, "404.html", status=404)
        org = orgs[0]
        projects = Project.objects.filter(title=self.kwargs["proj"],
                                          org_id=org.id)
        if not(len(projects)):
            return render(request, "404.html", status=404)
        return super(ViewProject, self).get(request, *args, **kwargs)

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
        context["ready"] = project.isReady()
        context["jobs"] = project.getChildlen()
        context["commits"] = project.getCommits()
        context["deadlines"] = project.getDeadlines()
        context["project_deadline"] = project.date_deadline.strftime(
            "%Y-%m-%d")
        return context

    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not len(orgs):
            return render(request, "404.html", status=404)
        org = orgs[0]
        projects = Project.objects.filter(title=self.kwargs["proj"], org_id=org.id)
        if not len(orgs):
            return render(request, "404.html", status=404)
        project = projects[0]
        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newJob = Job(title=title, description=description, date_deadline=date_deadline,
                     project_id=project.id, parent_id=None, completed=False)
        try:
            newJob.save()
        except IntegrityError:
            return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + "/?err=project name already exists")
        except:
            return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"])

    def put(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return render(request, "404.html", status=404)
        org = orgs[0]
        projects = Project.objects.filter(
            title=self.kwargs["proj"], org_id=org.id)
        if not(len(projects)):
            return render(request, "404.html", status=404)
        project = projects[0]

        description = request.PUT.get("description")
        deadline = request.PUT.get("deadline")
        completed = 0
        if not not request.PUT.get("completed"):
            completed = 1
        print(completed)
        project.description = description
        project.date_deadline = deadline
        project.completed = completed
        try:
            project.save()
        except:
            return redirect("/org/" + org.name + "/" + project.title + "/?err=Invalid form data")

        return redirect("/org/" + org.name + "/" + project.title)
        

class ViewJob(TemplateView):
    template_name = "job.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return render(request, "404.html", status=404)
        org = orgs[0]
        projects = Project.objects.filter(
            title=self.kwargs["proj"], org_id=org.id)
        if not(len(projects)):
            return render(request, "404.html", status=404)
        project = projects[0]

        # get job <- jobgetter <- 最強 <- 最上 <- もがみ <- 神?
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            print(parent_id, project.id, )
            jobs = Job.objects.filter(
                parent_id=parent_id, project_id=project.id, title=data)
            if not(len(jobs)):
                return render(request, "404.html", status=404)
            parent_id = jobs[0].id
        job = jobs[0]
        return super(ViewJob, self).get(request, *args, **kwargs)

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
            jobs = Job.objects.filter(
                parent_id=parent_id, project_id=project.id, title=data)
            if not(len(jobs)):
                return render(request, "404.html", status=404)
            parent_id = jobs[0].id
        job = jobs[0]
        if(job.parent_id):
            parent = Job.objects.get(id=job.parent_id)
        else:
            parent = project

        message = self.request.GET.get("err")
        context["message"] = message
        context["org"] = org
        context["project"] = project
        context["parent_deadline"] = parent.date_deadline.strftime("%Y-%m-%d")
        context["job"] = job
        context["ready"] = job.isReady()
        context["job_deadline"] = job.date_deadline.strftime(
            "%Y-%m-%d")
        context["jobs"] = job.getChildlen()
        context["children"] = job.getChildlen()
        context["commits"] = job.getCommits()
        context["deadlines"] = job.getDeadlines()
        context["job_url"] = self.kwargs["job"]
        return context

    def post(self, request, *args, **kwargs):
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        org = orgs[0]
        projects = Project.objects.filter(title=self.kwargs["proj"])
        project = projects[0]

        # jobGetter
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            jobs = Job.objects.filter(
                parent_id=parent_id, project_id=project.id, title=data)
            if not(len(jobs)):
                return render(request, "404.html", status=404)
            parent_id = jobs[0].id
        job = jobs[0]

        title = self.request.POST.get("name")
        description = self.request.POST.get("description")
        date_deadline = self.request.POST.get("deadline")
        newJob = Job(title=title, description=description, date_deadline=date_deadline,
                     project_id=project.id, parent_id=job.id, completed=False)
        try:
            newJob.save()
        except IntegrityError:
            return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + self.kwargs["job"] + "/?err=project name already exists")
        except:
            return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + self.kwargs["job"] + "/?err=Invalid form data")
        return redirect("/org/" + self.kwargs["org"] + "/" + self.kwargs["proj"] + "/" + self.kwargs["job"])

    def put(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not(len(orgs)):
            return render(request, "404.html", status=404)
        org = orgs[0]
        projects = Project.objects.filter(
            title=self.kwargs["proj"], org_id=org.id)
        if not(len(projects)):
            return render(request, "404.html", status=404)
        project = projects[0]

        # jobGetter
        parent_id = None
        jobs = None
        for data in self.kwargs["job"].split("/"):
            jobs = Job.objects.filter(
                parent_id=parent_id, project_id=project.id, title=data)
            if not(len(jobs)):
                return render(request, "404.html", status=404)
            parent_id = jobs[0].id
        job = jobs[0]

        completed = 0
        if not not request.PUT.get("completed"):
            completed = 1
        description = request.PUT.get("description")
        deadline = request.PUT.get("deadline")
        print(description, deadline)
        job.description = description
        job.date_deadline = deadline
        job.completed = completed
        try:
            job.save()
        except:
            redirect("/org/"
                     + org.name
                     + "/" + project.title
                     + self.kwargs["job"]
                     + "/"
                     + self.kwargs("job")
                     + "/?err=Invalid form data")

        return redirect("/org/"
                        + org.name
                        + "/"
                        + project.title
                        + "/"
                        + self.kwargs["job"])


class ViewCommit(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "404.html", status=404)

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
            newCommit = Commit(org_id=org.id, project_id=None,
                               user_id=request.session["user_id"], parent_id=None, body=body, path=path)
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
            newCommit = Commit(org_id=org.id, project_id=project.id,
                               user_id=request.session["user_id"], parent_id=None, body=body, path=path)
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
                jobs = Job.objects.filter(
                    parent_id=parent_id, project_id=project.id, title=data)
                if not(len(jobs)):
                    return redirect("org/" + path + "/?err=Job not found")
                parent_id = jobs[0].id
            job = jobs[0]
            newCommit = Commit(org_id=org.id, project_id=project.id,
                               user_id=request.session["user_id"], parent_id=job.id, body=body, path=path)
            try:
                newCommit.save()
            except:
                return redirect("org/" + path + "/?err=Internal server error")
        return redirect("org/" + path)

class ViewMember(TemplateView):
    template_name = "memberForm.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        print(self.kwargs["org"])
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not len(orgs):
            return render(request, "404.html", status=404)
        org = orgs[0]
        users = org.getUsers().filter(id=request.session["user_id"])
        if not len(users):
            return redirect("/",status=404)
        return super(ViewMember, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewMember, self).get_context_data(**kwargs)
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        print(orgs)
        org = orgs[0]
        user_requests = org.getRequests()
        print(user_requests)
        requests_data = []
        for data in user_requests:
            requests_data.append({
                "data": data,
                "user": data.getUser(),
            })
        print(org)
        context["err"] = self.request.GET.get("err")
        context["org"] = org
        context["user"] = User.objects.get(id=self.request.session["user_id"])
        context["members"] = org.getUsers()
        context["requests"] = requests_data
        return context
    
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not len(orgs):
            return render(request, "404.html", status=404)
        org = orgs[0]
        users = User.objects.filter(id=self.request.POST.get("user_id"))
        if not len(users):
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=User not found",
                            status=500)
        user = users[0]
        user_requests = MemberRequest.objects.filter(user_id=user.id, organization_id=org.id)
        if not len(user_requests):
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=Request not found",
                            status=500)
        user_request = user_requests[0]
        newMember = Member(user_id=user.id, organization_id=org.id)
        try:
            newMember.save()
        except:
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=Internal server error",
                            status=500)
        user_request.delete()
        return redirect("/", status=200)
    
    def delete(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.kwargs["org"])
        if not len(orgs):
            return render(request, "404.html", status=404)
        org = orgs[0]
        users = User.objects.filter(id=self.request.POST.get("user_id"))
        if not len(users):
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=User not found",
                            status=500)
        user = users[0]
        members = Member.objects.filter(organization_id=org.id, user_id=user.id)
        if not len(members):
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=Member not found",
                            status=500)
        member = members[0]
        try:
            member.delete()
        except:
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=Internal server error",
                            status=500)
        return redirect("/member/"
                        + org.name,
                        status=200)

class ViewRequest(TemplateView):
    template_name = "memberRequest.html"

    def get(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        if not (self.kwargs["id"]):
            return redirect("/")
        user_requests = MemberRequest.objects.filter(id=self.kwargs["id"])
        if not len(user_requests):
            return render(request, "404.html", {})
        user_request = user_requests[0]
        if not user_request.user_id is request.session["user_id"]:
            return render(request, "401.html", {})
        return super(ViewRequest, self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ViewRequest, self).get_context_data(**kwargs)
        user_requests = MemberRequest.objects.filter(id=self.kwargs["id"])
        user_request = user_requests[0]
        orgs = Organization.objects.filter(id=user_request.organization_id)
        org = orgs[0]
        user = User.objects.get(id=user_request.user_id)
        
        context["err"] = self.request.GET.get("err")
        context["org"] = org
        context["user"] = user
        return context
    
    def post(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        orgs = Organization.objects.filter(name=self.request.POST.get("org"))
        if not len(orgs):
            return render(request, "404.html", status=404)
        org = orgs[0]
        users = org.getUsers().filter(id=request.session["user_id"])
        if not len(users):
            return redirect("/",status=401)
        
        email = self.request.POST.get("email")
        users = User.objects.filter(email=email)
        if not len(users):
            return redirect("/member/"
                            + self.kwargs["org"]
                            + "/?err=User not found",
                            status=500)
        user = users[0]
        
        newRequest = MemberRequest(organization_id=org.id, user_id=user.id)
        try:
            newRequest.save()
        except:
            return redirect("/member/"
                            + org.name
                            + "/?err=Internal server error",
                            status=500)
        return redirect("/member/"
                            + org.name,
                            status=200)

    def delete(self, request, *args, **kwargs):
        if not (request.session["user_id"]):
            return redirect("/login")
        user_requests = MemberRequest.objects.filter(id=self.kwargs["id"])
        if not len(user_requests):
            return render(request, "404.html", {})
        user_request = user_requests[0]
        orgs = Organization.objects.filter(id=user_request.organization_id)
        user_request.delete()
        if not len(orgs):
            return redirect("/")
        return redirect("/member/" + orgs[0].name)