from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from.serializers import StudentSerializer,LoginSerializer,FacultySerializer,DepartmentSerializer,SemesterSerializer,SubjectSerializer
from rest_framework.response import Response
from rest_framework import status
from . models import Student
from . models import Login,Faculty,Department,Semester,Subject,SubjectTypeChoices
from itertools import chain
import json
# Create your views here.
def index(request):
    return HttpResponse("asdfghj")
    
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

#managesubjects
class subjects_reg(GenericAPIView):
    def get_serializer_class(self):
        return SubjectSerializer

    def post(self,request):

        subject_name=request.data.get('subject_name')
        department=request.data.get('department')
        staff_id=request.data.get('staff_id')
        subject_type=request.data.get('subject_type')
        subject_code=request.data.get('subject_code')

        sub_serializer=SubjectSerializer(

        data={
            'subject_name':subject_name,
            'department':department,
            'staff_id':staff_id,
            'subject_type':subject_type,
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
