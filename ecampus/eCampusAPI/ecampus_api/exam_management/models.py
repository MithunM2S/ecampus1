from django.db import models
from master.models import ClassName, Section, Quota
from student.models import Profile
from master import services

present_academic_year = services.get_academic_years_key_value('running')[0]

class SubjectType(models.Model):
    name = models.CharField('Subject Type', unique=True, null=False, max_length=30)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)

class Subject(models.Model):
    name = models.CharField('Subject Name', unique=True, null=False, max_length=80)
    subject_type = models.ForeignKey(SubjectType, on_delete=models.PROTECT, null=False)
    code = models.CharField('Subject Code', unique=True, null=True, max_length=30)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

class Group(models.Model):
    name = models.CharField('Group Name', unique=True, max_length=50)
    order = models.IntegerField('Group Order',unique=True)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

class ExamName(models.Model):
    name = models.CharField('Exam Name', unique=True, max_length=50)
    order = models.IntegerField('Exam Order',unique=True)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

class ExamType(models.Model):
    type = models.CharField('Type Name', unique=True, max_length=80)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

class ExamSchedule(models.Model):
    academic_year = models.CharField('Academic Year', null=False, max_length=20)
    class_name = models.ForeignKey(ClassName, on_delete=models.PROTECT, null=True)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True)
    exam_name = models.ForeignKey(ExamName, on_delete=models.PROTECT, null=False)
    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT, null=False)
    group = models.ForeignKey(Group, on_delete=models.PROTECT, null=False)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, null=False)
    max_marks = models.DecimalField('Maximum Marks', null=False, max_digits=5, decimal_places=2)
    min_marks = models.DecimalField('Minimum Marks', null=False, max_digits=5, decimal_places=2)
    status = models.CharField('Status', null=True, max_length=30)
    scheduled_date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    cancelled_date = models.DateTimeField(null=True)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

    # class Meta:
    #     ordering = ['-created_on']

class ExamScheduleHistory(models.Model):
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.PROTECT, null=False)
    exam_name = models.ForeignKey(ExamName, on_delete=models.PROTECT, null=False)
    rescheduled_date = models.DateTimeField(null=False)
    remarks = models.TextField(null=True, blank=True, max_length=400)
    status = models.CharField(null=True, blank=True, max_length=30)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)

    class Meta:
        ordering = ['-created_on']

class StudentMarks(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.PROTECT, null=False)
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.PROTECT, null=False)
    marks = models.CharField('Obtained Marks', null=True, max_length=10)
    grade = models.CharField('Obtained Grade', null=True, max_length=20)
    academic_year = models.CharField('Academic Year', null=False, max_length=20)
    remarks = models.TextField('Student Remarks', null=True, blank=True, max_length=400)
    status = models.CharField('Pass Status', choices=[('PASS','PASS'),('FAIL','FAIL'),('PENDING','PENDING')], default='PENDING', max_length=10) # helps to work with suplies and in marks changing scenario
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)

    class Meta:
        ordering = ['-created_on']

class ResultAprove(models.Model):
    exam_name = models.ForeignKey(ExamName, on_delete=models.PROTECT, null=False)
    class_name = models.ForeignKey(ClassName, on_delete=models.PROTECT, null=False)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=False)
    group = models.ForeignKey(Group, on_delete=models.PROTECT, null=False)
    academic_year = models.CharField('Academic Year', null=False, max_length=20)
    approved = models.BooleanField('Approved', null=False, default=False)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)

    class Meta:
        ordering = ['-created_on']

class ExamAttendance(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.PROTECT, null=False)
    exam_name = models.ForeignKey(ExamName, on_delete=models.PROTECT, null=False)
    worked_days = models.IntegerField('Days Worked', null=False)
    attended_days = models.IntegerField('Attended Days', null=False)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)

    class Meta:
        ordering = ['-created_on']

class Grading(models.Model):
    from_min = models.DecimalField('Minimum range', null=False, max_digits=5, decimal_places=2)
    to_max = models.DecimalField('Maximum range', null=False, max_digits=5, decimal_places=2)
    symbol = models.CharField('Grade symbol', null=False, max_length=5, unique=True)
    name = models.CharField('Grade name', null=True, max_length=25, unique=True)
    created_on =  models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.IntegerField('created by', null=False)
    deleted = models.BooleanField('Deleted', default=False)
    editable = models.BooleanField('Editable', default=True)
    academic_year = models.CharField('Academic Year',null=False, max_length=20, default=present_academic_year)

    class Meta:
        ordering = ['-created_on']