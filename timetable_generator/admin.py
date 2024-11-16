from django.contrib import admin
from.models import Faculty
from.models import Student
from.models import Login
from.models import Department
from.models import Semester
from.models import Subject
from.models import AdminSettings
# Register your models here.
admin.site.register(Faculty)
admin.site.register(Student)
admin.site.register(Login)
admin.site.register(Department)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(AdminSettings)