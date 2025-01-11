from django.contrib import admin
from.models import Faculty
from.models import Student
from.models import Login
from.models import College
from.models import Department
from.models import Semester
from.models import Subject
from.models import AdminSettings
from.models import SubjectTypeChoice
from.models import Number_of_hour
from.models import Schedule
# Register your models here.
admin.site.register(Faculty)
admin.site.register(Student)
admin.site.register(Login)
admin.site.register(College)
admin.site.register(Department)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(AdminSettings)
admin.site.register(SubjectTypeChoice)
admin.site.register(Number_of_hour)
admin.site.register(Schedule)