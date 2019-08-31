from rest_framework import serializers
from tests.testapp.models import Book, Course, Student, Phone
from drf_pretty_update.serializers import NestedModelSerializer
from drf_pretty_update.fields import ReplaceableNestedField, WritableNestedField

class PhoneSerializer(NestedModelSerializer):
    class Meta:
        model = Phone
        fields = ['number', 'type']


class BookSerializer(NestedModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author']


class WritableCourseSerializer(NestedModelSerializer):
    books = WritableNestedField(serializer=BookSerializer, many=True, required=False)
        
    class Meta:
        model = Course
        fields = ['name', 'code', 'books']


class ReplaceableCourseSerializer(NestedModelSerializer):
    books = ReplaceableNestedField(serializer=BookSerializer, many=True, required=False)
        
    class Meta:
        model = Course
        fields = ['name', 'code', 'books']


class ReplaceableStudentSerializer(NestedModelSerializer):
    course = ReplaceableNestedField(serializer=WritableCourseSerializer, many=False)
    phone_numbers = PhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['name', 'age', 'course', 'phone_numbers']


class WritableStudentSerializer(NestedModelSerializer):
    course = WritableNestedField(serializer=WritableCourseSerializer, many=False)
    phone_numbers = PhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['name', 'age', 'course', 'phone_numbers']

