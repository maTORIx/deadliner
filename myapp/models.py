from django.db import models
import uuid
from datetime import datetime , timedelta
# Create your models here.


class User(models.Model):
    email = models.CharField(max_length=255, unique=True, null=False)
    password = models.BinaryField(null=False)
    salt = models.BinaryField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)

    def getOrganization(self):
        organizations_id = Member.objects.filter(
            user_id=self.id).values_list("organization_id", flat=True)
        return Organization.objects.filter(id__in=organizations_id)

    def getRequests(self):
        return MemberRequest.objects.filter(user_id=self.id)

    def getUUID(self):
        beforeUUID = UUID.objects.filter(user_id=self.id)
        if(len(beforeUUID)):
            beforeUUID[0].delete()
        newUUID = UUID(user_id=self.id)
        newUUID.save()
        return newUUID

    def getCommits(self):
        return Commit.objects.filter(user_id=self.id)
    
    def getWorkingTask(self):
        return Task.objects.filter(user_id=self.id, completed=False)
    
    def getTask(self):
        return Task.objects.filter(user_id=self.id)

class UUID(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    user_id = models.IntegerField(null=False)

    def getUser(self):
        users = User.objects.filter(id=self.user_id)
        if not(len(users)):
            return None
        return users[0]


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)
    author = models.IntegerField(null=False)
    color = models.CharField(max_length=255, unique=True, null=False)
    link_img = models.CharField(max_length=255)
    link_homepage = models.CharField(max_length=255)
    description = models.TextField(null=True)

    def getUsers(self):
        users_id = Member.objects.filter(
            organization_id=self.id).values_list("user_id", flat=True)
        return User.objects.filter(id__in=users_id)

    def getProjects(self):
        return Project.objects.filter(org_id=self.id)

    def getCommits(self):
        return Commit.objects.filter(org_id=self.id)

    def getDeadlines(self):
        projects = self.getProjects()

        def forMap(data):
            deadline = {
                "path": "/" + data.title,
                "deadline": project.date_deadline
            }
            return data
        deadlines = []
        for project in projects:
            deadlines.extend(project.getDeadlines())
        return deadlines
    
    def getExpenses(self):
        expenses =  Expense.objects.filter(org_id=self.id)
        result = []
        for expense in expenses:
            result.append({
                "data": expense,
                "user": expense.getUser().name,
                "path": expense.getJob().getPath()
            })
        return result

    def getRequests(self):
        return MemberRequest.objects.filter(organization_id=self.id)

    def isMember(self, user_id):
        users_id = Member.objects.filter(
            organization_id=self.id).values_list("user_id", flat=True)
        return user_id in users_id
    
    def getTasks(self):
        projects = self.getProjects()
        tasks = []
        for project in projects:
            tasks = tasks + project.getTasks()
        return tasks
    
    def getRecentTasks(self):
        projects = self.getProjects()
        tasks = []
        for project in projects:
            tasks = tasks + project.getRecentTasks()
        return tasks
        

class Member(models.Model):
    organization_id = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)

    class Meta:
        unique_together = ("organization_id", "user_id")


class MemberRequest(models.Model):
    organization_id = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)

    class Meta:
        unique_together = ("organization_id", "user_id")
    
    def getUser(self):
        users = User.objects.filter(id=self.user_id)
        if not len(users):
            return
        return users[0]
    
    def getOrg(self):
        orgs = Organization.objects.filter(id=self.organization_id)
        if not len(orgs):
            return 
        return orgs[0]


class Project(models.Model):
    title = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    date_create = models.DateTimeField(auto_now_add=True, null=False)
    date_deadline = models.DateTimeField(null=False)
    org_id = models.IntegerField(null=False)
    completed = models.IntegerField(null=False)

    class Meta:
        unique_together = ("title", "org_id")

    def getOrg(self):
        orgs = Organization.objects.filter(id=self.org_id)
        if not len(orgs):
            return
        return orgs[0]

    def getChildlen(self):
        return Job.objects.filter(project_id=self.id, parent_id=None)

    def getCommits(self):
        return Commit.objects.filter(org_id=self.org_id, project_id=self.id)

    def getDeadlines(self):
        jobs = Job.objects.filter(project_id=self.id)
        deadlines = []
        for job in jobs:
            if not job.completed:
                deadlines.append(
                    {"path": job.getPath(), "deadline": job.date_deadline})
        deadlines.append(
            {"path": "/" + self.title, "deadline": self.date_deadline})
        return deadlines

    def isReady(self):
        children = self.getChildlen()
        for child in children:
            if not child.completed:
                return False
        return True
    
    def getTasks(self):
        jobs = self.getChildlen()
        tasks = []
        for job in jobs:
            tasks = tasks + job.getTasks()
        return tasks
    
    def getRecentTasks(self):
        jobs = self.getChildlen()
        tasks = []
        for job in jobs:
            tasks = tasks + job.getRecentTasks()
        return tasks

class Job(models.Model):
    title = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    date_create = models.DateTimeField(auto_now_add=True, null=False)
    date_deadline = models.DateTimeField(null=False)
    project_id = models.IntegerField(null=False)
    parent_id = models.IntegerField(null=True)
    completed = models.IntegerField(null=False)

    class Meta:
        unique_together = ("title", "parent_id", "project_id")
    
    def getProject(self):
        projects = Project.objects.filter(id=self.project_id)
        if not len(projects):
            return
        return projects[0]
    
    def isWorking(self):
        tasks = Task.objects.filter(job_id=self.id)
        if not len(tasks):
            return False
        return True

    def getPath(self):
        result = [self.title]
        parent_id = self.parent_id
        while(True):
            if(parent_id == None):
                break
            parent = Job.objects.get(id=parent_id)
            parent_id = parent.parent_id
            result.append(parent.title)
        project = Project.objects.get(id=self.project_id)
        org = Organization.objects.get(id=project.org_id)
        result.append(project.title)
        result.append("")
        return "/".join(result[::-1])

    def getCommits(self):
        commits = []
        children = self.getChildlen()
        for child in children:
            tmp_commits = child.getCommits()
            for commit in tmp_commits:
                commits.append(commit)
        commits.extend(Commit.objects.filter(parent_id=self.id))
        return commits

    def getChildlen(self):
        return Job.objects.filter(project_id=self.project_id, parent_id=self.id)

    def getDeadlines(self):
        jobs = self.getChildlen()
        deadlines = []
        for job in jobs:
            if not job.completed:
                tmp_deadlines = job.getDeadlines()
                for deadline in tmp_deadlines:
                    deadlines.append(deadline)
        if not self.completed:
            deadlines.append(
                {"deadline": self.date_deadline, "path": self.getPath()})
        return deadlines

    def isReady(self):
        children = self.getChildlen()
        for child in children:
            if child.completed == 0:
                return False
        return True
    
    def getTasks(self):
        tasks = []
        children = self.getChildlen()
        for child in children:
            tmp_tasks = child.getTasks()
            for task in tmp_tasks:
                tasks.append(task)
        tmp_tasks = Task.objects.filter(job_id=self.id)
        for task in tmp_tasks:
            tasks.append({"data": task, "job": self, "path": self.getPath(), "user": task.getUser()})
        return tasks
    
    def getRecentTasks(self):
        tasks = []
        children = self.getChildlen()
        for child in children:
            tmp_tasks = child.getTasks()
            for task in tmp_tasks:
                tasks.append(task)
        tmp_tasks = Task.objects.filter(job_id=self.id, date_update__gt=(datetime.now() - timedelta(days = 1)).strftime("%Y-%m-%d"))
        for task in tmp_tasks:
            tasks.append({"data": task, "job": self, "path": self.getPath(), "user": task.getUser()})
        return tasks

class Image(models.Model):
    user_id = models.IntegerField(null=False)
    image = models.ImageField(null=False)


class Commit(models.Model):
    date_create = models.DateTimeField(default=datetime.now)
    org_id = models.IntegerField(null=False)
    project_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=False)
    parent_id = models.IntegerField(null=True)
    body = models.CharField(max_length=255, null=False)
    path = models.CharField(max_length=255, null=False)

class Task(models.Model):
    job_id = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)
    completed = models.BooleanField(null=False, default=False)
    date_create = models.DateTimeField(default=datetime.now)
    date_update = models.DateTimeField(default=datetime.now)

    def getJob(self):
        jobs = Job.objects.filter(id=self.job_id)
        if not len(jobs):
            return
        return jobs[0]
    
    def getExpense(self):
        expenses = Expense.objects.filter(task_id=self.id)
        if not len(jobs):
            return
        return jobs[0]

    def getUser(self):
        users = User.objects.filter(id=self.user_id)
        if not len(users):
            return
        return users[0]

class Expense(models.Model):
    job_id = models.IntegerField(null=False)
    org_id = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)
    money = models.CharField(max_length=255, null=False)
    reason = models.CharField(max_length=255, null=False)
    subject = models.CharField(max_length=255, null=True)
    date_create = models.DateTimeField(default=datetime.now)

    def getUser(self):
        users = User.objects.filter(id=self.user_id)
        if not len(users):
            return
        return users[0]

    def getJob(self):
        jobs = Job.objects.filter(id=self.job_id)
        if not len(jobs):
            return
        return jobs[0]