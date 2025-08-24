from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from.serializers import StudentSerializer,LoginSerializer,FacultySerializer,CollegeSerializer,DepartmentSerializer,SemesterSerializer,SubjectSerializer,AdminSettingsSerializer,SubjectTypeChoicesSerializer,NumberofhourSerializer,TimeTableSerializer
from rest_framework.response import Response
from rest_framework import status
from . models import Student
from . models import Login,Faculty,College,Department,Semester,Subject,SubjectTypeChoice,AdminSettings,Number_of_hour,TimeTable
from itertools import chain
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
import json
from .models import *
import random
from random import choice
from collections import defaultdict
from django.db.models import Q 

# Create your views here.
def index(request):
    return HttpResponse("asdfghj")
import random
from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
import json

class GenerateTimeTableAPIView(APIView):
    def get(self, request):
        if TimeTable.objects.exists():
            timetable = TimeTable.objects.first()
            return Response({
                "message": "Timetable already exists",
                "success": False,
                'time_table': json.loads(timetable.timetable_data)
            }, status=400)

        settings = AdminSettings.objects.first()
        semesters = Semester.objects.all()
        working_days = settings.no_of_workingdays if settings else 5
        periods_per_day = settings.no_of_hours_in_a_day if settings else 5
        total_periods_per_week = working_days * periods_per_day

        teachers_subjects_map = {}
        teacher_availability = {}
        subject_hours_map = {}

        for semester in semesters:
            sem_name = semester.sem_name
            teachers_subjects_map[sem_name] = defaultdict(list)
            subject_hours_map[sem_name] = {}
            total_allocated_hours = 0

            unique_subject_types = set()
            for subject in semester.available_subjects.all():
                if subject.subject_type:
                    unique_subject_types.add(subject.subject_type)

            for subject_type in unique_subject_types:
                hours_entry = Number_of_hour.objects.filter(
                    subject_type=subject_type, semester=semester
                ).first()
                allocated_hours = hours_entry.no_of_hours_for_subject if hours_entry else 0
                subject_hours_map[sem_name][subject_type.subject_types] = allocated_hours
                total_allocated_hours += allocated_hours

            if total_allocated_hours != total_periods_per_week:
                return Response({
                    "message": f"Mismatch in {sem_name}: Allocated {total_allocated_hours} vs required {total_periods_per_week}",
                    "success": False
                }, status=400)

            for subject in semester.available_subjects.all():
                if subject.staff:
                    subject_type = subject.subject_type.subject_types if subject.subject_type else "Unknown"
                    teachers_subjects_map[sem_name][subject_type].append({
                        "teacher": subject.staff.name,
                        "subject": subject.subject_name,
                        "subject_code": subject.subject_code,
                        "staff_id": subject.staff.staff_id,
                        "semester": sem_name,
                        "is_fixed": subject.subject_type.is_fixed if subject.subject_type else False
                    })

            for subject in semester.available_subjects.all():
                if subject.staff:
                    staff_id = subject.staff.staff_id
                    if staff_id not in teacher_availability:
                        teacher_availability[staff_id] = {
                            f"Day {day + 1}": [False] * periods_per_day for day in range(working_days)
                        }

        try:
            timetable = self.generate_timetable(
                [sem.sem_name for sem in semesters],
                working_days,
                periods_per_day,
                teachers_subjects_map,
                teacher_availability,
                subject_hours_map
            )
        except ValueError as e:
            return Response({"message": str(e), "success": False}, status=400)

        TimeTable.objects.create(timetable_data=json.dumps(timetable))
        return Response({
            "data": timetable,
            "message": "Timetable generated successfully",
            "success": True
        })

    def generate_timetable(self, semesters, working_days, periods_per_day, teachers_subjects_map, teacher_availability, subject_hours_map):
        timetable = {}
        max_classes_per_teacher_per_day = 4  # Limit for max hours per teacher per day
        
        global_teacher_schedule = {
            staff_id: {f"Day {day + 1}": [False] * periods_per_day for day in range(working_days)}
            for semester in semesters
            for subject_type, subjects in teachers_subjects_map[semester].items()
            for sub in subjects
            for staff_id in [sub['staff_id']]
        }

        for semester in semesters:
            timetable[semester] = {}
            subject_hour_tracker = {k: 0 for k in subject_hours_map[semester]}
            
            for day in range(working_days):
                daily_schedule = []
                assigned_subjects_for_day = set()
                teacher_daily_hours = defaultdict(int)  # Track periods per teacher per day

                for period in range(periods_per_day):
                    assigned = False
                    available_subjects = [
                        (stype, subs) for stype, subs in teachers_subjects_map[semester].items()
                        if subject_hour_tracker[stype] < subject_hours_map[semester][stype]
                    ]
                    random.shuffle(available_subjects)
                    available_subjects.sort(
                        key=lambda x: subject_hours_map[semester][x[0]] - subject_hour_tracker[x[0]],
                        reverse=True
                    )

                    for subject_type, subjects in available_subjects.copy():
                        subjects_in_sem = [sub for sub in subjects if sub['semester'] == semester]
                        if not subjects_in_sem:
                            continue
                        staff_ids = {sub['staff_id'] for sub in subjects_in_sem}

                        if all(
                            not teacher_availability[sid][f"Day {day + 1}"][period] and 
                            not global_teacher_schedule[sid][f"Day {day + 1}"][period] and 
                            teacher_daily_hours[sid] < max_classes_per_teacher_per_day
                            for sid in staff_ids
                        ):
                            subject_str = ", ".join({sub['subject'] for sub in subjects_in_sem})
                            for sid in staff_ids:
                                teacher_availability[sid][f"Day {day + 1}"][period] = True
                                global_teacher_schedule[sid][f"Day {day + 1}"][period] = True
                                teacher_daily_hours[sid] += 1
                            daily_schedule.append({
                                "teacher": ", ".join({sub['teacher'] for sub in subjects_in_sem}),
                                "staff_id": ", ".join({str(sub['staff_id']) for sub in subjects_in_sem}),
                                "subject": subject_str,
                                "subject_code": "-",
                                "semester": semester,
                                "subject_type": subject_type,
                                "is_fixed": subjects_in_sem[0]['is_fixed']
                            })
                            assigned_subjects_for_day.add(subject_str)
                            subject_hour_tracker[subject_type] += 1
                            assigned = True
                            break
                
                timetable[semester][f"Day {day + 1}"] = daily_schedule
        
        return timetable








from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
import json
from .models import Student, TimeTable, Subject

class GenerateTimeTableStudentAPIView(GenericAPIView):

    def get(self, request):
        student_id = request.GET.get('student_id')
        timetable_entry = TimeTable.objects.first()

        if not timetable_entry:
            return Response({'message': 'No timetable found'}, status=status.HTTP_404_NOT_FOUND)

        timetable = json.loads(timetable_entry.timetable_data)

        student = Student.objects.filter(id=student_id).first()
        if not student:
            return Response({'message': 'Student not found'}, status=status.HTTP_400_BAD_REQUEST)

        semester = student.semester.sem_name
        department = student.department

        if semester not in timetable:
            return Response({'message': 'No timetable found for this semester'}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Fetch student's selected elective subjects
        student_selected_subs = {
            sub.subject_name.strip().lower(): sub.staff.name  
            for sub in student.selected_subjects.all() if sub.staff
        }

        # ✅ Fetch only fixed subjects for the student's department & semester
        fixed_subjects = Subject.objects.filter(
            subject_type__is_fixed=True, sem=student.semester, department=department
        )
        fixed_subject_map = {sub.subject_type.subject_types: (sub.subject_name, sub.staff.name if sub.staff else "TBA") for sub in fixed_subjects}

        filtered_timetable = {}

        for day, schedule in timetable[semester].items():
            filtered_timetable[day] = []
            for item in schedule:
                new_entry = item.copy()

                if item.get('is_fixed', False):  
                    # ✅ Assign fixed subject only if it belongs to the student's department
                    subject_type = item.get('subject_type')
                    if subject_type in fixed_subject_map:
                        new_entry['subject'], new_entry['teacher'] = fixed_subject_map[subject_type]
                    else:
                        new_entry['subject'], new_entry['teacher'] = 'Free', 'N/A'

                else:  
                    # ✅ Assign elective subjects based on student's selection
                    subject_list = item['subject'].split(',') if isinstance(item['subject'], str) else [item['subject']]
                    subject_list = [sub.strip().lower() for sub in subject_list]

                    matched = False
                    for sub in subject_list:
                        if sub in student_selected_subs:
                            new_entry['subject'] = sub.capitalize()  
                            new_entry['teacher'] = student_selected_subs[sub]  
                            matched = True
                            break

                    if not matched:
                        new_entry['subject'], new_entry['teacher'] = 'Free', 'N/A'

                filtered_timetable[day].append(new_entry)

        return Response({'timetable': filtered_timetable}, status=status.HTTP_200_OK)



from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
from .models import Faculty, TimeTable

class TeacherTimeTableAPIView(GenericAPIView):

    def get(self, request):
        staff_id = request.GET.get('staff_id')  # Fetch staff_id from request

        if not staff_id:
            return Response({'message': 'Staff ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        timetable_entry = TimeTable.objects.first()
        if not timetable_entry:
            return Response({'message': 'No timetable found'}, status=status.HTTP_404_NOT_FOUND)

        timetable = json.loads(timetable_entry.timetable_data)
        faculty = get_object_or_404(Faculty, staff_id=staff_id)  # Query by staff_id

        filtered_timetable = {}

        for semester, schedule in timetable.items():
            for day, slots in schedule.items():
                for hour, item in enumerate(slots, start=1):  
                    if 'staff_id' in item and item['staff_id']:  # Ensure staff_id exists
                        staff_ids = [t.strip().lower() for t in item['staff_id'].split(",")]

                        if str(faculty.staff_id).strip().lower() in staff_ids:
                            if semester not in filtered_timetable:
                                filtered_timetable[semester] = {}
                            if day not in filtered_timetable[semester]:
                                filtered_timetable[semester][day] = []

                            item_with_hour = item.copy()
                            item_with_hour['hour'] = hour
                            item_with_hour['teacher'] = faculty.name  # Only the requested faculty name
                            item_with_hour['staff_id'] = faculty.staff_id  # Only the requested faculty staff_id

                            # Extract only the relevant subject for this faculty
                            subject_list = item['subject'].split(",")
                            staff_index = staff_ids.index(str(faculty.staff_id).strip().lower())
                            if staff_index < len(subject_list):
                                item_with_hour['subject'] = subject_list[staff_index].strip()
                            else:
                                item_with_hour['subject'] = item['subject']  # Fallback

                            filtered_timetable[semester][day].append(item_with_hour)

        if not filtered_timetable:
            return Response({'message': 'No timetable found for this staff ID'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'timetable': filtered_timetable}, status=status.HTTP_200_OK)








class student_reg(GenericAPIView):
    serializer_class = StudentSerializer

    def post(self, request):
        login_id = ""
        name = request.data.get("name")
        email = request.data.get("email")
        mobile = request.data.get("mobile")
        password = request.data.get("password")
        department = request.data.get("department")
        semester = request.data.get("semester")
        student_id = request.data.get("student_id")  # Fetch student_id from request
        role = "Student"

        # Check if student ID, email, or mobile number already exists
        if Student.objects.filter(student_id=student_id).exists():
            return Response({"message": "Student ID already registered"}, status=status.HTTP_400_BAD_REQUEST)

        if Student.objects.filter(email=email).exists():
            return Response({"message": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        if Student.objects.filter(mobile=mobile).exists():
            return Response({"message": "Mobile number already registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle login creation
        login_serializer = LoginSerializer(data={"email": email, "password": password, "role": role})
        if login_serializer.is_valid():
            login_instance = login_serializer.save()
            login_id = login_instance.id
        else:
            return Response(
                {"message": "Login Failed", "error": login_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Handle student registration
        student_serializer = self.serializer_class(
            data={
                "name": name,
                "email": email,
                "mobile": mobile,
                "password": password,
                "department": department,
                "semester": semester,
                "student_id": student_id,
                "role": role,
                "login_id": login_id,
            }
        )

        # Collect subjects
        sub_list = []

        # Query fixed subjects
        for obj in SubjectTypeChoice.objects.filter(is_fixed=True):
            fixed_subs = Subject.objects.filter(subject_type=obj, sem__id=semester)
            sub_list.append(fixed_subs)

        # Query non-fixed subjects
        for obj in Subject.objects.filter(subject_type__is_fixed=False, sem__id=semester):
            key = obj.subject_type.subject_types
            if key:
                subjects_id = json.loads(request.data.get(key)) if key in request.data else []
                query = Subject.objects.filter(id__in=subjects_id)
                sub_list.append(query)

        # Combine all subject querysets
        combined_queryset = chain(*sub_list)

        if student_serializer.is_valid():
            student = student_serializer.save()
            student.selected_subjects.add(*combined_queryset)
            student.save()
            return Response(
                {"message": "Registration Successful", "data": student_serializer.data},
                status=status.HTTP_200_OK,
            )
        else:
            login_instance.delete()  # Rollback login creation if student registration fails
            return Response(
                {"message": "Registration Failed", "error": student_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class login_view(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        logreg = Login.objects.filter(email=email, password=password).first()

        if logreg:
            read_serializer = LoginSerializer(logreg)
            login_id = logreg.id
            role = logreg.role  # Default role from Login model
            name = None
            department_id = None
            department_name = None
            student_id = None
            is_hod = False  # Default value

            # Check if the user is a Student
            student = Student.objects.filter(login_id=login_id).first()
            if student:
                name = student.name
                student_id = student.student_id
                department_id = student.department.id if student.department else None  
                department_name = student.department.dept_name if student.department else None  
                role = "Student"  

                return Response(
                    {
                        "data": {**read_serializer.data, "role": role},
                        "name": name,
                        "department_id": department_id,
                        "department_name": department_name,
                        "student_id": student_id,
                        "role": role,
                        "success": 1,
                        "message": "Logged in Successfully",
                    },
                    status=status.HTTP_200_OK,
                )

            # Check if the user is a Faculty or HOD
            faculty = Faculty.objects.filter(login_id=login_id).first()
            if faculty:
                name = faculty.name
                staff_id = faculty.staff_id
                department_id = faculty.department.id if faculty.department else None  
                department_name = faculty.department.dept_name if faculty.department else None  
                is_hod = faculty.is_hod  
                role = "HOD" if is_hod else "Faculty"  

                return Response(
                    {
                        "data": {**read_serializer.data, "role": role},
                        "name": name,
                        "staff_id": staff_id,
                        "department_id": department_id,
                        "department_name": department_name,
                        "role": role,
                        "is_hod": is_hod,
                        "success": 1,
                        "message": "Logged in Successfully",
                    },
                    status=status.HTTP_200_OK,
                )

        return Response({"message": "Login Failed"}, status=status.HTTP_400_BAD_REQUEST)



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
            return Response({'message':'regstration Failed','errors':login_serializer.errors},status=status.HTTP_400_BAD_REQUEST,)

        faculty_data=request.data.copy()
        faculty_data['role']=role
        faculty_data['login_id']=login_id
        faculty_serializer=FacultySerializer(data=faculty_data)

        if faculty_serializer.is_valid():
            faculty_serializer.save()
            return Response({'message':'Registration Successfull'},status=status.HTTP_200_OK,)
        else:
            l.delete()
            return Response({'message':'Registration Failed','errors':faculty_serializer.errors},status=status.HTTP_400_BAD_REQUEST,)



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
    serializer_class = StudentSerializer

    def put(self, request, login_id):
        try:
            # Fetch the student object
            student = Student.objects.get(login_id=login_id)
        except Student.DoesNotExist:
            return Response(
                {'message': 'Student not found', 'success': False},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Print request data for debugging
        print(request.data)

        # Deserialize the request data
        serializerstd = StudentSerializer(instance=student, data=request.data, partial=True)

        if serializerstd.is_valid():
            # Save the updated student data
            updated_student = serializerstd.save()

            # Handle selected_subjects
            selected_subjects = request.data.get('selected_subjects', [])
            if selected_subjects:
                # Clear existing selected subjects
                updated_student.selected_subjects.clear()

                # Add new selected subjects
                for subject_id in selected_subjects:
                    try:
                        subject = Subject.objects.get(id=subject_id)
                        updated_student.selected_subjects.add(subject)
                    except Subject.DoesNotExist:
                        return Response(
                            {'message': f'Subject with ID {subject_id} not found', 'success': False},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            return Response(
                {
                    'data': serializerstd.data,
                    'message': 'Student Updated Successfully',
                    'success': True,
                },
                status=status.HTTP_200_OK,
            )

        # Return serializer errors if data is invalid
        return Response(
            serializerstd.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
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
    def get_serializer_class(self):
        return CollegeSerializer

    def post(self,request):

        login_id=""
        name=request.data.get('name')
        code=request.data.get('code')
        location=request.data.get('location')
        established_year=request.data.get('established_year')
        email=request.data.get('email')
        password=request.data.get('password')
        role='College'

        if not name or not code or not location or not established_year or not email:
            return Response({'message': 'All fields are required'},status=status.HTTP_400_BAD_REQUEST,)

        if College.objects.filter(email=email).exists():
            return Response({'message': 'Duplicate Emails are not allowed'},status=status.HTTP_400_BAD_REQUEST,)

        elif College.objects.filter(code=code).exists():
            return Response({'message': 'Code already found'},status=status.HTTP_400_BAD_REQUEST,)

        login_serializer=LoginSerializer(data={'email':email,'password':password,'role':role})
        print(login_serializer)
        if login_serializer.is_valid():
            l=login_serializer.save()
            login_id=l.id

        else:
            return Response({'message':'Registration Failed','errors':login_serializer.errors},status=status.HTTP_400_BAD_REQUEST,)
        college_data=request.data.copy()
        college_data['role']=role
        college_data['login_id']=login_id
        college_serializer=CollegeSerializer(data=college_data)

        if college_serializer.is_valid():
            college_serializer.save()
            return Response({'message':'Registration Successfull'},status=status.HTTP_200_OK,)
        else:
            l.delete()
            return Response({'message':'Registration Failed','errors':college_serializer.errors},status=status.HTTP_400_BAD_REQUEST,)


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
        serializercollege=CollegeSerializer(college,data=request.data,partial=True)

        if serializercollege.is_valid():
            serializercollege.save()
            return Response({'data':serializercollege.data,'message':'College Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializercollege.errors,status=status.HTTP_400_BAD_REQUEST)

class college_delete(GenericAPIView):
    serializer_class=CollegeSerializer

    def delete(self,request,id):
        college=College.objects.get(pk=id)
        college.delete()

        return Response('Department deleted successfully')  

class college_login(GenericAPIView):
    serializer_class=CollegeSerializer

    def get(self,request,login_id):
        college=College.objects.get(login_id=login_id)
        serializercollege=CollegeSerializer(college)
        return Response(serializercollege.data)  


#managedepartment
class department_reg(GenericAPIView):
    def get_serializer_class(self):
        return DepartmentSerializer

    def post(self,request):
        dept_serializer=DepartmentSerializer(data=request.data)

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
from .models import College
from .serializers import CollegeSerializer

class ViewCollege(GenericAPIView):
    serializer_class = CollegeSerializer

    def get(self, request, code=None):
        try:
            college = College.objects.get(code=code)
            serializer = CollegeSerializer(college)
            return Response({'data': serializer.data, 'message': 'Data fetched', 'Success': True}, status=status.HTTP_200_OK)
        except College.DoesNotExist:
            return Response({'data': 'No data available', 'Success': False}, status=status.HTTP_404_NOT_FOUND)

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
from .models import SubjectTypeChoice

class ViewAllSubjectTypes(GenericAPIView):
    serializer_class = SubjectTypeChoicesSerializer

    def get(self, request):
        subject_types = SubjectTypeChoice.objects.all()
        if subject_types.exists():
            serializer = self.get_serializer(subject_types, many=True)
            return Response({'data': serializer.data, 'message': 'Subject types fetched successfully', 'success': True}, status=status.HTTP_200_OK)
        return Response({'data': [], 'message': 'No subject types available', 'success': False}, status=status.HTTP_404_NOT_FOUND)

class SubjectTypeDetailView(GenericAPIView):
    serializer_class = SubjectTypeChoicesSerializer

    def get_object(self, id):
        try:
            return SubjectTypeChoice.objects.get(pk=id)
        except SubjectTypeChoice.DoesNotExist:
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

class subjects_reg(GenericAPIView):
    def get_serializer_class(self):
        return SubjectSerializer

    def post(self, request):
        subject_name = request.data.get('subject_name')
        department_id = request.data.get('department')
        staff_id = request.data.get('staff_id')
        subject_type_id = request.data.get('type_id')
        sem_id = request.data.get('sem')
        subject_code = request.data.get('subject_code')

        print(f"Received IDs - Department: {department_id}, Staff: {staff_id}, Subject Type: {subject_type_id}, Sem: {sem_id}")

        # Check if the IDs exist before assigning
        department = Department.objects.filter(id=department_id).first() if department_id else None
        staff = Faculty.objects.filter(id=staff_id).first() if staff_id else None
        subject_type = SubjectTypeChoice.objects.filter(id=subject_type_id).first() if subject_type_id else None
        sem = Semester.objects.filter(id=sem_id).first() if sem_id else None

        if None in [department, staff, subject_type, sem]:
            return Response({
                'message': 'Invalid foreign key reference(s)',
                'invalid_keys': {
                    'department': department_id if not department else "Valid",
                    'staff': staff_id if not staff else "Valid",
                    'subject_type': subject_type_id if not subject_type else "Valid",
                    'sem': sem_id if not sem else "Valid"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        sub_serializer = SubjectSerializer(data={
            'subject_name': subject_name,
            'department': department.id if department else None,
            'staff': staff.id if staff else None,
            'subject_type': subject_type.id if subject_type else None,
            'sem': sem.id if sem else None,
            'subject_code': subject_code,
        })

        if sub_serializer.is_valid():
            sub_serializer.save()
            return Response({'message': 'Subject added Successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Subject adding Failed', 'errors': sub_serializer.errors}, 
                            status=status.HTTP_400_BAD_REQUEST)

class view_subjects(GenericAPIView):
    serializer_class=SubjectSerializer
    def get(self,request):
        subjects=Subject.objects.all()
        if subjects.count()>0:
            serializersub=SubjectSerializer(subjects,many=True)
            return Response({'data':serializersub.data,'message':'Data fetched','Success':True},status=status.HTTP_200_OK)
        else:
            return Response({'data':'No data available'},status=status.HTTP_400_BAD_REQUEST)

class update_subject(GenericAPIView):
    serializer_class=SubjectSerializer

    def put(self,request,id):
        subjects=Subject.objects.get(pk=id)
        serializersub=SubjectSerializer(instance=subjects,data=request.data,partial=True)

        if serializersub.is_valid():
            serializersub.save()
            return Response({'data':serializersub.data,'message':'Subjects Updated Successfully','success':True},status=status.HTTP_200_OK)

        return Response(serializersub.errors,status=status.HTTP_400_BAD_REQUEST)

class subject_delete(GenericAPIView):
    serializer_class=SubjectSerializer

    def delete(self,request,id):
        subjects=Subject.objects.get(pk=id)
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



from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Login
from rest_framework import generics

class faculty_filter(generics.ListAPIView):
    serializer_class = FacultySerializer

    def get_queryset(self):
        department_id = self.kwargs['department_id']
        return Faculty.objects.filter(department_id=department_id)
    
from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Login
from rest_framework import generics

class student_filter(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        department_id = self.kwargs['department_id']
        return Student.objects.filter(department_id=department_id)
    

from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
import random
from .models import OTPVerification

class RequestOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = Login.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            OTPVerification.objects.create(user=user, otp=otp)

            send_mail(
                "Password Reset OTP",
                f"Your OTP is: {otp}",
                "timeit.lissah@gmail.com",  # Your email
                [email],
                fail_silently=False,
            )

            return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User with this email not found"}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from .models import Login, OTPVerification, Student, Faculty, College

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        try:
            # Find user in the Login model
            user = Login.objects.get(email=email)
            otp_entry = OTPVerification.objects.filter(user=user, otp=otp).first()

            if otp_entry and otp_entry.is_valid():
                # Update password in Login model
                user.password = new_password
                user.save()

                # Update password in related models (Student, Faculty, College)
                try:
                    if Student.objects.filter(email=email).exists():
                        student = Student.objects.get(email=email)
                        student.password = new_password
                        student.save()
                    elif Faculty.objects.filter(email=email).exists():
                        faculty = Faculty.objects.get(email=email)
                        faculty.password = new_password
                        faculty.save()
                    elif College.objects.filter(email=email).exists():
                        college = College.objects.get(email=email)
                        college.password = new_password
                        college.save()
                except ObjectDoesNotExist:
                    pass  # If no related model is found, just proceed

                # Delete OTP entry after successful password change
                otp_entry.delete()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except Login.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        

from rest_framework import generics
from .models import Student
from .serializers import StudentSerializer

class StudentListBySemesterView(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        semester_id = self.kwargs.get('semester_id')  # Get semester ID from URL
        if semester_id:
            return Student.objects.filter(semester_id=semester_id)  # Filter students
        return Student.objects.all()  # Return all students if no filter applied


from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import Faculty, Subject, Student

class FacultyStudentsAPIView(GenericAPIView):
    """
    API for faculty to view students who have chosen subjects they are teaching.
    """

    authentication_classes = []  # Removes authentication
    permission_classes = []  # Makes API accessible to everyone

    def get(self, request):
        staff_id = request.query_params.get("staff_id")
        if not staff_id:
            return Response({"message": "staff_id is required", "success": False}, status=400)

        try:
            faculty = Faculty.objects.get(staff_id=staff_id)
        except Faculty.DoesNotExist:
            return Response({"message": "Faculty not found", "success": False}, status=404)

        subjects = Subject.objects.filter(staff=faculty)
        if not subjects.exists():
            return Response({"message": "No subjects found for this faculty", "success": False})

        result = {
            "teacher_id": staff_id,
            "teacher_name": faculty.name,
            "subjects": []
        }

        for subject in subjects:
            students = Student.objects.filter(selected_subjects=subject)
            student_data = [
                {
                    "student_id": student.student_id,
                    "name": student.name,
                    "semester": student.semester.sem_name if student.semester else "Unknown",
                    "department_id": student.department.id if student.department else None,
                    "department_name": student.department.dept_name if student.department else "Unknown"
                }
                for student in students
            ]

            subject_entry = {
                "subject_name": subject.subject_name,
                "subject_code": subject.subject_code,
                "is_fixed": subject.subject_type.is_fixed if subject.subject_type else None,
                "students": student_data
            }

            result["subjects"].append(subject_entry)

        return Response({"data": result, "success": True})



from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
from .models import Faculty, TimeTable

class HoDTimeTableAPIView(GenericAPIView):
    def get(self, request):
        # Get HoD's staff_id from request
        hod_staff_id = request.GET.get('staff_id')

        if not hod_staff_id:
            return Response({'message': 'HoD staff ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch HoD details using staff_id
        hod = get_object_or_404(Faculty, staff_id=hod_staff_id, is_hod=True)

        # Get the timetable entry
        timetable_entry = TimeTable.objects.first()
        if not timetable_entry:
            return Response({'message': 'No timetable found'}, status=status.HTTP_404_NOT_FOUND)

        timetable_data = json.loads(timetable_entry.timetable_data)

        # Fetch all faculty members in the same department
        department_faculties = Faculty.objects.filter(department=hod.department)

        hod_timetable = {}

        for faculty in department_faculties:
            faculty_timetable = {}

            for semester, schedule in timetable_data.items():
                for day, slots in schedule.items():
                    for hour, item in enumerate(slots, start=1):
                        if 'staff_id' in item and item['staff_id']:
                            staff_ids = [t.strip().lower() for t in item['staff_id'].split(",")]

                            if str(faculty.staff_id).strip().lower() in staff_ids:
                                if faculty.name not in faculty_timetable:
                                    faculty_timetable[faculty.name] = {}

                                if day not in faculty_timetable[faculty.name]:
                                    faculty_timetable[faculty.name][day] = []

                                item_with_hour = item.copy()
                                item_with_hour['hour'] = hour
                                item_with_hour['teacher'] = faculty.name
                                item_with_hour['staff_id'] = faculty.staff_id

                                # Extract only the relevant subject for this faculty
                                subject_list = item['subject'].split(",")
                                staff_index = staff_ids.index(str(faculty.staff_id).strip().lower())
                                if staff_index < len(subject_list):
                                    item_with_hour['subject'] = subject_list[staff_index].strip()
                                else:
                                    item_with_hour['subject'] = item['subject']

                                faculty_timetable[faculty.name][day].append(item_with_hour)

            hod_timetable[faculty.name] = faculty_timetable.get(faculty.name, {})

        if not hod_timetable:
            return Response({'message': 'No timetable found for this department'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'timetable': hod_timetable}, status=status.HTTP_200_OK)




from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
import json
from django.shortcuts import get_object_or_404
from .models import Faculty, Student, TimeTable, Subject

class HoDStudentTimeTableAPIView(GenericAPIView):
    def get(self, request):
        # Get HoD's staff_id from request
        hod_staff_id = request.GET.get('staff_id')

        if not hod_staff_id:
            return Response({'message': 'HoD staff ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch HoD details using staff_id
        hod = get_object_or_404(Faculty, staff_id=hod_staff_id, is_hod=True)

        # Get the timetable entry
        timetable_entry = TimeTable.objects.first()
        if not timetable_entry:
            return Response({'message': 'No timetable found'}, status=status.HTTP_404_NOT_FOUND)

        timetable_data = json.loads(timetable_entry.timetable_data)

        # Fetch all students in the same department
        students = Student.objects.filter(department=hod.department)
        
        if not students.exists():
            return Response({'message': 'No students found in this department'}, status=status.HTTP_404_NOT_FOUND)

        student_timetables = {}

        for student in students:
            semester = student.semester.sem_name if student.semester else None

            if not semester or semester not in timetable_data:
                continue  # Skip students without a valid semester or timetable data

            # ✅ Fetch student's selected elective subjects (Mapping subject name → staff)
            student_selected_subs = {
                sub.subject_name.strip().lower(): sub.staff  
                for sub in student.selected_subjects.all() if sub.staff
            }

            # ✅ Fetch fixed subjects for the student's department & semester
            fixed_subjects = Subject.objects.filter(
                subject_type__is_fixed=True, sem=student.semester, department=hod.department
            )
            fixed_subject_map = {
                sub.subject_type.subject_types: (sub.subject_name, sub.staff)  
                for sub in fixed_subjects
            }

            student_timetable = {}

            for day, schedule in timetable_data[semester].items():
                student_timetable[day] = []

                for item in schedule:
                    new_entry = item.copy()
                    teacher = None
                    staff_id = None

                    if item.get('is_fixed', False):
                        # ✅ Assign fixed subjects
                        subject_type = item.get('subject_type')
                        if subject_type in fixed_subject_map:
                            new_entry['subject'], teacher_obj = fixed_subject_map[subject_type]
                            if teacher_obj:
                                teacher = teacher_obj.name
                                staff_id = teacher_obj.staff_id
                        else:
                            new_entry['subject'] = 'Free'
                    else:
                        # ✅ Assign elective subjects based on student's selection
                        subject_list = item['subject'].split(',') if isinstance(item['subject'], str) else [item['subject']]
                        subject_list = [sub.strip().lower() for sub in subject_list]

                        for sub in subject_list:
                            if sub in student_selected_subs:
                                new_entry['subject'] = sub.capitalize()
                                teacher_obj = student_selected_subs[sub]
                                if teacher_obj:
                                    teacher = teacher_obj.name
                                    staff_id = teacher_obj.staff_id
                                break

                        if not teacher:
                            new_entry['subject'] = 'Free'

                    # ✅ Update the entry with the single teacher name
                    new_entry['teacher'] = teacher if teacher else ''
                    new_entry['staff_id'] = staff_id if staff_id else ''

                    student_timetable[day].append(new_entry)

            student_timetables[student.name] = student_timetable

        if not student_timetables:
            return Response({'message': 'No timetable data available for students'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'timetable': student_timetables}, status=status.HTTP_200_OK)
