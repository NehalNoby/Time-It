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


#college
   path('collegeregistration/',views.college_reg.as_view()),
   path('viewcollege/',views.view_college.as_view()),
   path('collegeupdate/<int:id>',views.update_college.as_view()),
   path('collegedelete/<int:id>',views.college_delete.as_view()),
   path('collegelogin/<int:login_id>',views.college_login.as_view()),


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

#subjecttypechoices
   path('subject_typeregister/',views.SubjectTypeChoicesRegistration.as_view()),
   path('subject_typeview/',views.ViewAllSubjectTypes.as_view()),
   path('subject_type/<int:id>/',views.SubjectTypeDetailView.as_view()),

#no.ofhours
    path('number_of_hours/register/', views.NumberOfHourRegistration.as_view(), name='number_of_hours_register'),
    path('number_of_hours/view/', views.ViewAllNumberOfHours.as_view(), name='view_all_number_of_hours'),
    path('number_of_hours/<int:id>/', views.NumberOfHourDetailView.as_view(), name='number_of_hours_detail'),
    path('number_of_hours/update/<int:id>/', views.UpdateNumberOfHour.as_view(), name='number_of_hours_update'),
    path('number_of_hours/delete/<int:id>/', views.DeleteNumberOfHour.as_view(), name='number_of_hours_delete'),



    # Existing Subject URLs
    path('subjectregistration/', views.subjects_reg.as_view()),
    path('viewsubjects/', views.view_subjects.as_view()),
    path('subjectupdate/<int:id>', views.update_subject.as_view()),
    path('subjectdelete/<int:id>', views.subject_delete.as_view()),

    # Existing Generate Timetable URL
    path('generate-timetable/', views.GenerateTimeTableAPIView.as_view()),
    path('generate-teacher-timetable/', views.TeacherTimeTableAPIView.as_view(), name='generate_teacher_timetable'),



   
    


#adminsettings
   # path('adminsettingsregistration/',views.adminsettings_reg.as_view()),
   # path('viewadminsettings/',views.view_adminsettings.as_view()),
   # path('adminsettingsupdate/<int:id>',views.update_adminsettings.as_view()),
   # path('adminsettingsdelete/<int:id>',views.adminsettings_delete.as_view()),

]
