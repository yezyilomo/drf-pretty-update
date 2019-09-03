from django.urls import reverse
from rest_framework.test import APITestCase
from tests.testapp.models import Book, Course, Student, Phone


class ViewTests(APITestCase):
    def setUp(self):
        self.book1 = Book.objects.create(title="Advanced Data Structures", author="S.Mobit")
        self.book2 = Book.objects.create(title="Basic Data Structures", author="S.Mobit")

        self.course1 = Course.objects.create(
            name="Data Structures", code="CS210"
        )
        self.course2 = Course.objects.create(
            name="Programming", code="CS150"
        )

        self.course1.books.set([self.book1, self.book2])
        self.course2.books.set([self.book1])

        self.student = Student.objects.create(
            name="Yezy", age=24, course=self.course1
        )

        self.phone1 = Phone.objects.create(number="076711110", type="Office", student=self.student)
        self.phone2 = Phone.objects.create(number="073008880", type="Home", student=self.student)

    def tearDown(self):
        Book.objects.all().delete()
        Course.objects.all().delete()
        Student.objects.all().delete()


    # **************** POST Tests ********************* #

    def test_post_on_pk_nested_foreignkey_related_field(self):
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
                    'books': [
                        {"title": "Advanced Data Structures", "author": "S.Mobit"}
                    ]
                }, 
                'phone_numbers': []
            }
        )
        
    def test_post_on_writable_nested_foreignkey_related_field(self):
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

    def test_post_with_add_operation(self):
        url = reverse("rcourse-list")
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {"add":[1,2]}
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

    def test_post_with_create_operation(self):
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {"create": [
                    {"title": "Linear Math", "author": "Me"},
                    {"title": "Algebra Three", "author": "Me"}
                ]}
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

    def test_post_on_deep_nested_fields(self):
        url = reverse("wstudent-list")
        data = {
            "name": "yezy",
            "age": 33,
            "course": {
                "name": "Programming", 
                "code": "CS50",
                "books": {"create": [
                    {"title": "Python Tricks", "author": "Dan Bader"}
                ]}
            }
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
                    'books': [
                        {"title": "Python Tricks", "author": "Dan Bader"}
                    ]
                }, 
                'phone_numbers': []
            }
        )

    # **************** PUT Tests ********************* #

    def test_put_on_pk_nested_foreignkey_related_field(self):
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
                        {"title": "Advanced Data Structures", "author": "S.Mobit"}
                    ]
                }, 
                'phone_numbers': [
                    {'number': '076711110', 'type': 'Office'}, 
                    {'number': '073008880', 'type': 'Home'} 
                ]
            }
        )

    def test_put_on_writable_nested_foreignkey_related_field(self):
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

    def test_put_with_add_operation(self):
        url = reverse("rcourse-detail", args=[self.course2.id])
        data = {
                "name": "Data Structures",
                "code": "CS410",
                "books": {
                    "add": [2]
                }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS410",
                "books": [
                    {'title': 'Advanced Data Structures', 'author': 'S.Mobit'},
                    {'title': 'Basic Data Structures', 'author': 'S.Mobit'}
                ]
            }
        )

    def test_put_with_remove_operation(self):
        url = reverse("rcourse-detail", args=[self.course2.id])
        data = {
                "name": "Data Structures",
                "code": "CS410",
                "books": {
                    "remove": [1]
                }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS410",
                "books": []
            }
        )

    def test_put_with_create_operation(self):
        url = reverse("wcourse-detail", args=[self.course2.id])
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {
                    "create": [
                        {"title": "Primitive Data Types", "author": "S.Mobit"}
                    ]
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
                    {"title": "Primitive Data Types", "author": "S.Mobit"}
                ]
            }
        )

    def test_put_with_update_operation(self):
        url = reverse("wcourse-detail", args=[self.course2.id])
        data = {
                "name": "Data Structures",
                "code": "CS310",
                "books": {
                    "update": {
                        1: {"title": "React Programming", "author": "M.Json"}
                    }
                }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                "name": "Data Structures",
                "code": "CS310",
                "books": [
                    {"title": "React Programming", "author": "M.Json"}
                ]
            }
        )

    def test_put_on_deep_nested_fields(self):
        url = reverse("wstudent-detail", args=[self.student.id])
        data = {
            "name": "yezy",
            "age": 33,
            "course": {
                "name": "Programming", 
                "code": "CS50", 
                "books": {
                    "remove": [1]
                }
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(
            response.data,
            {
                'name': 'yezy', 'age': 33, 
                'course': {
                    'name': 'Programming', 'code': 'CS50', 
                    'books': [
                        {'title': 'Basic Data Structures', 'author': 'S.Mobit'}
                    ]
                }, 
                'phone_numbers': [
                    {'number': '076711110', 'type': 'Office'}, 
                    {'number': '073008880', 'type': 'Home'}
                ]
            }
        )