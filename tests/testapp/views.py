from rest_framework import viewsets
from rest_framework.response import Response
from django_restql.mixins import DynamicFieldsMixin

from tests.testapp.models import Book, Course, Student
from tests.testapp.serializers import (
	BookSerializer, ReplaceableStudentSerializer,
	WritableStudentSerializer, WritableCourseSerializer,
	ReplaceableCourseSerializer
)

class BookViewSet( viewsets.ModelViewSet):
	serializer_class = BookSerializer
	queryset = Book.objects.all()

class WritableCourseViewSet( viewsets.ModelViewSet):
	serializer_class = WritableCourseSerializer
	queryset = Course.objects.all()

class ReplaceableCourseViewSet( viewsets.ModelViewSet):
	serializer_class = ReplaceableCourseSerializer
	queryset = Course.objects.all()


class ReplaceableStudentViewSet( viewsets.ModelViewSet):
	serializer_class = ReplaceableStudentSerializer
	queryset = Student.objects.all()


class WritableStudentViewSet( viewsets.ModelViewSet):
	serializer_class = WritableStudentSerializer
	queryset = Student.objects.all()
