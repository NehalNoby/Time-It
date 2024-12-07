from rest_framework import serializers
from .models import Student,Login,Faculty,Department,Semester,Subject,AdminSettings,College


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Student
        fields='__all__'
        
class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Login
        fields='__all__'

class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model=Faculty
        fields='__all__'

class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model=College
        fields='__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Department
        fields='__all__'

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model=Semester
        fields='__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Subject
        fields='__all__'

class AdminSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=AdminSettings
        fields='__all__'
