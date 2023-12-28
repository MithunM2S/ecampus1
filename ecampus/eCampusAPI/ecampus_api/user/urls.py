from django.urls import path
from .views import *

urlpatterns = [
    path('account/register/', RegisterView.as_view(), name="register"),
    path('account/list/', UserViewSet.as_view({'get':'list'}), name="list_user"),
    path('account/update/<pk>/', UserViewSet.as_view({'put':'update'}), name="update_user"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]