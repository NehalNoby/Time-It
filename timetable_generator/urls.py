from django.urls import path,include
from.import views
urlpatterns = [
   path('',views.index),

#login
   path('login/',views.login_view.as_view()),

#student
   path('studentregistration/',views.student_reg.as_view()),
   path('viewstudents/',views.view_students.as_view()),
   path('studentlogin/<int:login_id>',views.student_login.as_view()),
   path('studentupdate/<int:login_id>',views.update_students.as_view()),
   path('studentdelete/<int:login_id>',views.student_delete.as_view()),

#faculty
   path('facultyregistration/',views.faculty_reg.as_view()),
   path('viewfaculties/',views.view_faculty.as_view()),
   path('facultylogin/<int:login_id>',views.faculty_login.as_view()),
   path('facultyupdate/<int:login_id>',views.update_faculties.as_view()),
   path('facultydelete/<int:login_id>',views.faculty_delete.as_view()),

#department
   path('departmentregistration/',views.department_reg.as_view()),
   path('viewdepartments/',views.view_departments.as_view()),
   path('departmentupdate/<int:id>',views.update_departments.as_view()),
   path('departmentdelete/<int:id>',views.department_delete.as_view()),

#semester
   path('semesterregistration/',views.semester_reg.as_view()),
   path('viewsemesters/',views.view_semesters.as_view()),
   path('semesterupdate/<int:id>',views.update_semester.as_view()),
   path('semesterdelete/<int:id>',views.semester_delete.as_view()),

#subject
   path('subjectregistration/',views.subjects_reg.as_view()),
   path('viewsubjects/',views.view_subjects.as_view()),
   path('subjectupdate/<int:id>',views.update_subject.as_view()),
   path('subjectdelete/<int:id>',views.subject_delete.as_view()),
   path('generate-timetable/',views.GenerateTimeTableAPIView.as_view()),

#adminsettings
   # path('adminsettingsregistration/',views.adminsettings_reg.as_view()),
   # path('viewadminsettings/',views.view_adminsettings.as_view()),
   # path('adminsettingsupdate/<int:id>',views.update_adminsettings.as_view()),
   # path('adminsettingsdelete/<int:id>',views.adminsettings_delete.as_view()),

]
