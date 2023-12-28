from . import models
from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from api_authentication.permissions import HasOrganizationAPIKey
from rest_framework.permissions import AllowAny, IsAuthenticated
from employee.permissions import EmployeeHasPermission, EmployeeHasSpecificPermission
from django.db.models import Q, F, Sum, Count, Max
from student.models import Profile,ParentDetails
from student import serializers as student_serializer
from rest_framework import response
from master import services
from student import services as student_services
from django_filters.rest_framework import DjangoFilterBackend
from fee import services as fee_services
from rest_framework import status
from datetime import datetime
from openpyxl import Workbook
import os
from base import services as base_services
from master.models import GroupConcat

from . import serializers
from base.pagination import APIPagination  # Import your custom pagination class
from rest_framework.response import Response  # Import Response

def get_marks_value(marks):
    try:
        return float(marks)
    except:
        return 0


class ExamManGenericMixinViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.UpdateModelMixin,
                                viewsets.GenericViewSet):
                                pass

class SubjectTypeViewSet(ExamManGenericMixinViewSet):
    queryset = models.SubjectType.objects.all()
    serializer_class = serializers.SubjectTypeSerializer
    http_method_names = ['get', 'post', 'update']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class SubjectViewSet(ExamManGenericMixinViewSet):
    
    queryset = models.Subject.objects.all()
    serializer_class = serializers.SubjectSerializer
    http_method_names = ['get', 'post', 'put']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class GroupViewSet(ExamManGenericMixinViewSet):
    
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    http_method_names = ['get', 'post', 'put']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class ExamNameViewSet(ExamManGenericMixinViewSet):
    
    queryset = models.ExamName.objects.all()
    serializer_class = serializers.ExamNameSerializer
    http_method_names = ['get', 'post', 'put']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class ExamTypeViewSet(ExamManGenericMixinViewSet):
    
    queryset = models.ExamType.objects.all()
    serializer_class = serializers.ExamTypeSerializer
    http_method_names = ['get', 'post', 'put']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class ExamScheduling(ExamManGenericMixinViewSet):
    queryset = models.ExamSchedule.objects.all()
    serializer_class = serializers.ExamScheduleSerializer
    http_method_names = ['get', 'post', 'put']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'academic_year',
        'class_name',
        'section',
        'exam_name',
    ]

    def get_serializer(self, *args, **kwargs):
      if "data" in kwargs:
        request_data = kwargs["data"]
        if isinstance(request_data, list):
            kwargs["many"] = True

      return super(ExamScheduling, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = self.request.user.id
        serializer = self.get_serializer(data=request.data)
        for i in request.data:
            i['created_by'] = user
        records = models.ExamSchedule.objects.filter(
                subject = request.data[0].get('subject'),
                group = request.data[0].get('group'),
                section = request.data[0].get('section'),
                class_name = request.data[0].get('class_name'),
                exam_name = request.data[0].get('exam_name'),
                exam_type = request.data[0].get('exam_type'),
                academic_year = request.data[0].get('academic_year'),
                scheduled_date = request.data[0].get('scheduled_date')
            ).exists()
        if records:
            return Response({'detail': 'An Exam was Scheduled with same subject !'}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return response.Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=user) # specify user
        
        need = models.ResultAprove.objects.filter(
            exam_name = serializer.validated_data[0]['exam_name'],
            class_name = serializer.validated_data[0]['class_name'],
            section = serializer.validated_data[0]['section'],
            group = serializer.validated_data[0]['group'],
            academic_year = serializer.validated_data[0]['academic_year'],
        )

        if not need:
            models.ResultAprove.objects.create(
            exam_name = serializer.validated_data[0]['exam_name'],
            class_name = serializer.validated_data[0]['class_name'],
            section = serializer.validated_data[0]['section'],
            group = serializer.validated_data[0]['group'],
            academic_year = serializer.validated_data[0]['academic_year'],
            created_by = user
            )
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        custom_op = []

        if not response.data['results']:
            return Response({'detail': 'NO Exams Scheduled.'}, status=status.HTTP_404_NOT_FOUND)

        for rec in response.data['results']:
            custom_op = generate_scheduled(0,[],rec,custom_op)
        response.data['results'] = custom_op

        return response
    
    def update(self, request, *args, **kwargs):
        user = request.user.id
        partial = kwargs.pop('partial', False)

        # Assuming the request data contains a list of dictionaries,
        # each representing the data to update for different objects
        serialized_data = []
        for data in request.data:
            instance = models.ExamSchedule.objects.get(id=data['id'])
            data['created_by'] = user
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            serialized_data.append(serializer.data)
        return Response(serialized_data)

# need to implement the group and exam totals ...
def generate_scheduled(x_i,i_list,rec,custom_op):
    x_list = ['exam_name','group','subject','exam_type']

    if x_list[x_i] == 'exam_name':
        if any(rec['exam_name']['exam_name'] in x for x in custom_op):
            ex_i = [i for i,o in enumerate(custom_op) if rec['exam_name']['exam_name'] in o][0]
            i_list.append(ex_i)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
        else:
            custom_op.append({rec['exam_name']['exam_name']:[]})
            i_list.append(len(custom_op)-1)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
    if x_list[x_i] == 'group':
        if any(rec['group']['group'] in x for x in custom_op[i_list[x_i-1]][rec['exam_name']['exam_name']]):
            grp_i = [i for i,o in enumerate(custom_op[i_list[x_i-1]][rec['exam_name']['exam_name']]) if rec['group']['group'] in o][0]
            i_list.append(grp_i)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
        else:
            custom_op[i_list[x_i-1]][rec['exam_name']['exam_name']].append({rec['group']['group']:[]})
            i_list.append(len(custom_op[i_list[x_i-1]][rec['exam_name']['exam_name']])-1)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
    if x_list[x_i] == 'subject':
        if any(rec['subject']['subject'] in x for x in custom_op[i_list[x_i-2]][rec['exam_name']['exam_name']][i_list[x_i-1]][rec['group']['group']]):
            sub_i = [i for i,o in enumerate(custom_op[i_list[x_i-2]][rec['exam_name']['exam_name']][i_list[x_i-1]][rec['group']['group']]) if rec['subject']['subject'] in o][0]
            i_list.append(sub_i)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
        else:
            custom_op[i_list[x_i-2]][rec['exam_name']['exam_name']][i_list[x_i-1]][rec['group']['group']].append({rec['subject']['subject']:[]})
            i_list.append(len(custom_op[i_list[x_i-2]][rec['exam_name']['exam_name']][i_list[x_i-1]][rec['group']['group']])-1)
            return generate_scheduled(x_i+1,i_list,rec,custom_op)
    if x_list[x_i] == 'exam_type':
        if any(rec['exam_type']['exam_type'] in x for x in custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']]):
            return custom_op
        else:
            op_d = {'id':rec['id'],"scheduled_date":rec['scheduled_date'],'start_time':rec['start_time'],'end_time':rec['end_time'],rec['exam_type']['exam_type']:{'max_marks':rec['max_marks'],'min_marks':rec['min_marks']}}
            custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']].append(op_d)
            is_there = [i for i,o in enumerate(custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']]) if 'subject_total' in o]
            if is_there:
                custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']][is_there[0]]['subject_total']['min_marks']+=float(rec['min_marks'])
                custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']][is_there[0]]['subject_total']['max_marks']+=float(rec['max_marks'])
            else:
                custom_op[i_list[x_i-3]][rec['exam_name']['exam_name']][i_list[x_i-2]][rec['group']['group']][i_list[x_i-1]][rec['subject']['subject']].append({'subject_total':{'max_marks':float(rec['max_marks']),'min_marks':float(rec['min_marks'])}})
        return custom_op

class GradingViewSet(ExamManGenericMixinViewSet):
    queryset = models.Grading.objects.all()
    serializer_class = serializers.GradingSerializer
    http_method_names = ['get', 'post', 'put']

    def perform_create(self, serializer):
        user = self.request.user.id
        serializer.save(created_by=user) # specify user

class RecordMarks(viewsets.ModelViewSet):
    queryset = models.StudentMarks.objects.all()
    serializer_class = serializers.RecordMarksSerializer
    http_method_names = ['get', 'post', 'put']

    def get_serializer(self, *args, **kwargs):
      if "data" in kwargs:
        request_data = kwargs["data"]
        if isinstance(request_data, list):
            kwargs["many"] = True

      return super(RecordMarks, self).get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        filter_class = self.request.query_params.get('class',None)
        filter_section = self.request.query_params.get('section',None)
        filter_subject = self.request.query_params.get('subject',None)
        filter_exam = self.request.query_params.get('exam',None)
        filter_academic_year = self.request.query_params.get('academic_year',None)
        filter_group = self.request.query_params.get('group',None)
        queryset = super().get_queryset()
        queryset = queryset.filter(
            academic_year = filter_academic_year,
            exam_schedule__subject__id = filter_subject,
            exam_schedule__exam_name__id = filter_exam,
            exam_schedule__class_name__id = filter_class,
            exam_schedule__section__id = filter_section
        )
        cus_op = []
        students = Profile.objects.filter(
            class_name__id=filter_class,
            section__id=filter_section,
            is_active=True).order_by('id')
        
        approved = True # models.ResultAprove.objects.filter(
            # academic_year=filter_academic_year,
            # exam_name=filter_exam,
            # class_name=filter_class,
            # section=filter_section,
            # group=filter_group,
            # approved=False).exists()
        
        for student in students:
            recs = [i for i,o in enumerate(queryset) if student == o.student]
            if recs:
                for rec in recs:
                    ex = [x for x,o in enumerate(cus_op) if queryset[rec].student.id == o['id']]
                    if ex:
                        cus_op[ex[0]][queryset[rec].exam_schedule.exam_type.type]={
                            'id':queryset[rec].id,
                            'marks':queryset[rec].marks,
                            'grade':queryset[rec].grade,
                        }
                    else:
                        cus_op.append({
                            'id':queryset[rec].student.id,
                            'first_name':queryset[rec].student.first_name,
                            'last_name':queryset[rec].student.last_name,
                            'student_id':queryset[rec].student.student_id,
                            'editable':approved,
                            queryset[rec].exam_schedule.exam_type.type:{
                                'id':queryset[rec].id,
                                'marks':queryset[rec].marks,
                                'grade':queryset[rec].grade,
                            }
                        })
            else:
                cus_op.append({
                    'id':student.id,
                    'first_name':student.first_name,
                    'last_name':student.last_name,
                    'student_id':student.student_id,
                    'editable':approved
                    })
        response.data['results'] = cus_op

        # filter the records based on class,section,subject,exam,academic_year
        # filter student based on class,section and is_active=1
        # if there is no records give the student details so that they can use them in post request
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        user = self.request.user.id
        for i in request.data:
            i['created_by'] = user
        serializer.is_valid(raise_exception=True)
        exam_obj = serializer.validated_data[0]['exam_schedule']
        approved = models.ResultAprove.objects.filter(
            academic_year=exam_obj.academic_year,
            exam_name=exam_obj.exam_name,
            class_name=exam_obj.class_name,
            section=exam_obj.section,
            group=exam_obj.group,
            approved=False).exists()
        if not approved:
            return Response({'detail': 'Results already Generated !'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return response.Response(status=status.HTTP_201_CREATED)
    
    def put(self, request, *args, **kwargs):
        user = request.user.id
        partial = kwargs.pop('partial', False)
        serialized_data = []
        for data in request.data:
            instance = models.StudentMarks.objects.get(id=data['id'])
            data['created_by'] = user
            data['academic_year'] = instance.academic_year
            data['student'] = instance.student.id
            data['exam_schedule'] = instance.exam_schedule.id
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            serialized_data.append(serializer.data)
        return Response(serialized_data)
            

class ResultRelease(ExamManGenericMixinViewSet):
    queryset = models.ResultAprove.objects.all()
    serializer_class = serializers.ResultReleaseSerializer
    http_method_names = ['get', 'post', 'put']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'section',
        'class_name',
        'exam_name',
        'group',
        'academic_year'
    ]
    
    def create(self, request, *args, **kwargs):
        queryset = super().get_queryset()
        queryset = self.filter_queryset(queryset)
        if queryset:
            return response.Response({'approved':queryset[0].approved})
        return response.Response({'approved':False})
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        students = Profile.objects.filter(
            class_name__id=request.query_params.get('class_name'),
            section__id=request.query_params.get('section'),
            is_active=True
        ).order_by('id')
        for exam in response.data['results']:
            sub_list = models.ExamSchedule.objects.filter(
                exam_name__id=request.query_params.get('exam_name'),
                class_name__id=request.query_params.get('class_name'),
                section__id=request.query_params.get('section'),
                group__id=request.query_params.get('group'))
            cus_op = []
            for rec in sub_list:
                sub_i = [i for i,o in enumerate(cus_op) if rec.subject.name in o]
                if sub_i:
                    if rec.exam_type.type not in cus_op[sub_i[0]][rec.subject.name]:
                        cus_op[sub_i[0]][rec.subject.name].append(rec.exam_type.type)
                else:
                    cus_op.append({
                        rec.subject.name:[rec.exam_type.type]
                    })
            exam['subjects'] = cus_op
            exam['student-marks'] = []
            for student in students:
                mop = get_results(student,request.query_params.get('exam_name'),request.query_params.get('group'))
                exam['student-marks'].append({
                    'student_id':student.student_id,
                    'first_name':student.first_name,
                    'last_name':student.last_name,
                    'subject_marks':mop['swm'],
                    'total_marks':mop['total_marks'],
                    'percentage':mop['total_percentage'],
                    'overall_grade':mop['grade']
                })
        return response
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.data:
            test = models.StudentMarks.objects.filter(
                academic_year=response.data['academic_year'],
                exam_schedule__exam_name__id=response.data['exam_name'],
                exam_schedule__class_name__id=response.data['class_name'],
                exam_schedule__section__id=response.data['section'],
                exam_schedule__group__id=response.data['group']).update(editable=False)
        return response

def get_results(student,exam_name,group):
    student_marks = models.StudentMarks.objects.filter(
        student=student,
        exam_schedule__exam_name__id=exam_name,
        exam_schedule__group__id=group)
    mop = {
        'swm':[],
        'total_marks':0,
        'total_percentage':0,
        'grade':'N/A'
    }
    sub_max_total = 0
    exam_max_total = 0
    for rec in student_marks:
        marks = get_marks_value(rec.marks)
        sub_i = [i for i,o in enumerate(mop['swm']) if rec.exam_schedule.subject.name in o]
        if sub_i:
            sub_max_total += float(rec.exam_schedule.max_marks)
            mop['swm'][sub_i[0]][rec.exam_schedule.subject.name][rec.exam_schedule.exam_type.type]=marks
            mop['swm'][sub_i[0]]['subject_total'] += marks
            mop['swm'][sub_i[0]]['percentage'] = mop['swm'][sub_i[0]]['subject_total']/sub_max_total*100
            mop['swm'][sub_i[0]]['grade'] = get_grade(mop['swm'][sub_i[0]]['percentage'])
            # print(mop['swm'][sub_i[0]]['percentage'],get_grade(mop['swm'][sub_i[0]]['percentage']))
        else:
            mop['swm'].append({
                rec.exam_schedule.subject.name:{
                    rec.exam_schedule.exam_type.type:marks
                },
                'subject_total':marks,
                'percentage':marks/float(rec.exam_schedule.max_marks)*100,
                'grade':get_grade(marks/float(rec.exam_schedule.max_marks)*100),
            })
            sub_max_total = float(rec.exam_schedule.max_marks)
        mop['total_marks'] += marks
        exam_max_total += float(rec.exam_schedule.max_marks)
    mop['total_percentage'] = mop['total_marks']/exam_max_total*100 if exam_max_total else 0
    mop['grade'] = get_grade(mop['total_percentage'])
    return mop

class ExamAttendanceView(viewsets.ModelViewSet):
    queryset = models.ExamAttendance.objects.all()
    serializer_class = serializers.ExamAttendanceSerializer
    http_method_names = ['get', 'post', 'put']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'academic_year',
        'exam_name',
    ]

    def get_serializer(self, *args, **kwargs):
      if "data" in kwargs:
        request_data = kwargs["data"]
        if isinstance(request_data, list):
            kwargs["many"] = True

      return super(ExamAttendanceView, self).get_serializer(*args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = super().get_queryset()
        queryset = self.filter_queryset(queryset)
        response = super().list(request, *args, **kwargs)
        filter_class = self.request.query_params.get('class',None)
        filter_section = self.request.query_params.get('section',None)
        filter_exam = self.request.query_params.get('exam_name',None)
        filter_academic_year = self.request.query_params.get('academic_year',None)
        queryset = queryset.filter(
            student__class_name__id=filter_class,
            student__section__id=filter_section
        )

        scheduled = models.ExamSchedule.objects.filter(
            academic_year = filter_academic_year,
            class_name__id = filter_class,
            section__id = filter_section,
            exam_name__id = filter_exam
        ).exists()

        if not scheduled:
            return Response({'detail': 'No Exams Scheduled !'}, status=status.HTTP_404_NOT_FOUND)
        
        cus_op = []
        students = Profile.objects.filter(
            class_name__id=filter_class,
            section__id=filter_section,
            is_active=True).order_by('id')
        approved = True 

        worked_days = queryset[0].worked_days if queryset else None
        
        for student in students:
            obj = {
                "stud_id":student.id,
                "student_id":student.student_id,
                "first_name":student.first_name,
                "last_name":student.last_name,
                "editable":approved
            }
            if worked_days:
                obj['worked_days'] = worked_days
            recs = [i for i,o in enumerate(queryset) if student == o.student]
            if recs:
                obj['id'] = queryset[recs[0]].id
                obj['attended_days'] = queryset[recs[0]].attended_days
            cus_op.append(obj)
        response.data['results'] = cus_op

        # filter the records based on class,section,subject,exam,academic_year
        # filter student based on class,section and is_active=1
        # if there is no records give the student details so that they can use them in post request
        return response
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        user = self.request.user.id
        student_list = []
        for i in request.data:
            i['created_by'] = user
            student_list.append(i['student'])
        serializer.is_valid(raise_exception=True)
        if models.ExamAttendance.objects.filter(
            student__in = student_list,
            academic_year=request.data[0]['academic_year'],
            exam_name__id = request.data[0]['exam_name']).exists():
            return Response({'detail': 'Data conflicts are there !'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return response.Response(status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
    
    def update(self, request, *args, **kwargs):
        user = request.user.id
        request.data['created_by'] = user
        response = super().update(request, *args, **kwargs)
        print(response)
        return response

class GenSheet(APIView):
    http_method_names = ['get']

    def get(self, request):
        marks_sheet = {}
        students = []
        academicYear = request.GET.get('academicYear', None)
        filter_type = request.GET.get('type', None)
        filter_exam = request.GET.get('exam', None)
        if not academicYear:
            academicYear = services.get_academic_years_key_value('running')[0]
        
        if filter_type == 'student':
            student_id = request.GET.get('student', None)
            student = student_services.get_student(student_id)
            students.append({student.student_id:{
                'studentId':student.student_id,
                'first_name':student.first_name,
                'last_name':student.last_name,
                'academic_year':academicYear,
                'admission_number':student.admission_number,
                'class':student.class_name.class_name,
                'section':student.section.section_name,
                'exam_wise_marks':[],
                'exam_wise_attendance':get_attendance(student,academicYear,filter_exam)
            }})
            filter_class = student.class_name
            filter_section = student.section
        else:
            filter_class = request.GET.get('class_name', None)
            filter_section = request.GET.get('section', None)
            profiles = Profile.objects.filter(class_name__id=filter_class,section__id=filter_section,is_active=True).order_by('id')
            for stud in profiles:
                students.append({stud.student_id:{
                    'studentId':stud.student_id,
                    'first_name':stud.first_name,
                    'last_name':stud.last_name,
                    'academic_year':academicYear,
                    'admission_number':stud.admission_number,
                    'class':stud.class_name.class_name,
                    'section':stud.section.section_name,
                    'exam_wise_marks':[],
                    'exam_wise_attendance':get_attendance(stud,academicYear,filter_exam)
                }})

        # approved = models.ResultAprove.objects.filter(
        #     academic_year=academicYear,
        #     class_name=filter_class,
        #     section=filter_section,
        #     exam_name__id=filter_exam,
        #     approved=False).exists() if filter_exam else models.ResultAprove.objects.filter(
        #         academic_year=academicYear,
        #         class_name=filter_class,
        #         section=filter_section,
        #         approved=False).exists()
        # if approved:
        #     return Response({'detail': 'Results Not Generated Yet !'}, status=status.HTTP_404_NOT_FOUND)
        queryset = models.StudentMarks.objects.filter(
            student = student,
            academic_year = academicYear
        ) if filter_type == "student" else models.StudentMarks.objects.filter(
            academic_year = academicYear,
            exam_schedule__class_name__id=filter_class,
            exam_schedule__section__id=filter_section
        )

        if filter_exam:
            queryset = queryset.filter(exam_schedule__exam_name__id=filter_exam)
            if not queryset:
                return Response({'detail': 'No Records Found !'}, status=status.HTTP_404_NOT_FOUND)

        for rec in queryset.order_by('exam_schedule__subject__id'):
            student_i = [i for i,o in enumerate(students) if rec.student.student_id in o]
            students[student_i[0]][rec.student.student_id]['exam_wise_marks'] = generate_sheet(0,rec,students[student_i[0]][rec.student.student_id]['exam_wise_marks'])
        return response.Response(students)

def get_attendance(student,academic_year,exam=None):
    op = []
    attendance = models.ExamAttendance.objects.filter(
        student = student,
        exam_name__id = exam,
        academic_year = academic_year) if exam else models.ExamAttendance.objects.filter(
            student = student,
            academic_year = academic_year)
    
    for obj in attendance:
        op.append({
            obj.exam_name.name:{
                'worked_days':obj.worked_days,
                'attended_days':obj.attended_days
            }
        })

    return op

def get_grade(percentage,remark = False):
    grade = models.Grading.objects.filter(from_min__lte=percentage,to_max__gte=percentage) if percentage else None
    r_obj = {
        'grade' : grade[0].symbol,
        "grade_remarks" : grade[0].name
    } if grade else {
        'grade' : 'N/A',
        'grade_remarks' : 'N/A'
    }
    return r_obj if remark else r_obj['grade']

def generate_sheet(check,rec,op,i_list=[None,None]):
    checks = ['exam','subject']
    marks = get_marks_value(rec.marks)
    if checks[check] == 'exam':
        ex_i = [i for i,o in enumerate(op) if rec.exam_schedule.exam_name.name in o]
        i_list[check] = ex_i[0] if ex_i else len(op)
        if not ex_i:
            op.append({
                rec.exam_schedule.exam_name.name:[],
                'total_marks_gained':0.0,
                'total_marks':0.0,
                'total_percentage':0.0,
                'grade':'N/A',
                # 'remarks':'Improve',
                # 'no_of_working_days':30,
                # 'no_of_days_attended':30
                })
        return generate_sheet(check+1,rec,op)
    elif checks[check] == 'subject':
        sub_i = [sub for sub,o in enumerate(op[i_list[check-1]][rec.exam_schedule.exam_name.name]) if rec.exam_schedule.subject.name in o]
        i_list[check] = sub_i[0] if sub_i else len(op[i_list[check-1]][rec.exam_schedule.exam_name.name])
        op[i_list[check-1]]['total_marks_gained'] += marks
        op[i_list[check-1]]['total_marks'] += float(rec.exam_schedule.max_marks)
        if not sub_i:
            percent = marks / float(rec.exam_schedule.max_marks) * 100 if rec.exam_schedule.max_marks > 0 else None
            op[i_list[check-1]][rec.exam_schedule.exam_name.name].append({rec.exam_schedule.subject.name:{
                'marks_obtained':marks,
                'total_marks':float(rec.exam_schedule.max_marks),
                'percentage': percent,
                'grade':get_grade(percent) if rec.exam_schedule.max_marks > 0 else rec.marks,
            }})
        else:
            op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['marks_obtained'] += marks
            op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['total_marks'] += float(rec.exam_schedule.max_marks)
            percent = op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['marks_obtained'] / op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['total_marks'] * 100
            op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['percentage'] = percent
            op[i_list[check-1]][rec.exam_schedule.exam_name.name][sub_i[0]][rec.exam_schedule.subject.name]['grade'] = get_grade(percent) if rec.exam_schedule.max_marks > 0 else rec.marks
        op[i_list[check-1]]['total_percentage'] = op[i_list[check-1]]['total_marks_gained'] / op[i_list[check-1]]['total_marks'] * 100 if op[i_list[check-1]]['total_marks'] > 0 else None
        grade_obj = get_grade(round(op[i_list[check-1]]['total_percentage']) if op[i_list[check-1]]['total_percentage'] else 0,True)
        op[i_list[check-1]]['grade'] = grade_obj['grade']
        op[i_list[check-1]]['grade_remarks'] = grade_obj['grade_remarks']
        return op

# generate_scheduled
class HallTicketGenerationView(viewsets.ModelViewSet):
    queryset = models.ExamSchedule.objects.all()
    serializer_class = serializers.ExamScheduleSerializer
    http_method_names = ['get']

    def generate_hall_ticket(self, request, *args, **kwargs):
        # Get the academic year from the request or use the running academic year if not provided
        academicYear = request.GET.get('academicYear', None)
        exam = request.GET.get('exam', None)
        class_name = request.GET.get('class_name', None)
        section = request.GET.get('section', None)
        req_type = 'class'

        if req_type == 'class':
            students = Profile.objects.filter(class_name__id=class_name,section__id=section,is_active=True)
    
        if not academicYear:
            academicYear = services.get_academic_years_key_value('running')[0]

        # Get the student based on the provided student_id
        # student = student_services.get_student(student_id)

        # if not student:
        #     return Response({'error': f'Student with ID {student_id} not found'}, status=404)

        # Get the relevant exam schedule for the student
        exam_schedules = models.ExamSchedule.objects.filter(
            class_name__id=class_name,
            section__id=section,
            academic_year=academicYear,
            exam_name = exam
        ).order_by('scheduled_date')

        # Prepare the initial hall ticket data with student details and an empty list for exams
        hall_ticket_data = {
            # 'student_id': student.student_id,
            # 'first_name': student.first_name,
            # 'last_name': student.last_name,
            # 'admission_number': student.admission_number,
            # 'class_name': student.class_name.class_name,
            # 'section': student.section.section_name,
            'academic_year': academicYear,
            'exams': {},
        } if exam_schedules else {}

        for exam_schedule in exam_schedules:
            exam_key = f"{exam_schedule.exam_name.name}_{exam_schedule.group.name}"

            if exam_key not in hall_ticket_data['exams']:
                hall_ticket_data['exams'][exam_key] = {
                    'exam_name': exam_schedule.exam_name.name,
                    'group': exam_schedule.group.name,
                    'subjects': [],
                }

            # Check if the subject already exists for this exam and group
            sub_i = [i for i,o in enumerate(hall_ticket_data['exams'][exam_key]['subjects']) if (o['subject_name'] == exam_schedule.subject.name and o['schedule_date']==exam_schedule.scheduled_date and o['start_time']==exam_schedule.start_time and o['end_time']==exam_schedule.end_time)]
            # Append the subject data only if it's not already included
            if not sub_i:
                subject_data = {
                    'subject_name': exam_schedule.subject.name,
                    'schedule_date': exam_schedule.scheduled_date,
                    'start_time': exam_schedule.start_time,  # Set the timing as None as mentioned
                    'end_time': exam_schedule.end_time,
                    'exam_type': exam_schedule.exam_type.type
                    }
                hall_ticket_data['exams'][exam_key]['subjects'].append(subject_data)
            else:
                hall_ticket_data['exams'][exam_key]['subjects'][sub_i[0]]['exam_type'] += f",{exam_schedule.exam_type.type}"

        # Convert the dictionary of exams to a list for the final response
        if hall_ticket_data:
            for exam in hall_ticket_data['exams']:
                hall_ticket_data['exams'][exam]['group'] = exam.split('_')[-1]  # Extracting group name

            hall_ticket_data['exams'] = list(hall_ticket_data['exams'].values())
            if req_type == 'class':
                ex_data = hall_ticket_data['exams']
                c_op = []
                for cstudent in students:
                    c_op.append({
                        'student_id': cstudent.student_id,
                        'first_name': cstudent.first_name,
                        'last_name': cstudent.last_name,
                        'admission_number': cstudent.admission_number,
                        'class_name': cstudent.class_name.class_name,
                        'section': cstudent.section.section_name,
                        'academic_year': academicYear,
                        'exams': ex_data,
                    })
                hall_ticket_data = c_op
        else:
            return Response({'detail': 'NO Exams Scheduled.'}, status=status.HTTP_404_NOT_FOUND)

        # Return the response with the hall ticket data, status code, and message
        return Response(hall_ticket_data)
    
    def create(self, request, *args, **kwargs):
        id_list = request.data['ids']
        try:
            models.ExamSchedule.objects.filter(id__in = id_list).update(editable=False)
            return response.Response(status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({'detail': 'Wrong Data !'}, status=status.HTTP_400_BAD_REQUEST)