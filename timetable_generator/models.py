from django.db import models
from django.contrib.auth.models import User

class RoleChoices(models.TextChoices):
    ADMIN="Admin","Admin"
    STUDENT="Student","Student"
    FACULTY="Faculty","Faculty"
    HOD="Hod","Hod"

class SubjectTypeChoices(models.TextChoices):
    MAJOR="Major","Major"
    MINOR1="Minor1","Minor1"
    MINOR2="Minor2","Minor2"
    AEC1="Aec1","Aec1"
    AEC2="Aec2","Aec2"
    MDC="Mdc","Mdc"


class Login(models.Model):
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    role=models.CharField(max_length=40,choices=RoleChoices.choices)

class Department(models.Model):
    dept_name=models.CharField(max_length=40)
    dept_id=models.CharField(max_length=40)

    def __str__(self):
        return self.dept_name

class Faculty(models.Model):
    name=models.CharField(max_length=40)
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    mobile=models.IntegerField(null=False)
    staff_id=models.CharField(max_length=40)
    is_hod=models.BooleanField(default=False)

    def __str__(self):
        return self.name
    login_id=models.OneToOneField(Login,on_delete=models.CASCADE,default="100")


class Subject(models.Model):
    subject_name=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    staff=models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True)
    subject_type=models.CharField(max_length=40,choices=SubjectTypeChoices.choices)
    subject_code=models.CharField(max_length=40)

    def __str__(self):
        return f"{self.department.dept_name}-{self.subject_name} -{self.subject_type}" 

class Student(models.Model):
    name=models.CharField(max_length=40)
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    mobile=models.IntegerField(null=False)
    selected_subjects=models.ManyToManyField(Subject,blank=True)
    def __str__(self):
        return self.name

    login_id=models.OneToOneField(Login,on_delete=models.CASCADE,default="100")







class Semester(models.Model):
    sem_name=models.CharField(max_length=40)

    def __str__(self):
        return self.sem_name

