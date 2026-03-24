from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

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


class ClassroomAttendanceTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="attendance_teacher", password="password", is_student=False
        )
        self.student_a = User.objects.create_user(
            username="student_a", password="password", is_student=True
        )
        self.student_b = User.objects.create_user(
            username="student_b", password="password", is_student=True
        )

        StudentProfile.objects.create(
            user=self.student_a,
            roll_no="THA079BEI111",
            department="CT",
        )
        StudentProfile.objects.create(
            user=self.student_b,
            roll_no="THA079BEI112",
            department="CT",
        )

        self.classroom = Classroom.objects.create(
            name="Attendance Classroom",
            description="Attendance testing",
            created_by=self.teacher,
        )
        self.classroom.students.add(self.student_a, self.student_b)

    def test_teacher_can_upsert_attendance(self):
        self.client.force_authenticate(user=self.teacher)
        url = f"/api/v1/classrooms/{self.classroom.id}/attendance/"
        payload = {
            "date": "2026-03-24",
            "assessment_component": "theory",
            "entries": [
                {"student_id": str(self.student_a.id), "is_present": True},
                {"student_id": str(self.student_b.id), "is_present": False},
            ],
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_upsert_attendance(self):
        self.client.force_authenticate(user=self.student_a)
        url = f"/api/v1/classrooms/{self.classroom.id}/attendance/"
        payload = {
            "date": "2026-03-24",
            "assessment_component": "theory",
            "entries": [{"student_id": str(self.student_a.id), "is_present": True}],
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_sees_only_own_attendance_summary(self):
        self.client.force_authenticate(user=self.teacher)
        url = f"/api/v1/classrooms/{self.classroom.id}/attendance/"
        self.client.post(
            url,
            {
                "date": "2026-03-24",
                "assessment_component": "theory",
                "entries": [
                    {"student_id": str(self.student_a.id), "is_present": True},
                    {"student_id": str(self.student_b.id), "is_present": False},
                ],
            },
            format="json",
        )

        self.client.force_authenticate(user=self.student_a)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_teacher"])
        self.assertEqual(len(response.data["attendance_summary"]), 1)
        self.assertEqual(
            response.data["attendance_summary"][0]["student_id"], str(self.student_a.id)
        )

    def test_teacher_can_upload_attendance_csv(self):
        self.client.force_authenticate(user=self.teacher)
        url = f"/api/v1/classrooms/{self.classroom.id}/attendance/bulk/csv/"

        content = (
            "date,assessment_component,roll_no,is_present,note\n"
            "2026-03-20,theory,THA079BEI111,1,Week 1\n"
            "2026-03-20,theory,THA079BEI112,0,Week 1\n"
        )
        upload = SimpleUploadedFile(
            "attendance.csv", content.encode("utf-8"), content_type="text/csv"
        )

        response = self.client.post(url, {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_upload_attendance_csv(self):
        self.client.force_authenticate(user=self.student_a)
        url = f"/api/v1/classrooms/{self.classroom.id}/attendance/bulk/csv/"

        content = (
            "date,assessment_component,roll_no,is_present\n"
            "2026-03-20,theory,THA079BEI111,1\n"
        )
        upload = SimpleUploadedFile(
            "attendance.csv", content.encode("utf-8"), content_type="text/csv"
        )

        response = self.client.post(url, {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
