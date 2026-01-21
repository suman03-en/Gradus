from django.db import models

class Semester(models.IntegerChoices):
    SEM_1 = 1, 'Semester 1'
    SEM_2 = 2, 'Semester 2'
    SEM_3 = 3, 'Semester 3'
    SEM_4 = 4, 'Semester 4'
    SEM_5 = 5, 'Semester 5'
    SEM_6 = 6, 'Semester 6'
    SEM_7 = 7, 'Semester 7'
    SEM_8 = 8, 'Semester 8'

class Department(models.TextChoices):
    ELECTRONIC_COMPUTER = 'EC', "Electronics and Computer Engineering"
    MECHANICAL_AUTOMOBILE = "MA", "Mechanical and Automobile Engineering"
    CIVIL_ARCHITECTURE = "CA", "Civil and Architecture Engineering"
    INDUSTRIAL = "IN", "Industrial Engineering"

class Section(models.TextChoices):
    GROUP_A = "A", "Group A"
    GROUP_B = "B", "Group B"
    GROUP_C = "C", "Group C"
    GROUP_D = "D", "Group D"

class Designation(models.TextChoices):
    # Leadership
    HOD = 'HOD', 'Head of Department'
    PROFESSOR = 'PROF', 'Professor'
    
    # Senior Faculty
    ASSOCIATE_PROF = 'ASSOC', 'Associate Professor'
    ASSISTANT_PROF = 'ASST', 'Assistant Professor'
    
    # Junior / Visiting Faculty
    LECTURER = 'LECT', 'Lecturer'
    ADJUNCT_FACULTY = 'ADJ', 'Adjunct Faculty'
    VISITING_FACULTY = 'VISIT', 'Visiting Faculty'
    
    # Research / Support
    TEACHING_ASSISTANT = 'TA', 'Teaching Assistant'
    LAB_INSTRUCTOR = 'LAB', 'Lab Instructor'