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
    BDC="bdc","bdc"


class Login(models.Model):
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    role=models.CharField(max_length=40,choices=RoleChoices.choices)


class College(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # Unique code for the college
    location = models.CharField(max_length=200)
    established_year = models.IntegerField()
    contact_email = models.EmailField()

    def __str__(self):
        return self.name


class Department(models.Model):
    dept_name = models.CharField(max_length=40)
    dept_id = models.CharField(max_length=40)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="departments",null=True,blank=True)

    def __str__(self):
        return self.dept_name

class Subject(models.Model):
    subject_name=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    staff=models.ForeignKey('Faculty',on_delete=models.SET_NULL,null=True)
    subject_type=models.CharField(max_length=40,choices=SubjectTypeChoices.choices)
    subject_code=models.CharField(max_length=40)
    is_fixed=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.department.dept_name if self.department else ''}-{self.subject_name} -{self.subject_type}" 


    
    

class Semester(models.Model):
    sem_name=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    no_of_subjects=models.IntegerField(default=4)
    available_subjects=models.ManyToManyField('Subject',blank=True)
    no_of_hours_for_major=models.IntegerField(default=0)
    no_of_hours_for_minor1=models.IntegerField(default=0)
    no_of_hours_for_minor2=models.IntegerField(default=0)
    no_of_hours_for_aec1=models.IntegerField(default=0)
    no_of_hours_for_aec2=models.IntegerField(default=0)
    no_of_hours_for_mdc=models.IntegerField(default=0)

    def __str__(self):
        return self.sem_name


class Faculty(models.Model):
    name=models.CharField(max_length=40)
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    mobile=models.IntegerField(null=False)
    staff_id=models.CharField(max_length=40)
    is_hod=models.BooleanField(default=False)

    login_id=models.OneToOneField(Login,on_delete=models.CASCADE,default="100")

    def __str__(self):
        return self.name
    



class Student(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField(unique=True)
    semester = models.ForeignKey('Semester', on_delete=models.SET_NULL, null=True)
    password = models.CharField(max_length=40)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    mobile = models.IntegerField(null=False)
    selected_subjects = models.ManyToManyField(Subject, blank=True)

    login_id = models.OneToOneField(Login, on_delete=models.CASCADE, default="100")
    def __str__(self):
        return self.name




class AdminSettings(models.Model):
    no_of_workingdays=models.IntegerField(default=0)
    no_of_hours_in_a_day=models.IntegerField(default=0)





