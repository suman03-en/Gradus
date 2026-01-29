# Gradus - Internal Mark Evaluation System

Gradus is a web-based system designed for tracking and maintaining students' internal marks efficiently.

## Tasks Completed

1. Logout view added.
2. User profile editing/adding based on role (teacher or student) implemented.

   * Role identified using `is_student` field in the User model (overriding AbstractUser).
3. Profile retrieval URL implemented: `user/<username>` (read-only).
4. Teacher classroom management pending (edit, update, delete).

   * Student notifications on classroom deletion still pending.
5. Students can join classrooms but cannot leave after joining.
6. Classroom join view refactored.
7. Classroom details view implemented.
8. Teachers can add students by roll number.

## Remaining Tasks

1. Implement features for creating various tasks, assignments, offline assessments, tutorials, and attendance management (daily, bulk, or marks assignment).
2. Allow students to view and submit tasks online.
3. Allow students to view marks received for tasks.
4. Implement dashboard to show total marks or percentage gains per classroom.

## Notes

* Each classroom is associated with a single subject.
