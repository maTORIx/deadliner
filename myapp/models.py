from django.db import models
import uuid
from datetime import datetime
# Create your models here.


class User(models.Model):
    email = models.CharField(max_length=255, unique=True, null=False)
    password = models.BinaryField(null=False)
    salt = models.BinaryField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)

    def getOrganization(self):
        organizations_id = Member.objects.filter(
            user_id=self.id).values_list("organization_id", flat=True)
        return Organization.objects.filter(id=organizations_id)

    def getUUID(self):
        beforeUUID = UUID.objects.filter(user_id=self.id)
        if(len(beforeUUID)):
            beforeUUID[0].delete()
        newUUID = UUID(user_id=self.id)
        newUUID.save()
        return newUUID


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

    def getUsers(self):
        users_id = Member.objects.filter(
            organization_id=self.id).values_list("user_id", flat=True)
        return User.objects.filter(id=users_id)

    def getProjects(self):
        return Project.objects.filter(org_id=self.id)

    def getCommits(self):
        return Commit.objects.filter(org_id=self.id)

    def getDeadlines(self):
        projects = self.getProjects()
        def forMap(project):
            deadline = {
                "path" : self.name + ":/ /" + project.title,
                "deadline": project.date_deadline
            }
            return deadline
        return map(forMap, projects)


class Member(models.Model):
    organization_id = models.IntegerField(null=False)
    user_id = models.IntegerField(null=False)


class Project(models.Model):
    title = models.CharField(max_length=255, null=False)
    description = models.CharField(max_length=255, null=False)
    date_create = models.DateTimeField(auto_now_add=True, null=False)
    date_deadline = models.DateTimeField(null=False)
    org_id = models.IntegerField(null=False)
    completed = models.IntegerField(null=False)

    class Meta:
        unique_together = ("title", "org_id")

    def getChildlen(self):
        return Job.objects.filter(project_id=self.id, parent_id=None)

    def getCommits(self):
        return Commit.objects.filter(org_id=self.org_id, project_id=self.id)

    def getDeadlines(self):
        jobs = self.getChildlen()
        def forMap(job):
            deadline = {
                "path": job.getPath(),
                "deadline": job.date_deadline
            }
            return deadline
        return map(forMap, jobs)

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

    def getPath(self):
        result = [self.title]
        parent_id = self.parent_id
        while(True):
            if(parent_id == None):
                break
            parent = Jobs.objects.get(id=parent_id)
            parent_id = parent.parent_id
            result.append(parent.title)
        project = Project.objects.get(id=self.project_id)
        org = Organization.objects.get(id=project.org_id)
        result.append(project.title)
        result.append("")
        return "/".join(result[::-1])

    def getCommits(self):
        return Commit.objects.filter(parent_id=self.id, project_id=self.project_id)
    
    def getChildlen(self):
        return Job.objects.filter(project_id=self.project_id, parent_id=self.id)
    
    def getDeadlines(self):
        jobs = self.getChildlen()
        def forMap(job):
            deadline = {
                "path": job.getPath(),
                "deadline": job.date_deadline
            }
            return deadline
        return map(forMap, jobs)

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
