from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from classrooms.models import Classroom
from tasks.models import Task
from .models import Resource

User = get_user_model()

class ResourcePermissionTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='teacher', email='teacher@example.com', password='password', is_student=False)
        self.student = User.objects.create_user(username='student', email='student@example.com', password='password', is_student=True)
        
        self.classroom = Classroom.objects.create(name="Test Class", created_by=self.teacher)
        self.classroom.students.add(self.student)
        
        self.task = Task.objects.create(name="Test Task", description="Desc", end_date="2025-01-01T00:00:00Z", full_marks=10, created_by=self.teacher, classroom=self.classroom)
        
        self.test_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")

        self.resource_data = {
            'content_type': 'classroom',
            'object_id': str(self.classroom.id),
            'file': self.test_file
        }

    def test_create_resource_teacher(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(reverse('resource-list'), self.resource_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Resource.objects.count(), 1)

    def test_create_resource_student_forbidden(self):
        self.client.force_authenticate(user=self.student)
        self.resource_data['file'] = SimpleUploadedFile("test2.txt", b"content", content_type="text/plain")
        response = self.client.post(reverse('resource-list'), self.resource_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_resources_teacher(self):
        file_obj = SimpleUploadedFile("t1.txt", b"content")
        Resource.objects.create(name='t1.txt', file=file_obj, content_type=ContentType.objects.get_for_model(Classroom), object_id=self.classroom.id, uploaded_by=self.teacher)
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse('resource-list') + f'?content_type=classroom&object_id={self.classroom.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_resources_student(self):
        file_obj = SimpleUploadedFile("t1.txt", b"content")
        Resource.objects.create(name='t1.txt', file=file_obj, content_type=ContentType.objects.get_for_model(Classroom), object_id=self.classroom.id, uploaded_by=self.teacher)
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('resource-list') + f'?content_type=classroom&object_id={self.classroom.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_resource_teacher(self):
        file_obj = SimpleUploadedFile("t1.txt", b"content")
        resource = Resource.objects.create(name='t1.txt', file=file_obj, content_type=ContentType.objects.get_for_model(Classroom), object_id=self.classroom.id, uploaded_by=self.teacher)
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(reverse('resource-detail', args=[resource.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Resource.objects.count(), 0)

    def test_delete_resource_student_forbidden(self):
        file_obj = SimpleUploadedFile("t1.txt", b"content")
        resource = Resource.objects.create(name='t1.txt', file=file_obj, content_type=ContentType.objects.get_for_model(Classroom), object_id=self.classroom.id, uploaded_by=self.teacher)
        self.client.force_authenticate(user=self.student)
        response = self.client.delete(reverse('resource-detail', args=[resource.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
