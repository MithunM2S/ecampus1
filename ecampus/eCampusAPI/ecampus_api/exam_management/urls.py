from django.urls import path, include, re_path
from . import views
from .views import HallTicketGenerationView
from rest_framework import routers

router = routers.SimpleRouter()
# router.register(r'SubjectType', views.SubjectTypeViewset)
router.register(r'subject-type', views.SubjectTypeViewSet)
router.register(r'subject', views.SubjectViewSet)
router.register(r'group', views.GroupViewSet)
router.register(r'exam', views.ExamNameViewSet)
router.register(r'markstype', views.ExamTypeViewSet)
router.register(r'record-marks', views.RecordMarks)
router.register(r'result-release', views.ResultRelease)
router.register(r'grading', views.GradingViewSet)
router.register(r'attendance', views.ExamAttendanceView)

# urlpatterns = []

urlpatterns = [
    path('scheduled/', views.ExamScheduling.as_view({'get': 'list'}), name='Exam-Schedules'),
    path('schedule/', views.ExamScheduling.as_view({'post': 'create'}), name='Exam-Scheduling'),
    path('reschedule/', views.ExamScheduling.as_view({'put':'update'}), name='Exam-Rescheduling'),
    path('get-marks/', views.GenSheet.as_view(), name='marks-card'),
    path('hall-ticket/', HallTicketGenerationView.as_view({'get':'generate_hall_ticket'})),
    path('hall-ticket/', HallTicketGenerationView.as_view({'post':'create'})),
   
#     path('Result-generation/', Resultgeneration.as_view(),   name='Result_generation'),
   
]
urlpatterns += router.urls
