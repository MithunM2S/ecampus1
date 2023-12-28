from django.contrib.auth.models import Group as Role, Permission
from rest_framework import permissions 
from modules.models import FeaturePerms
from user.models import AuthUser
import copy

methods = {
    'GET':'view',
    'POST':'add',
    'PUT':'change',
    'DELETE':'delete'
}

def get_user_role(employee):

    try:
        return Role.objects.get(id=employee.id)
    except Role.DoesNotExist:
        return None
'''this works on project/module level'''
class EmployeeHasPermission(permissions.DjangoModelPermissions):
    def __init__(self):
        self.perms_map = copy.deepcopy(self.perms_map)
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']

'''this works on view/object level'''
class EmployeeHasSpecificPermission(permissions.BasePermission):

    def has_specific_permission(self, request, permission_name):
        if permission_name in request.user.get_all_permissions():
            return True
        return False
    
    def has_permission(self, request, view):
        try:
            if request.META.get('HTTP_FEATUREPERM')=='LoginPage' and request.method == 'GET':
                return True
            module,position,point = request.META.get('HTTP_FEATUREPERM').split('_')
            require = FeaturePerms.objects.get(module__name=module,position=position,point=point if point else None,option=methods[request.method])
            if require in request.user.feature_perms.all() or request.user.is_superuser:
                return True
            return False
        except Exception as e:
            print(e)
            return False
    
    def has_object_permission(self, request, view, *args):
        try:
            module,position,point = request.META.get('HTTP_FEATUREPERM').split('_')
            require = FeaturePerms.objects.get(module__name=module,position=position,point=point if point else None,option=methods[request.method])
            if require in request.user.feature_perms.all() or request.user.is_superuser:
                return True
            return False
        except Exception as e:
            print(e)
            return False
