from rest_framework import serializers
from tests.testapp.models import Book, Course, Student, Phone
from drf_pretty_update.mixins import ReplaceableNestedField, NestedModelSerializer, WritableNestedField

class PhoneSerializer(NestedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = ['number', 'type']

        
class BookSerializer(NestedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author']


class WritableCourseSerializer(NestedModelSerializer, serializers.ModelSerializer):
    books = WritableNestedField(serializer=BookSerializer, many=True, required=False)
        
    class Meta:
        model = Course
        fields = ['name', 'code', 'books']


class ReplaceableCourseSerializer(NestedModelSerializer, serializers.ModelSerializer):
    books = ReplaceableNestedField(serializer=BookSerializer, many=True, required=False)
        
    class Meta:
        model = Course
        fields = ['name', 'code', 'books']


class ReplaceableStudentSerializer(NestedModelSerializer, serializers.ModelSerializer):
    course = ReplaceableNestedField(serializer=WritableCourseSerializer, many=False)
    phone_numbers = PhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['name', 'age', 'course', 'phone_numbers']


class WritableStudentSerializer(NestedModelSerializer, serializers.ModelSerializer):
    course = WritableNestedField(serializer=WritableCourseSerializer, many=False)
    phone_numbers = PhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ['name', 'age', 'course', 'phone_numbers']

