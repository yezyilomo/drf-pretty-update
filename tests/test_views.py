from django.urls import reverse
from rest_framework.test import APITestCase
from tests.testapp.models import Book, Course, Student, Phone


class ViewTests(APITestCase):
    def setUp(self):
        self.book1 = Book.objects.create(title="Advanced Data Structures", author="S.Mobit")
        self.book2 = Book.objects.create(title="Basic Data Structures", author="S.Mobit")

        self.course = Course.objects.create(
            name="Data Structures", code="CS210"
        )

        self.course2 = Course.objects.create(
            name="Programming", code="CS150"
        )

        self.course.books.set([self.book1, self.book2])

        self.student = Student.objects.create(
            name="Yezy", age=24, course=self.course
        )

        self.phone1 = Phone.objects.create(number="076711110", type="Office", student=self.student)
        self.phone2 = Phone.objects.create(number="073008880", type="Home", student=self.student)

    def tearDown(self):
        Book.objects.all().delete()
        Course.objects.all().delete()
        Student.objects.all().delete()


    # **************** POST Tests ********************* #

    def test_post_on_replaceable_nested_simple_related_field(self):
        url = reverse("rstudent-list")
        data = {
            "name": "yezy",
            "age": 33,
            "course": 2
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(
            response.data,
            {
                'name': 'yezy', 
                'age': 33, 
                'course': {
                    'name': 'Programming', 
                    'code': 'CS150', 
                    'books': []
                }, 
                'phone_numbers': []
            }
        )
        
    def test_post_on_writable_nested_simple_related_field(self):
        url = reverse("wstudent-list")
        data = {
            "name": "yezy",
            "age": 33,
            "course": {"name": "Programming", "code": "CS50"}
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(
            response.data,
            {
                'name': 'yezy', 
                'age': 33, 
                'course': {
                    'name': 'Programming', 
                    'code': 'CS50', 
                    'books': []
                }, 
                'phone_numbers': []
            }
        )

    def test_post_on_replaceable_with_nested_many_related_field(self):
        url = reverse("rcourse-list")
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": [1,2]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {'title': 'Advanced Data Structures', 'author': 'S.Mobit'},
                    {'title': 'Basic Data Structures', 'author': 'S.Mobit'}
                ]
            }
        )

    def test_post_on_writable_with_nested_many_related_field(self):
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {"title": "Linear Math", "author": "Me"},
                    {"title": "Algebra Three", "author": "Me"}
                ]
        }
        url = reverse("wcourse-list")
        response = self.client.post(url, data, format="json")

        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {"title": "Linear Math", "author": "Me"},
                    {"title": "Algebra Three", "author": "Me"}
                ]
            }
        )


    # **************** PUT Tests ********************* #

    def test_put_on_replaceable_nested_simple_related_field(self):
        url = reverse("rstudent-detail", args=[self.student.id])
        data = {
            "name": "yezy",
            "age": 33,
            "course": 2
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                'name': 'yezy', 'age': 33, 
                'course': {
                    'name': 'Programming', 'code': 'CS150', 
                    'books': [

                    ]
                }, 
                'phone_numbers': [
                    {'number': '076711110', 'type': 'Office'}, 
                    {'number': '073008880', 'type': 'Home'} 
                ]
            }
        )

    def test_put_on_writable_nested_simple_related_field(self):
        url = reverse("wstudent-detail", args=[self.student.id])
        data = {
            "name": "yezy",
            "age": 33,
            "course": {"name": "Programming", "code": "CS50"}
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                'name': 'yezy', 'age': 33, 
                'course': {
                    'name': 'Programming', 'code': 'CS50', 
                    'books': [
                        {'title': 'Advanced Data Structures', 'author': 'S.Mobit'},
                        {'title': 'Basic Data Structures', 'author': 'S.Mobit'}
                    ]
                }, 
                'phone_numbers': [
                    {'number': '076711110', 'type': 'Office'}, 
                    {'number': '073008880', 'type': 'Home'}
                    
                ]
            }
        )

    def test_put_on_replaceable_with_nested_many_related_field(self):
        url = reverse("rcourse-detail", args=[self.course.id])
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {
                    "remove": [1],
                    "add": [1]
                }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {'title': 'Advanced Data Structures', 'author': 'S.Mobit'},
                    {'title': 'Basic Data Structures', 'author': 'S.Mobit'}
                ]
            }
        )
        
    def test_put_on_writable_with_nested_many_related_field(self):
        url = reverse("wcourse-detail", args=[self.course.id])
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {
                    "remove": [2],
                    "add": [{"title": "Primitive Data Types", "author": "S.Mobit"}],
                    "update": {1:{"title": "Power Of Data", "author": "James"}}
                }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {"title": "Power Of Data", "author": "James"},
                    {"title": "Primitive Data Types", "author": "S.Mobit"}
                ]
            }
        )
