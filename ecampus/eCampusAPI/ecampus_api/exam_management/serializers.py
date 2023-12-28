from itertools import count
import numpy as np
from rest_framework import serializers
from zmq import has
from . import models
from master import services
from django.db.models import Q, F, Sum, Count
from student import models as student_models
import pandas as pd

class SubjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SubjectType
        # fields = '__all__'
        exclude = ('created_by',)

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        # fields = '__all__'
        exclude = ('created_by',)
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['subject_type'] = instance.subject_type.name
        return response

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        # fields = '__all__'
        exclude = ('created_by',)

class ExamNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExamName
        # fields = '__all__'
        exclude = ('created_by',)

class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExamType
        # fields = '__all__'
        exclude = ('created_by',)

class ExamScheduleSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = models.ExamSchedule
        fields = '__all__'
    '''same subject with different group can be created'''
    def validate(self, validated_data):
        request = self.context.get('request')
        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')
        if request.method != "PUT":
            records = models.ExamSchedule.objects.filter(
                ((Q(start_time__lte=start_time) & Q(end_time__gte=start_time)) |
                (Q(start_time__lte=end_time) & Q(end_time__gte=end_time))),
                # subject = validated_data.get('subject'),
                group = validated_data.get('group'),
                section = validated_data.get('section'),
                class_name = validated_data.get('class_name'),
                exam_name = validated_data.get('exam_name'),
                exam_type = validated_data.get('exam_type'),
                academic_year = validated_data.get('academic_year'),
                scheduled_date = validated_data.get('scheduled_date')
            )
        else:
            records = models.ExamSchedule.objects.filter(
                ~Q(id = self.instance.id),
                ((Q(start_time__lte=start_time) & Q(end_time__gte=start_time)) |
                (Q(start_time__lte=end_time) & Q(end_time__gte=end_time))),
                # subject = validated_data.get('subject'),
                group = validated_data.get('group'),
                section = validated_data.get('section'),
                class_name = validated_data.get('class_name'),
                exam_name = validated_data.get('exam_name'),
                exam_type = validated_data.get('exam_type'),
                academic_year = validated_data.get('academic_year'),
                scheduled_date = validated_data.get('scheduled_date')
            )

        if records:
            raise serializers.ValidationError({'Exam': "An Exam was Scheduled with same date and time."})
        return validated_data

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['class_name'] = {'id':instance.class_name.id, 'class_name':instance.class_name.class_name}
        response['section'] = {'id':instance.section.id, 'section':instance.section.section_name}
        response['exam_name'] = {'id':instance.exam_name.id, 'exam_name':instance.exam_name.name}
        response['exam_type'] = {'id':instance.exam_type.id, 'exam_type':instance.exam_type.type}
        response['group'] = {'id':instance.group.id, 'group':instance.group.name}
        response['subject'] = {'id':instance.subject.id, 'subject':instance.subject.name}
        return response

class GradingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Grading
        fields = ('id','from_min','to_max','symbol','name')
    
    def validate(self, validated_data):
        from_min = validated_data.get("from_min")
        to_max = validated_data.get("to_max")
        request = self.context.get('request')
        if from_min > to_max:
            raise serializers.ValidationError({"Grade": "Invalid Grade Range !"})
        elif request.method != "PUT":
            grades = models.Grading.objects.filter(
                (Q(from_min__lte=from_min) & Q(to_max__gte=from_min)) |
                (Q(from_min__lte=to_max) & Q(to_max__gte=to_max)),
            ).exists()
        else:
            grades = models.Grading.objects.filter(
                (Q(from_min__lte=from_min) & Q(to_max__gte=from_min)) |
                (Q(from_min__lte=to_max) & Q(to_max__gte=to_max)),
                ~Q(id = self.instance.id)
            ).exists()
        if grades:
            raise serializers.ValidationError({'Grade': "Should not be in already created ranges !"})
        return validated_data

class RecordMarksSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StudentMarks
        fields = '__all__'
    
    def validate(self, validated_data):
        records = models.StudentMarks.objects.filter(
            exam_schedule = validated_data.get('exam_schedule'),
            student = validated_data.get('student'),
            editable = False
        ).exists()

        if records:
            raise serializers.ValidationError({validated_data.get('student').student_id:'Results Generated.'})
        return validated_data

class ResultReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResultAprove
        fields = '__all__'
    
    def validate(self, validated_data):
        request = self.context.get('request')
        if request.method == 'PUT' and self.instance.approved:
            raise serializers.ValidationError({'Results':'Results already Generated.'})
        return validated_data

class ExamAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExamAttendance
        fields = '__all__'