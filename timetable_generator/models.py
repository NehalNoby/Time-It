from django.db import models
from django.contrib.auth.models import User

class RoleChoices(models.TextChoices):
    ADMIN="Admin","Admin"
    STUDENT="Student","Student"
    FACULTY="Faculty","Faculty"
    HOD="Hod","Hod"
    COLLEGE="College","College"

class SubjectTypeChoice(models.Model):
    subject_types=models.CharField(max_length=20,unique=True)
    is_fixed=models.BooleanField(default=False)

    def __str__(self):
        return self.subject_types


class Login(models.Model):
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    role=models.CharField(max_length=40,choices=RoleChoices.choices)


class College(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # Unique code for the college
    location = models.CharField(max_length=200)
    established_year = models.IntegerField()
    email = models.EmailField()
    password = models.CharField(max_length=40,default="1234")
    college_logo=models.ImageField(null=True,blank=True)

    login_id=models.OneToOneField(Login,on_delete=models.CASCADE,default="100")

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
    subject_type= models.ForeignKey(SubjectTypeChoice, on_delete=models.CASCADE,null=True,blank=True)
    sem=models.ForeignKey('Semester',on_delete=models.SET_NULL,null=True,related_name="semester_subjects")
    subject_code=models.CharField(max_length=40)


    def __str__(self):
        return f"{self.department.dept_name if self.department else ''}-{self.subject_name} -{self.subject_type} -- {self.sem.sem_name if self.sem else ''}" 

class Number_of_hour(models.Model):
    subject_type = models.ForeignKey(SubjectTypeChoice, on_delete=models.CASCADE, null=True, blank=True)
    no_of_hours_for_subject = models.IntegerField(default=0)
    semester = models.ForeignKey('Semester', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.subject_type} - {self.no_of_hours_for_subject} hours in {self.semester.sem_name if self.semester else 'No Semester'}"


class Semester(models.Model):
    sem_name = models.CharField(max_length=40)
    # department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    no_of_subjects = models.IntegerField(default=4)
    available_subjects = models.ManyToManyField('Subject', blank=True)

    def __str__(self):
        return self.sem_name


class Faculty(models.Model):
    name=models.CharField(max_length=40)
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=40)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)
    mobile=models.IntegerField(null=False)
    staff_id=models.CharField(max_length=40)
    profile_picture=models.ImageField(null=True, blank=True)
    is_hod=models.BooleanField(default=False)
    max_hours_per_day = models.IntegerField(default=6, null=True, blank=True) 
    max_hours_per_week = models.IntegerField(default=30, null=True, blank=True) 

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
    profile_picture=models.ImageField(null=True, blank=True)
    selected_subjects = models.ManyToManyField(Subject, blank=True)

    login_id = models.OneToOneField(Login, on_delete=models.CASCADE, default="100")
    def __str__(self):
        return self.name


class TimeTable(models.Model):
    year=models.IntegerField(default=2025)
    timetable_data = models.JSONField()



class AdminSettings(models.Model):
    no_of_workingdays=models.IntegerField(default=0)
    no_of_hours_in_a_day=models.IntegerField(default=0)

from django.db import models
from django.utils.timezone import now
from .models import Login  # Import Login model

class OTPVerification(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE,null=True,blank=True)  # Change User → Login
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)

    def is_valid(self):
        return (now() - self.created_at).seconds < 300  # OTP expires after 5 minutes


from django.db import models
from django.utils.timezone import now
from .models import Login  # Import Login model

class OTPVerification(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE,null=True,blank=True)  # Change User → Login
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)

    def is_valid(self):
        return (now() - self.created_at).seconds < 300  # OTP expires after 5 minutes

