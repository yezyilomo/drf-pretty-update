"""test_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from rest_framework import routers
from tests.testapp.views import (
    BookViewSet, ReplaceableStudentViewSet, 
    WritableStudentViewSet, WritableCourseViewSet, ReplaceableCourseViewSet
)


router = routers.DefaultRouter()
router.register('books', BookViewSet, base_name='book')
router.register('writable-courses', WritableCourseViewSet, base_name='wcourse')
router.register('replaceable-courses', ReplaceableCourseViewSet, base_name='rcourse')
router.register('replaceable-students', ReplaceableStudentViewSet, base_name='rstudent')
router.register('writable-students', WritableStudentViewSet, base_name='wstudent')

urlpatterns = [
    path('', include(router.urls))
]
