# from ecampus_api import employee
from os import truncate
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.db.models.fields import NullBooleanField
from master.models import CasteCategory, Caste, Gender, ClassGroup
from phone_field import PhoneField



GENDER = (
    ('Male', ('Male')),
    ('Female', ('Female')),
)

ATTENDANCE_STATUS = (
    ('Present', ('Present')),
    ('Absent', ('Absent')),
)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT / user_id/filename
    return "uploads/employee-profile/{0}/{1}".format(instance.pk, filename)
    # return filename


class Department(models.Model):
    name = models.CharField('Department', max_length=120)

    def __str__(self):
        return str(self.name)


class Designation(models.Model):
    designation = models.CharField('Designation', max_length=20)

    def __str__(self):
        return str(self.designation)

    class Meta:
        verbose_name = 'Designations'
        verbose_name_plural = 'Designations'


class EmployeeDetails(models.Model):
    employee_name = models.CharField(max_length=40)
    employee_photo = models.FileField(
        upload_to=user_directory_path, blank=True, null=True)
    dob = models.DateField()
    qualification = models.CharField(max_length=25, null=True)
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE, null=True)
    caste_category = models.ForeignKey(
        CasteCategory, on_delete=models.CASCADE, null=True)
    martial_status = models.CharField(max_length=15, null=True)
    father_husband_name = models.CharField(max_length=20, null=True)
    father_husband_number = PhoneField(blank=True, help_text='Contact phone number', null=True)
    present_address = models.CharField(max_length=200, null=True)
    permanent_address = models.CharField(max_length=200, null=True)
    contact_number = PhoneField(blank=True, help_text='Contact phone number')
    email = models.EmailField(null=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, default=Gender.objects.order_by('id').first().id)
    blood_group = models.CharField(max_length=15, null=True)
    date_of_join = models.DateField()
    work_experience = models.CharField(max_length=25, null=True)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, default=ClassGroup.objects.order_by('id').first().id)
    class_teacher = models.CharField(max_length=20, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
    active= models.BooleanField(default=True, blank=True, null=True)
    login_access= models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return str(self.employee_name)

    class Meta:
        verbose_name = 'Employee Details'
        verbose_name_plural = 'Employee Details'


class Attendance(models.Model):
    presence = models.TextField(blank=True)
    absence = models.TextField(blank=True)
    attendance_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.attendance_date)

    def save(self, *args, **kwargs):
        att = self.attendance_date
        if not Attendance.objects.filter(
                attendance_date=att):
            return super(Attendance, self).save(*args, **kwargs)
        else:
            return "Attendance cannot be duplicated"
