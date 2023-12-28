from django.contrib.auth.models import Group as Role, Permission
from django.db.models import fields
from django.db.models.base import Model
from django.db.models.query_utils import FilteredRelation
from rest_framework import serializers
from .models import *
from django.conf import settings
from api_authentication.views import is_superuser_id
from master import services as master_services_emp
from user.models import AuthUser
from django.contrib.auth.hashers import check_password



class EmployeeRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions', 'department']
        # extra_kwargs = {'permissions': {'required': False}}


class ListPermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = ['id', 'name']


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ['id', 'designation']
    
    def validate(self,validated_data):
        is_there = Role.objects.filter(name=validated_data.get('designation'))
        if is_there:
            raise serializers.ValidationError({'designation': "Already created."})
        
        role, created = Role.objects.get_or_create(name=validated_data.get('designation'))
        return validated_data


class EmployeeProfileSerializer(serializers.ModelSerializer):
    caste = serializers.SerializerMethodField('get_caste_name')
    department = serializers.SerializerMethodField('get_department_name')
    caste_category = serializers.SerializerMethodField('get_caste_cat_name')
    designation = serializers.SerializerMethodField('get_designation_name')
    gender = serializers.SerializerMethodField('get_gender')
    modules = serializers.SerializerMethodField('get_modules')


    def get_department_name(self, obj):
        if obj:
            return {'id':obj.department.id, 'name':obj.department.name}

    def get_caste_name(self, obj):
        if obj:
            return {'id':obj.caste.id, 'name':obj.caste.caste} if obj.caste else {'id':obj.caste, 'name':obj.caste}

    def get_caste_cat_name(self, obj):
        if obj:
            return {'id':obj.caste_category.id, 'name':obj.caste_category.category} if obj.caste_category else {'id':obj.caste_category, 'name':obj.caste_category}

    def get_designation_name(self, obj):
        if obj:
            return {'id':obj.designation.id, 'name':obj.designation.designation}

    def get_gender(self, obj):
        if obj:
            return {'id':obj.gender.id, 'name':obj.gender.gender}
    
    def get_modules(self, obj):
        modules = []
        if obj.login_access:
            user_modules = AuthUser.objects.values('modules').filter(username=obj.employee_name,email=obj.email)
            if user_modules:
                modules = [int(x) for x in user_modules[0]['modules'].split(',')]
        return modules

    class Meta:
        model = EmployeeDetails
        fields = [
            'id',
            'employee_name',
            'employee_photo',
            'dob',
            'qualification',
            'caste',
            'caste_category',
            'martial_status',
            'father_husband_name',
            'father_husband_number',
            'present_address',
            'permanent_address',
            'contact_number',
            'email',
            'gender',
            'blood_group',
            'date_of_join',
            'work_experience',
            'class_group',
            'class_teacher',
            'department',
            'designation',
            'active',
            'login_access',
            'modules']


class EmployeePostSerizlizer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetails
        fields = '__all__'

    def validate(self,validated_data):
        is_there = EmployeeDetails.objects.filter(email=validated_data['email']).exists()
        if is_there:
            raise serializers.ValidationError({'Fields Error':'There is an Employee with same contact number or email'})
        if validated_data['login_access'] == True:
            request = self.context.get('request')
            # create user
            user,create = AuthUser.objects.get_or_create(email=validated_data['email'],
                                                         username=validated_data['employee_name'].replace(' ',''),
                                                         modules=request.data['modules'])
            if create:
                user.set_password(request.data['password'])
                user.save()
                # user.feature_perms.set(request.data.get('permissions',))
        return validated_data


class EmployeeUpdateSerizlizer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetails
        fields = '__all__'

    def validate(self,validated_data):
        # is_there = EmployeeDetails.objects.filter(contact_number=validated_data['contact_number'],email=validated_data['email']).exists()
        request = self.context.get('request')
        s_u_name = validated_data['employee_name'].replace(' ','') if validated_data['employee_name'] == self.instance.employee_name else self.instance.employee_name.replace(' ','')
        try:
            user = AuthUser.objects.get(username=s_u_name, email=self.instance.email)
            user.username = validated_data['employee_name'].replace(' ','')
            user.is_active=validated_data['login_access']
            user.email = validated_data['email']
            if validated_data['login_access']:
                user.modules = request.data['modules']
                user.feature_perms.set(user.feature_perms.filter(module_id__in=request.data['modules'].split(',')+[15]))
            user.save()
        except AuthUser.DoesNotExist:
            if validated_data['login_access']:
                user,create = AuthUser.objects.get_or_create(email=validated_data['email'],
                                                         username=validated_data['employee_name'].replace(' ',''),
                                                         modules=request.data['modules'],
                                                         is_active=True)
                if create:
                    password = request.data['password'] if request.data.get('password', None) else f"{user.username[-4:].capitalize()}@{validated_data['dob'].year}"
                    user.set_password(password)
                user.save()
        
        return validated_data


class EmployeeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetails
        fields = ['id', 'employee_name', 'class_group']



class EmployeeAttendaceSerializer(serializers.Serializer):
    
    data = serializers.ListField(required=False)


class EmployeeAttendaceSerializerGet(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'


class EmployeeInactiveSerializer(serializers.Serializer):
    employee_name = serializers.CharField(required=False)


class EmpoyeeProfileGet(serializers.ModelSerializer):

    class Meta:
        model = EmployeeDetails
        fields = '__all__'


class EmpAttendanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attendance()
        fields = '__all__'


    
class EmpModDepartmentSerizlizer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = ['id', 'name']