import csv
import io
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from accounts.models import User, StudentProfile, TeacherProfile
from classrooms.models import Classroom
from tasks.models import Task, TaskRecord
from tasks.constants import TaskStatus, TaskMode, TaskType


class BulkTaskEvaluationTests(APITestCase):
    def setUp(self):
        # Setup Teacher
        self.teacher = User.objects.create_user(
            username="teacher1", password="password", is_student=False
        )
        TeacherProfile.objects.create(
            user=self.teacher, department="CT", designation="Asst. Prof"
        )

        # Setup Students
        self.student1 = User.objects.create_user(
            username="student1", password="password", is_student=True
        )
        StudentProfile.objects.create(
            user=self.student1, roll_no="THA079BEI001", department="CT"
        )

        self.student2 = User.objects.create_user(
            username="student2", password="password", is_student=True
        )
        StudentProfile.objects.create(
            user=self.student2, roll_no="THA079BEI002", department="CT"
        )

        # Setup Classroom and Task
        self.classroom = Classroom.objects.create(
            name="Math 101",
            description="Math classroom",
            created_by=self.teacher,
        )
        self.classroom.students.add(self.student1, self.student2)

        self.task = Task.objects.create(
            name="Offline Midterm",
            end_date="2026-12-31T23:59:59Z",
            full_marks=100,
            created_by=self.teacher,
            classroom=self.classroom,
            status=TaskStatus.PUBLISHED,
            mode=TaskMode.OFFLINE,
            task_type=TaskType.ASSESSMENT,
        )

        self.client.force_authenticate(user=self.teacher)
        self.url = f"/api/v1/tasks/{self.task.id}/bulk-evaluate/"

    def test_bulk_evaluation_success(self):
        csv_content = "Student Name,Roll No,Marks,Feedback\nJohn Doe,THA079BEI001,85,Good job\nJane Doe,THA079BEI002,92,Excellent\n"
        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "marks.csv"

        response = self.client.post(self.url, {"file": csv_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], 2)
        self.assertEqual(len(response.data["errors"]), 0)

        # Verify database - marks are stored directly on TaskRecord
        record1 = TaskRecord.objects.get(student=self.student1, task=self.task)
        self.assertEqual(record1.marks_obtained, 85.0)
        self.assertEqual(record1.feedback, "Good job")
        self.assertTrue(record1.is_evaluated)
        self.assertIsNone(record1.uploaded_file.name)  # No file for offline tasks

        record2 = TaskRecord.objects.get(student=self.student2, task=self.task)
        self.assertEqual(record2.marks_obtained, 92.0)
        self.assertEqual(record2.feedback, "Excellent")

    def test_bulk_evaluation_with_errors(self):
        # One valid student, one non-existent, one with invalid marks
        csv_content = (
            "Roll No,Marks,Feedback\n"
            "THA079BEI001,85,Valid\n"
            "THA079BEI999,50,Missing Student\n"
            "THA079BEI002,150,Invalid Marks\n"
        )
        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "marks.csv"

        response = self.client.post(self.url, {"file": csv_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data["success"], 1)
        self.assertEqual(len(response.data["errors"]), 2)
        self.assertIn("not found in classroom", response.data["errors"][0])
        self.assertIn("Marks must be between 0", response.data["errors"][1])

    def test_bulk_evaluation_wrong_mode(self):
        self.task.mode = TaskMode.ONLINE
        self.task.save()

        csv_content = "Roll No,Marks,Feedback\nTHA079BEI001,85,Valid\n"
        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "marks.csv"

        response = self.client.post(self.url, {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Bulk upload is only for offline tasks."
        )

    def test_no_fake_submissions_for_offline(self):
        """Verify that offline evaluations don't create unnecessary submission records with files."""
        csv_content = "Roll No,Marks,Feedback\nTHA079BEI001,90,Great\n"
        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "marks.csv"

        self.client.post(self.url, {"file": csv_file}, format="multipart")

        record = TaskRecord.objects.get(student=self.student1, task=self.task)
        self.assertEqual(record.marks_obtained, 90.0)
        self.assertFalse(bool(record.uploaded_file))  # No file attached
        self.assertIsNotNone(record.evaluated_at)  # Has evaluation timestamp

    def test_manual_student_evaluation(self):
        """Test the new direct evaluate-student endpoint (POST)."""
        url = f"/api/v1/tasks/{self.task.id}/evaluate-student/THA079BEI001/"
        data = {"marks_obtained": 75, "feedback": "Consistent performance"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = TaskRecord.objects.get(task=self.task, student=self.student1)
        self.assertEqual(record.marks_obtained, 75)
        self.assertEqual(record.feedback, "Consistent performance")
