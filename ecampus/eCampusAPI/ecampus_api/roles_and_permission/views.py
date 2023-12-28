from django.shortcuts import render
from django.contrib.auth.models import Group as Role, Permission
from modules.models import FeaturePerms
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from . import serializers
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from api_authentication import permissions as api_permissions
from employee.permissions import EmployeeHasPermission, EmployeeHasSpecificPermission
from django.conf import settings
from employee.models import Department
from modules.models import Module
from django.db.models import F, Q
from user.models import AuthUser

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = serializers.DepartmentSerizlizer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = serializers.RoleSerializer

class ListPermission(APIView):
    permission_classes = [EmployeeHasSpecificPermission,]#IsAuthenticated, api_permissions.HasOrganizationAPIKey]

    def get(self, request):
        if 1==1: # self.has_specific_permission(request, 'auth.view_permission') or request.user.is_superuser:
        #     queryset = Permission.objects.values('id', 'name').filter(content_type__app_label__in=settings.PERMISSION_APP_NAMES, content_type__model__in=settings.PERMISSION_MODEL_NAMES)
            user = AuthUser.objects.filter(id=request.query_params.get('user',None))[0]
            filter_module = request.query_params.get('module','')
            # user.
            queryset = FeaturePerms.objects.values('id',
                                                  menu=F('position'),
                                                  permission_name=F('option'),
                                                  feature=F('point'),
                                                  moduleName=F('module__name'),
                                                  ).filter(
                                                      Q(module_id__in=user.modules.split(',')) | Q(module_id=15),) # Module.objects.values('name')
            # print(user.has_perm(f"student.{queryset[0]['codename']}"),queryset[0]['codename'])

            module = ''
            position = ''
            point = ''
            op = []

            for i in queryset:
                if module != i['moduleName']:
                    op.append({
                        i['moduleName']:[]
                        })
                    module = i['moduleName']
                if position != i['menu']:
                    op[-1][module].append({i['menu']:[]})
                    position = i['menu']
                if point != i['feature'] and i['feature'] != None:
                    op[-1][module][-1][position].append({i['feature']:[]})
                    point = i['feature']
                if i['feature'] == None:
                    op[-1][module][-1][position].append({
                        'id':i['id'],
                        'permission_name':i['permission_name'],
                        'status': user.feature_perms.filter(id=i['id']).exists()
                    })
                else:
                    op[-1][module][-1][position][-1][point].append({
                        'id':i['id'],
                        'permission_name':i['permission_name'],
                        'status': user.feature_perms.filter(id=i['id']).exists()
                    })
            return Response(op)
        else:
            queryset = {'details':'You don not have permission to perform this action'}
            return Response(queryset)
