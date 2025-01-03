from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from.serializers import StudentSerializer,LoginSerializer,FacultySerializer,CollegeSerializer,DepartmentSerializer,SemesterSerializer,SubjectSerializer,AdminSettingsSerializer,SubjectTypeChoicesSerializer,NumberofhourSerializer
from rest_framework.response import Response
from rest_framework import status
from . models import Student
from . models import Login,Faculty,College,Department,Semester,Subject,SubjectTypeChoice,AdminSettings,Number_of_hour
from itertools import chain
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
import json
import random
from random import choice

# Create your views here.
def index(request):
    return HttpResponse("asdfghj")


class GenerateTimeTableAPIView(GenericAPIView):

    def get(self, request):
        settings = AdminSettings.objects.first()
        semesters = Semester.objects.all()

        if settings:
            working_days = settings.no_of_workingdays
            periods_per_day = settings.no_of_hours_in_a_day
        else:
            working_days = 5
            periods_per_day = 5

        teachers_subjects_map = {}
        teacher_availability = {}
        subject_hours_map = {}

        for semester in semesters:
            subjects = semester.available_subjects.all()
            teachers_subjects_map[semester.sem_name] = []
            subject_hours_map[semester.sem_name] = {}

            # Populate subject hours based on Number_of_hour
            subject_types = SubjectTypeChoice.objects.all()
            for subject_type in subject_types:
                hours_entry = Number_of_hour.objects.filter(subject_type=subject_type, semester=semester).first()
                subject_hours_map[semester.sem_name][subject_type.subject_types] = hours_entry.no_of_hours_for_subject if hours_entry else 0

            for subject in subjects:
                if subject.staff:
                    teachers_subjects_map[semester.sem_name].append({
                        "teacher": subject.staff.name,
                        "subject": subject.subject_name,
                        "subject_code": subject.subject_code,
                        "department": subject.department.dept_name if subject.department else None,
                        "staff_id": subject.staff.staff_id,
                        "type": subject.subject_type.subject_types if subject.subject_type else "Unknown",
                    })

        for semester in semesters:
            for subject in semester.available_subjects.all():
                if subject.staff:
                    staff_id = subject.staff.staff_id
                    if staff_id not in teacher_availability:
                        teacher_availability[staff_id] = {
                            f"Day {day + 1}": [False] * periods_per_day for day in range(working_days)
                        }

        timetable = self.generate_timetable(
            [semester.sem_name for semester in semesters],
            working_days,
            periods_per_day,
            teachers_subjects_map,
            teacher_availability,
            subject_hours_map
        )

        return Response({
            "data": timetable,
            "message": "Timetable generated successfully",
            "success": True
        })

    def generate_timetable(self, semesters, working_days, periods_per_day, teachers_subjects_map, teacher_availability, subject_hours_map):
        timetable = {}

        for semester in semesters:
            timetable[semester] = {}
            subject_hour_tracker = {k: 0 for k in subject_hours_map[semester]}
            total_hours_needed = sum(subject_hours_map[semester].values())

            if total_hours_needed != working_days * periods_per_day:
                raise ValueError(f"Mismatch in total hours ({total_hours_needed}) and available periods ({working_days * periods_per_day}) for semester {semester}.")

            for day in range(working_days):
                daily_schedule = []
                assigned_subjects_for_day = set()

                for period in range(periods_per_day):
                    available_subjects = [
                        s for s in teachers_subjects_map.get(semester, []) \
                        if subject_hour_tracker[s["type"]] < subject_hours_map[semester][s["type"]]
                    ]
                    assigned = False

                    while available_subjects and not assigned:
                        subject = random.choice(available_subjects)
                        teacher = subject["teacher"]
                        staff_id = subject["staff_id"]
                        subject_name = subject["subject"]
                        subject_type = subject["type"]

                        if (not teacher_availability[staff_id][f"Day {day + 1}"][period] and
                            subject_name not in assigned_subjects_for_day):

                            teacher_availability[staff_id][f"Day {day + 1}"][period] = True
                            daily_schedule.append({
                                "teacher": teacher,
                                "subject": subject_name,
                                "subject_code": subject["subject_code"],
                                "semester": semester,
                                "subject_type": subject_type,
                            })
                            assigned_subjects_for_day.add(subject_name)
                            subject_hour_tracker[subject_type] += 1
                            assigned = True
                        else:
                            available_subjects.remove(subject)

                    if not assigned:
                        fallback_subjects = [
                            s for s in teachers_subjects_map.get(semester, []) \
                            if subject_hour_tracker[s["type"]] < subject_hours_map[semester][s["type"]]
                        ]
                        for subject in fallback_subjects:
                            subject_type = subject["type"]
                            staff_id = subject["staff_id"]
                            subject_name = subject["subject"]

                            if not teacher_availability[staff_id][f"Day {day + 1}"][period]:
                                teacher_availability[staff_id][f"Day {day + 1}"][period] = True
                                daily_schedule.append({
                                    "teacher": subject["teacher"],
                                    "subject": subject_name,
                                    "subject_code": subject["subject_code"],
                                    "semester": semester,
                                    "subject_type": subject_type,
                                })
                                subject_hour_tracker[subject_type] += 1
                                assigned = True
                                break

                    if not assigned:
                        raise ValueError(f"Unable to assign subject for period {period + 1} on Day {day + 1} in semester {semester}.")

                timetable[semester][f"Day {day + 1}"] = daily_schedule

        return timetable



class TeacherTimeTableAPIView(APIView):
    
    def get(self, request, teacher_id):
        settings = AdminSettings.objects.first()
        semesters = Semester.objects.all()
        
        if settings:
            working_days = settings.no_of_workingdays
            periods_per_day = settings.no_of_hours_in_a_day
        else:
            working_days = 5
            periods_per_day = 5
        
        teacher = Faculty.objects.get(id=teacher_id)  # Fetch teacher by ID
        teacher_timetable = {}
        
        for semester in semesters:
            timetable = self.get_teacher_timetable_for_semester(teacher, semester, working_days, periods_per_day)
            if timetable:
                teacher_timetable[semester.sem_name] = timetable
        
        if not teacher_timetable:
            return Response({
                "message": "No timetable found for the teacher.",
                "success": False
            })
        
        return Response({
            "data": teacher_timetable,
            "message": "Teacher timetable retrieved successfully",
            "success": True
        })

    def get_teacher_timetable_for_semester(self, teacher, semester, working_days, periods_per_day):
        # Fetch subjects taught by the teacher in the given semester
        subjects = semester.available_subjects.filter(staff=teacher)
        if not subjects.exists():
            return None
        
        timetable = {}
        teacher_schedule = {
            f"Day {day + 1}": [None] * periods_per_day for day in range(working_days)
        }

        for day in range(working_days):
            daily_schedule = []
            assigned_subjects_for_day = set()

            for period in range(periods_per_day):
                assigned = False
                for subject in subjects:
                    if subject.subject_name not in assigned_subjects_for_day:
                        daily_schedule.append({
                            "teacher": teacher.name,
                            "subject": subject.subject_name,
                            "subject_code": subject.subject_code,
                            "semester": semester.sem_name,
                            "subject_type": subject.subject_type.subject_types if subject.subject_type else "Unknown"
                        })
                        assigned_subjects_for_day.add(subject.subject_name)
                        assigned = True
                        break

                if not assigned:
                    # No subject assigned for this period, add an empty dict
                    daily_schedule.append({})

            timetable[f"Day {day + 1}"] = daily_schedule
        
        return timetable






class student_reg(GenericAPIView):
    serializer_class=StudentSerializer

    def post(self,request):

        login_id=""
        name=request.data.get('name')
        email=request.data.get('email')
        mobile=request.data.get('mobile')
        password=request.data.get('password')
        department=request.data.get('department')
        role='Student'

        if not name or not email or not mobile or not password or not department:
            return Response({'message': 'All fields are required'},status=status.HTTP_400_BAD_REQUEST,)

        if Student.objects.filter(email=email).exists():
            return Response({'message': 'Duplicate Emails are not allowed'},status=status.HTTP_400_BAD_REQUEST,)

        elif Student.objects.filter(mobile=mobile).exists():
            return Response({'message': 'Number already found'},status=status.HTTP_400_BAD_REQUEST,)

        login_serializer=LoginSerializer(data={'email':email,'password':password,'role':role})
        print(login_serializer)
        if login_serializer.is_valid():
            l=login_serializer.save()
            login_id=l.id

        else:
            return Response({'message':'Login Failed','error':login_serializer.errors},status=status.HTTP_400_BAD_REQUEST,)

        student_serializer=self.serializer_class(

        data={
            'name':name,
            'email':email,
            'mobile':mobile,
            'password':password,
            'department':department,
            'role':role,
            'login_id':login_id})
        
        minor_subjects_id=json.loads(request.data.get("minor"))

        
        major_subjects=Subject.objects.filter(department=department,subject_type=SubjectTypeChoices.MAJOR)
        aec1_subjects=Subject.objects.filter(department=department,subject_type=SubjectTypeChoices.AEC1)
        minor_subjects=Subject.objects.filter(id__in=minor_subjects_id)
        combined_queryset=chain(major_subjects,aec1_subjects,minor_subjects)
        

        if student_serializer.is_valid():
            student=student_serializer.save()
            student.selected_subjects.add(*combined_queryset)
            student.save()
            return Response({'message':'Registration Successfull'},status=status.HTTP_200_OK,)

        else:
            return Response({'mmesage':'Registration Failed'},status=status.HTTP_400_BAD_REQUEST,)



class login_view(GenericAPIView):
    serializer_class=LoginSerializer

    def post(self,request):
        email=request.data.get('email')
        password=request.data.get('password')

        logreg=Login.objects.filter(email=email,password=password)
        if(logreg.count()>0):
            read_serializers=LoginSerializer(logreg,many=True)

            for i in read_serializers.data:
                login_id=i['id']
                role=i['role']

                register_data=Student.objects.filter(login_id=login_id).values()
                for i in register_data:
                    name=i['name']

            return Response({'data':read_serializers.data,'success':1,'message':'Logged in Successfully'},status=status.HTTP_200_OK,)
        else:
            return Response({'message':'Login Failed'},status=status.HTTP_400_BAD_REQUEST,)


class faculty_reg(GenericAPIView):
    def get_serializer_class(self):
        return FacultySerializer

    def post(self,request):

        login_id=""
        name=request.data.get('name')
        email=request.data.get('email')
        mobile=request.data.get('mobile')
        password=request.data.get('password')
        department=request.data.get('department')
        role='Faculty'

        if not name or not email or not mobile or not password or not department:
            return Response({'message': 'All fields are required'},status=status.HTTP_400_BAD_REQUEST,)

        if Faculty.objects.filter(email=email).exists():
            return Response({'message': 'Duplicate Emails are not allowed'},status=status.HTTP_400_BAD_REQUEST,)

        elif Faculty.objects.filter(mobile=mobile).exists():
            return Response({'message': 'Number already found'},status=status.HTTP_400_BAD_REQUEST,)

        login_serializer=LoginSerializer(data={'email':email,'password':password,'role':role})
        print(login_serializer)
        if login_serializer.is_valid():
            l=login_serializer.save()
            login_id=l.id

        else:
            return Response({'message':'Login Failed'},status=status.HTTP_400_BAD_REQUEST,)

        faculty_serializer=FacultySerializer(

        data={
            'name':name,
            'email':email,
            'mobile':mobile,
            'password':password,
            'department':department,
            'role':role,
            'login_id':login_id})

        if faculty_serializer.is_valid():
            faculty_serializer.save()
            return Response({'message':'Registration Successfull'},status=status.HTTP_200_OK,)

        else:
            return Response({'message':'Registration Failed'},status=status.HTTP_400_BAD_REQUEST,)



#managestudent
class view_students(GenericAPIView):
    serializer_class=StudentSerializer

    def get(self,request):
        student=Student.objects.all()
        if student.count()>0:
            serializerstd=StudentSerializer(student,many=True)
            return Response({'data':serializerstd.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)

        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class student_login(GenericAPIView):
    serializer_class=StudentSerializer

    def get(self,request,login_id):
        student=Student.objects.get(login_id=login_id)
        serializerstd=StudentSerializer(student)
        return Response(serializerstd.data) 

class update_students(GenericAPIView):
    serializer_class=StudentSerializer

    def put(self,request,login_id):
        student=Student.objects.get(login_id=login_id)
        serializerstd=StudentSerializer(instance=student,data=request.data,partial=True)

        if serializerstd.is_valid():
            serializerstd.save()
            return Response({'data':serializerstd.data,'message':'Student Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializerstd.errors,status=status.HTTP_400_BAD_REQUEST)

class student_delete(GenericAPIView):
    serializer_class=StudentSerializer

    def delete(self,request,login_id):
        student=Student.objects.get(login_id=login_id)
        student.delete()

        return Response('Student deleted successfully')


#managefaculty
class view_faculty(GenericAPIView):
    serializer_class=FacultySerializer

    def get(self,request):
        faculty=Faculty.objects.all()
        if faculty.count()>0:
            serializerfaculty=FacultySerializer(faculty,many=True)
            return Response({'data':serializerfaculty.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)

        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class faculty_login(GenericAPIView):
    serializer_class=FacultySerializer

    def get(self,request,login_id):
        faculty=Faculty.objects.get(login_id=login_id)
        serializerfaculty=FacultySerializer(faculty)
        return Response(serializerfaculty.data)   

class update_faculties(GenericAPIView):
    serializer_class=FacultySerializer

    def put(self,request,login_id):
        faculty=Faculty.objects.get(login_id=login_id)
        serializerstd=FacultySerializer(instance=faculty,data=request.data,partial=True)

        if serializerstd.is_valid():
            serializerstd.save()
            return Response({'data':serializerstd.data,'message':'Faculty Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializerstd.errors,status=status.HTTP_400_BAD_REQUEST)


class faculty_delete(GenericAPIView):
    serializer_class=FacultySerializer

    def delete(self,request,login_id):
        faculty=Faculty.objects.get(login_id=login_id)
        faculty.delete()

        return Response('Faculty deleted successfully')   


#college
class college_reg(GenericAPIView):
    def get(self, request, code):
        try:
            college = College.objects.prefetch_related('departments').get(code=code)
        except College.DoesNotExist:
            raise NotFound("College with the given code does not exist.")

        data = {
            "name": college.name,
            "location": college.location,
            "established_year": college.established_year,
            "contact_email": college.contact_email,
            "departments": [{"id": dept.id, "name": dept.dept_name} for dept in college.departments.all()],
        }
        return Response(data)

class view_college(GenericAPIView):
    serializer_class=CollegeSerializer

    def get(self,request):
        college=College.objects.all()
        if college.count()>0:
            serializercollege=CollegeSerializer(college,many=True)
            return Response({'data':serializercollege.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)

        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_college(GenericAPIView):
    serializer_class=CollegeSerializer

    def put(self,request,id):
        college=College.objects.get(pk=id)
        serializercollege=CollegeSerializer(instance=college,data=request.data,partial=True)

        if serializercollege.is_valid():
            serializercollege.save()
            return Response({'data':serializercollege.data,'message':'College Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializercollege.errors,status=status.HTTP_400_BAD_REQUEST)

class college_delete(GenericAPIView):
    serializer_class=CollegeSerializer

    def delete(self,request,id):
        college=Colleget.objects.get(pk=id)
        college.delete()

        return Response('Department deleted successfully')  


#managedepartment
class department_reg(GenericAPIView):
    def get_serializer_class(self):
        return DepartmentSerializer

    def post(self,request):

        dept_name=request.data.get('dept_name')
        dept_id=request.data.get('dept_id')

        dept_serializer=DepartmentSerializer(

        data={
            'dept_name':dept_name,
            'dept_id':dept_id,})

        if dept_serializer.is_valid():
            dept_serializer.save()
            return Response({'message':'Department added Successfull'},status=status.HTTP_200_OK,)

        else:
            return Response({'message':'Department adding Failed'},status=status.HTTP_400_BAD_REQUEST,)                  


class view_departments(GenericAPIView):
    serializer_class=DepartmentSerializer

    def get(self,request):
        department=Department.objects.all()
        if department.count()>0:
            serializerdept=DepartmentSerializer(department,many=True)
            return Response({'data':serializerdept.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)

        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_departments(GenericAPIView):
    serializer_class=DepartmentSerializer

    def put(self,request,id):
        department=Department.objects.get(pk=id)
        serializerdept=DepartmentSerializer(instance=department,data=request.data,partial=True)

        if serializerdept.is_valid():
            serializerdept.save()
            return Response({'data':serializerdept.data,'message':'Department Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializerdept.errors,status=status.HTTP_400_BAD_REQUEST)

class department_delete(GenericAPIView):
    serializer_class=DepartmentSerializer

    def delete(self,request,id):
        department=Department.objects.get(pk=id)
        department.delete()

        return Response('Department deleted successfully')  


#managesemester
class semester_reg(GenericAPIView):
    def get_serializer_class(self):
        return SemesterSerializer
    def post(self,request):
        sem_name=request.data.get('sem_name')
        sem_serializer=SemesterSerializer(
        data={
            'sem_name':sem_name,})
        if sem_serializer.is_valid():
            sem_serializer.save()
            return Response({'message':'Semester added Successfull'},status=status.HTTP_200_OK,)
        else:
            return Response({'message':'Semester adding Failed'},status=status.HTTP_400_BAD_REQUEST,)                  


class view_semesters(GenericAPIView):
    serializer_class=SemesterSerializer
    def get(self,request):
        semester=Semester.objects.all()
        if semester.count()>0:
            serializersem=SemesterSerializer(semester,many=True)
            return Response({'data':serializersem.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)
        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_semester(GenericAPIView):
    serializer_class=SemesterSerializer

    def put(self,request,id):
        semester=Semester.objects.get(pk=id)
        serializersem=SemesterSerializer(instance=semester,data=request.data,partial=True)

        if serializersem.is_valid():
            serializersem.save()
            return Response({'data':serializersem.data,'message':'Semester Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializersem.errors,status=status.HTTP_400_BAD_REQUEST)

class semester_delete(GenericAPIView):
    serializer_class=SemesterSerializer

    def delete(self,request,id):
        semester=Semester.objects.get(pk=id)
        semester.delete()
        return Response('Semester deleted successfully')


#managesubjecttypechoices
class SubjectTypeChoicesRegistration(GenericAPIView):
    serializer_class = SubjectTypeChoicesSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Subject type added successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Failed to add subject type', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ViewAllSubjectTypes(GenericAPIView):
    serializer_class = SubjectTypeChoicesSerializer

    def get(self, request):
        subject_types = SubjectTypeChoices.objects.all()
        if subject_types.exists():
            serializer = self.get_serializer(subject_types, many=True)
            return Response({'data': serializer.data, 'message': 'Subject types fetched successfully', 'success': True}, status=status.HTTP_200_OK)
        return Response({'data': [], 'message': 'No subject types available', 'success': False}, status=status.HTTP_404_NOT_FOUND)

class SubjectTypeDetailView(GenericAPIView):
    serializer_class = SubjectTypeChoicesSerializer

    def get_object(self, id):
        try:
            return SubjectTypeChoices.objects.get(pk=id)
        except SubjectTypeChoices.DoesNotExist:
            return None

    def get(self, request, id):
        subject_type = self.get_object(id)
        if subject_type:
            serializer = self.get_serializer(subject_type)
            return Response({'data': serializer.data, 'message': 'Subject type fetched successfully'}, status=status.HTTP_200_OK)
        return Response({'message': 'Subject type not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        subject_type = self.get_object(id)
        if not subject_type:
            return Response({'message': 'Subject type not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(subject_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Subject type updated successfully'}, status=status.HTTP_200_OK)
        return Response({'message': 'Failed to update subject type', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        subject_type = self.get_object(id)
        if not subject_type:
            return Response({'message': 'Subject type not found'}, status=status.HTTP_404_NOT_FOUND)

        subject_type.delete()
        return Response({'message': 'Subject type deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

#managenoofhours
class NumberOfHourRegistration(GenericAPIView):
    serializer_class = NumberofhourSerializer
    
    def post(self, request):
        subject_type = request.data.get('subject_type')
        no_of_hours_for_subject = request.data.get('no_of_hours_for_subject')
        semester = request.data.get('semester')

        # Check if the related SubjectTypeChoice and Semester exist
        subject_type_instance = SubjectTypeChoice.objects.get(id=subject_type)
        semester_instance = Semester.objects.get(id=semester)

        number_of_hour_serializer = NumberofhourSerializer(
            data={
                'subject_type': subject_type_instance,
                'no_of_hours_for_subject': no_of_hours_for_subject,
                'semester': semester_instance,
            })

        if number_of_hour_serializer.is_valid():
            number_of_hour_serializer.save()
            return Response({'message': 'Number of hours added successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Failed to add number of hours', 'errors': number_of_hour_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# View for All Number_of_hour
class ViewAllNumberOfHours(GenericAPIView):
    serializer_class = NumberofhourSerializer

    def get(self, request):
        number_of_hours = Number_of_hour.objects.all()
        if number_of_hours:
            serializer = NumberofhourSerializer(number_of_hours, many=True)
            return Response({'data': serializer.data, 'message': 'Data fetched successfully', 'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No data available'}, status=status.HTTP_404_NOT_FOUND)


# Detail View for a Single Number_of_hour
class NumberOfHourDetailView(GenericAPIView):
    serializer_class = NumberofhourSerializer

    def get(self, request, id):
        try:
            number_of_hour = Number_of_hour.objects.get(id=id)
            serializer = NumberofhourSerializer(number_of_hour)
            return Response({'data': serializer.data, 'message': 'Data fetched successfully', 'success': True}, status=status.HTTP_200_OK)
        except Number_of_hour.DoesNotExist:
            return Response({'message': 'Number of hours not found'}, status=status.HTTP_404_NOT_FOUND)


# Update Number_of_hour
class UpdateNumberOfHour(GenericAPIView):
    serializer_class = NumberofhourSerializer

    def put(self, request, id):
        try:
            number_of_hour = Number_of_hour.objects.get(id=id)
            serializer = NumberofhourSerializer(number_of_hour, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Number of hours updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Number_of_hour.DoesNotExist:
            return Response({'message': 'Number of hours not found'}, status=status.HTTP_404_NOT_FOUND)


# Delete Number_of_hour
class DeleteNumberOfHour(GenericAPIView):
    def delete(self, request, id):
        try:
            number_of_hour = Number_of_hour.objects.get(id=id)
            number_of_hour.delete()
            return Response({'message': 'Number of hours deleted successfully'}, status=status.HTTP_200_OK)
        except Number_of_hour.DoesNotExist:
            return Response({'message': 'Number of hours not found'}, status=status.HTTP_404_NOT_FOUND)

#managesubjects
class subjects_reg(GenericAPIView):
    def get_serializer_class(self):
        return SubjectSerializer

    def post(self,request):

        subject_name=request.data.get('subject_name')
        department=request.data.get('department')
        staff_id=request.data.get('staff_id')
        subject_type_id=request.data.get('type_id')
        subject_code=request.data.get('subject_code')

        sub_serializer=SubjectSerializer(

        data={
            'subject_name':subject_name,
            'department':department,
            'staff_id':staff_id,
            'subject_type':subject_type_id,
            'subject_code':subject_code,})

        if sub_serializer.is_valid():
            sub_serializer.save()
            return Response({'message':'Subject added Successfull'},status=status.HTTP_200_OK,)

        else:
            return Response({'message':'Subject adding Failed'},status=status.HTTP_400_BAD_REQUEST,)                 


class view_subjects(GenericAPIView):
    serializer_class=SubjectSerializer
    def get(self,request):
        subjects=Subjects.objects.all()
        if subjects.count()>0:
            serializersub=SubjectSerializer(subjects,many=True)
            return Response({'data':serializersub.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)
        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_subject(GenericAPIView):
    serializer_class=SubjectSerializer

    def put(self,request,id):
        subjects=Subjects.objects.get(pk=id)
        serializersub=SubjectSerializer(instance=subjects,data=request.data,partial=True)

        if serializersub.is_valid():
            serializersub.save()
            return Response({'data':serializersub.data,'message':'Subjects Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializersub.errors,status=status.HTTP_400_BAD_REQUEST)

class subject_delete(GenericAPIView):
    serializer_class=SubjectSerializer

    def delete(self,request,id):
        subjects=Subjects.objects.get(pk=id)
        subjects.delete()
        return Response('Subjects deleted successfully')

#manageadminsettings
class adminsettings_reg(GenericAPIView):
    def get_serializer_class(self):
        return AdminSettingsSerializer
    def post(self,request):
        ads_name=request.data.get('ads_name')
        ads_serializer=AdminSettingsSerializer(
        data={
            'no_of_workingdays':no_of_workingdays,
            'no_of_hours_in_a_day':no_of_hours_in_a_day,})
        if ads_serializer.is_valid():
            ads_serializer.save()
            return Response({'message':'AdminSettings added Successfull'},status=status.HTTP_200_OK,)
        else:
            return Response({'message':'AdminSettings adding Failed'},status=status.HTTP_400_BAD_REQUEST,)                  


class view_adminsettings(GenericAPIView):
    serializer_class=AdminSettingsSerializer
    def get(self,request):
        adminsettings=AdminSettings.objects.all()
        if adminsettings.count()>0:
            serializerads=AdminSettingsSerializer(adminsettings,many=True)
            return Response({'data':serializerads.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)
        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_adminsettings(GenericAPIView):
    serializer_class=AdminSettingsSerializer

    def put(self,request,id):
        adminsettings=AdminSettings.objects.get(pk=id)
        serializerads=AdminSettingsSerializer(instance=adminsettings,data=request.data,partial=True)

        if serializerads.is_valid():
            serializerads.save()
            return Response({'data':serializerads.data,'message':'AdminSettings Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializerads.errors,status=status.HTTP_400_BAD_REQUEST)

class adminsettings_delete(GenericAPIView):
    serializer_class=AdminSettingsSerializer

    def delete(self,request,id):
        adminsettings=AdminSettings.objects.get(pk=id)
        adminsettings.delete()
        return Response('AdminSettings deleted successfully')

