from rest_framework import serializers
from .models import Module

class ModuleSerializer(serializers.ModelSerializer):

    accessable = serializers.SerializerMethodField('get_perm')

    def get_perm(self, obj):
        user = self.context.get('request')
        user = user.user
        if user.modules != '0':
            ml = [int(x) for x in user.modules.split(',')]
            return obj.id in ml
        return True

    class Meta:
        model = Module
        fields = ['id', 'name', 'color', 'icon', 'rank', 'accessable']