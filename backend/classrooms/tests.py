from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import StudentProfile, User
from .models import Classroom


class ClassroomMultiTeacherTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_teacher", password="password", is_student=False
        )
        self.co_teacher = User.objects.create_user(
            username="co_teacher", password="password", is_student=False
        )
        self.other_teacher = User.objects.create_user(
            username="other_teacher", password="password", is_student=False
        )
        self.student_user = User.objects.create_user(
            username="student_user", password="password", is_student=True
        )
        StudentProfile.objects.create(
            user=self.student_user,
            roll_no="THA079BEI042",
            department="CT",
        )

        self.classroom = Classroom.objects.create(
            name="Networks",
            description="Computer Networks",
            created_by=self.owner,
        )

    def test_owner_can_add_co_teacher(self):
        self.client.force_authenticate(user=self.owner)
        url = f"/api/v1/classrooms/{self.classroom.id}/teachers/"

        response = self.client.post(url, {"username": "co_teacher"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.classroom.teachers.filter(id=self.co_teacher.id).exists())

    def test_non_owner_cannot_add_co_teacher(self):
        self.client.force_authenticate(user=self.other_teacher)
        url = f"/api/v1/classrooms/{self.classroom.id}/teachers/"

        response = self.client.post(url, {"username": "co_teacher"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_co_teacher_can_add_student(self):
        self.classroom.teachers.add(self.co_teacher)
        self.client.force_authenticate(user=self.co_teacher)
        url = f"/api/v1/classrooms/{self.classroom.id}/students/"

        response = self.client.post(url, {"roll_no": "THA079BEI042"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            self.classroom.students.filter(id=self.student_user.id).exists()
        )
