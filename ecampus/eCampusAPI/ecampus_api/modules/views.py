from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import ModuleSerializer
from .models import Module, FeaturePerms
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAdminUser
from api_authentication.permissions import HasOrganizationAPIKey, IsSuperUser
from rest_framework import generics
from employee.permissions import EmployeeHasSpecificPermission
from django.db import connection

def direct_operations():

    '''this will create the main dashboard'''
    try:
        if not Module.objects.filter(name='Main Dashboard'):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO modules_module VALUES (15,'Main Dashboard','Main Dashboard','main-dashboard',15,'Red','http://52.66.185.61/static/modules/icon',0,NULL);
                    """
                    )
    except Exception as e:
        print(e)
    
    something = Module.objects.all()

    '''this is to change the managment to management and course management to exam management'''
    for i in something:
        if 'Managment' in i.name:
            i.name = i.name[:-4] + 'ement'
        
        if i.name == 'Attendence':
            i.name = 'Attendance'
        
        if i.name == 'Course-Management':
            i.name = 'Exam-Management'
        
        i.save()

    '''this is to create perms'''
    methods = ['add','change','delete','view']

    perms = {
        'Main Dashboard':{
            'Main Dashboard':[],
            'Institution Profile':[]
        },
        'Student':{
            'Dashboard':[],
            'Masters':[
                'Add Academic Year',
                'Add Existing Student',
                'Profile',
                'Caste Category',
                'Caste',
                'Gender',
                'Quota',
                'Religion',
                'Mother Tongue'
            ],
            'Settings':[
                'Import',
                'Export',
                'Activate/Deactivate Student',
                'Student Registration Setting'
            ],
            'Actions':[],
            'Reports':[
                'Classwise Students List'
            ]},
        'Attendance':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Fee':{
            'Dashboard':[],
            'Masters':[
                'Fee Category',
                'Fee Type',
                'Fee to class',
                'Fee to Student',
                'Payment Mode'
            ],
            'Settings':[
                'Fee Bill Setting'
            ],
            'Actions':[
                'Fee Collection',
                'Assign Fee Concession',
                'Assign Old Fee'
            ],
            'Reports':[
                'Daily Fee Collections',
                'Fee Collections & Balance',
                'Fee Due Report',
                'Re Print Bill',
                'Bill to Bill'
            ]},
        'Transportation':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Employee':{
            'Dashboard':[],
            'Masters':[
                'Profile',
                'Department',
                'Designation'
            ],
            'Settings':[
                'Modify Permissions',
                'Update Password'
            ],
            'Actions':[
                'Attendance'
            ],
            'Reports':[]},
        'Exam':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Media':{
            'Dashboard':[],
            'Masters':[
                'SMS Group'
            ],
            'Settings':[],
            'Actions':[
                'Send SMS',
                'Send SMS By Mobile Numbers',
                'Send SMS By Group',
                'Whatsapp',
                'Voice',
                'Video'
            ],
            'Reports':[]},
        'Exam-Management':{
            'Dashboard':[],
            'Masters':[
                'Add Subject',
                'Add Group',
                'Add Exam Name',
                'Add Exam Mark Type',
                'Exam Scheduling',
                'Add Grading System'
            ],
            'Settings':[
                'Hall Ticked',
                'Mark Card'
            ],
            'Actions':[
                'Exam Attendance',
                'Exam Marks Entry',
                'Remarks',
                'Result Generation'
            ],
            'Reports':[
                'Hall Ticket Generation',
                'Marks Card',
                'Consolidate Marks Card',
                'Consolidate Marks Sheet',
                'Graphical Analysis'
            ]},
        'Certificates':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Visitors-Management':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Profile':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Room Management':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]},
        'Pre-Admission':{
            'Dashboard':[],
            'Masters':[],
            'Settings':[],
            'Actions':[],
            'Reports':[]}
    }

    count = FeaturePerms.objects.count()

    for module in something:
        m = perms.get(module.name)

        if not FeaturePerms.objects.filter(module=module.id):
            try:
                with connection.cursor() as cursor:
                    '''id,position,point,option,module_id'''
                    for position in m:
                        if m[position]:
                            for point in m[position]:
                                for method in methods:
                                    cursor.execute(
                                        f"""
                                        INSERT INTO modules_featureperms VALUES ({count+1},'{position}','{point}','{method}',{module.id});
                                        """
                                    )
                                    count+=1
                        else:
                            for method in methods:
                                cursor.execute(
                                    f"""
                                    INSERT INTO modules_featureperms VALUES ({count+1},'{position}',NULL,'{method}',{module.id});
                                    """
                                )
                                count+=1
                
            except Exception as e:
                print(e,module.name)
    
    print(f"{count} permissions were created ..")

class DashboardModules(generics.ListAPIView):
    serializer_class = ModuleSerializer
    queryset = Module.objects.filter(is_active=True)

    # direct_operations()


class MasterModules(generics.ListAPIView):
    serializer_class = ModuleSerializer
    queryset = Module.objects.all()
