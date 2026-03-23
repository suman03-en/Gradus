import re
import string
import random
from io import BytesIO
from typing import Optional

from django.db import transaction

from tasks.constants import TaskComponent


def generate_classroom_code():
    # Returns a code like 'AB-C12-D3'
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(random.choices(chars, k=2))
    part2 = "".join(random.choices(chars, k=3))
    part3 = "".join(random.choices(chars, k=2))
    return f"{part1}-{part2}-{part3}"


def is_valid_component_filter(component_filter: Optional[str]) -> bool:
    if not component_filter:
        return True
    return component_filter in {TaskComponent.THEORY, TaskComponent.LAB}


def build_classroom_gradebook_payload(classroom, user, component_filter: Optional[str] = None):
    from tasks.models import TaskRecord
    from .models import ClassroomTaskTypeWeightage

    is_teacher = not getattr(user, "is_student", False) and classroom.created_by == user

    tasks = classroom.tasks.all()
    if component_filter:
        tasks = tasks.filter(assessment_component=component_filter)

    tasks_data = [
        {
            "id": str(t.id),
            "name": t.name,
            "full_marks": t.full_marks,
            "task_type": t.task_type,
            "assessment_component": t.assessment_component,
        }
        for t in tasks
    ]

    weightage_qs = ClassroomTaskTypeWeightage.objects.filter(classroom=classroom)
    if component_filter:
        weightage_qs = weightage_qs.filter(assessment_component=component_filter)

    weightage_by_key = {
        (item.assessment_component, item.task_type): float(item.weightage)
        for item in weightage_qs
        if item.include_in_final and item.weightage > 0
    }

    total_configured_weightage = sum(weightage_by_key.values())
    total_configured_weightage_by_component = {
        TaskComponent.THEORY: sum(
            weight
            for (component, _task_type), weight in weightage_by_key.items()
            if component == TaskComponent.THEORY
        ),
        TaskComponent.LAB: sum(
            weight
            for (component, _task_type), weight in weightage_by_key.items()
            if component == TaskComponent.LAB
        ),
    }

    if is_teacher:
        students = classroom.students.all().select_related("student_profile")
    else:
        students = [user]

    records = TaskRecord.objects.filter(task__in=tasks, student__in=students).select_related(
        "task", "student"
    )

    record_map = {}
    for rec in records:
        record_map[(rec.student_id, rec.task_id)] = rec.marks_obtained

    full_marks_by_key = {}
    for task in tasks:
        key = (task.assessment_component, task.task_type)
        if key in weightage_by_key:
            full_marks_by_key.setdefault(key, 0)
            full_marks_by_key[key] += task.full_marks

    students_data = []
    for st in students:
        st_prof = getattr(st, "student_profile", None)
        roll_no = st_prof.roll_no if st_prof and st_prof.roll_no else st.username

        marks = {}
        total_obtained = 0
        total_full_marks = 0
        obtained_by_key = {}
        component_totals = {
            TaskComponent.THEORY: {"obtained": 0, "full_marks": 0},
            TaskComponent.LAB: {"obtained": 0, "full_marks": 0},
        }

        for t in tasks:
            total_full_marks += t.full_marks
            component_totals[t.assessment_component]["full_marks"] += t.full_marks
            eval_marks = record_map.get((st.id, t.id))
            if eval_marks is not None:
                marks[str(t.id)] = eval_marks
                total_obtained += eval_marks
                component_totals[t.assessment_component]["obtained"] += eval_marks
                key = (t.assessment_component, t.task_type)
                obtained_by_key.setdefault(key, 0)
                obtained_by_key[key] += eval_marks

        weighted_accumulator = 0
        effective_weightage = 0
        for key, weightage in weightage_by_key.items():
            type_full_marks = full_marks_by_key.get(key, 0)
            if type_full_marks <= 0:
                continue
            type_obtained_marks = obtained_by_key.get(key, 0)
            weighted_accumulator += (type_obtained_marks / type_full_marks) * weightage
            effective_weightage += weightage

        final_marks = 0
        if effective_weightage > 0:
            final_marks = round((weighted_accumulator / effective_weightage) * 100, 2)

        students_data.append(
            {
                "id": str(st.id),
                "username": st.username,
                "roll_no": roll_no,
                "marks": marks,
                "total_obtained": total_obtained,
                "total_full_marks": total_full_marks,
                "final_marks": final_marks,
                "component_totals": component_totals,
            }
        )

    return {
        "classroom": {"id": str(classroom.id), "name": classroom.name},
        "active_component_filter": component_filter,
        "tasks": tasks_data,
        "weightage_config": [
            {
                "assessment_component": assessment_component,
                "task_type": task_type,
                "include_in_final": True,
                "weightage": weightage,
            }
            for (assessment_component, task_type), weightage in weightage_by_key.items()
        ],
        "total_configured_weightage": total_configured_weightage,
        "total_configured_weightage_by_component": total_configured_weightage_by_component,
        "students": students_data,
    }


def build_weightage_config_payload(classroom):
    from tasks.constants import TaskType
    from .models import ClassroomTaskTypeWeightage

    existing = {
        (item.assessment_component, item.task_type): item
        for item in ClassroomTaskTypeWeightage.objects.filter(classroom=classroom)
    }

    payload = []
    for assessment_component, _ in TaskComponent.choices:
        for task_type, _ in TaskType.choices:
            item = existing.get((assessment_component, task_type))
            payload.append(
                {
                    "assessment_component": assessment_component,
                    "task_type": task_type,
                    "include_in_final": item.include_in_final if item else False,
                    "weightage": float(item.weightage) if item else 0,
                }
            )

    total_weightage = sum(row["weightage"] for row in payload if row["include_in_final"])
    total_weightage_by_component = {
        TaskComponent.THEORY: sum(
            row["weightage"]
            for row in payload
            if row["include_in_final"]
            and row["assessment_component"] == TaskComponent.THEORY
        ),
        TaskComponent.LAB: sum(
            row["weightage"]
            for row in payload
            if row["include_in_final"]
            and row["assessment_component"] == TaskComponent.LAB
        ),
    }

    return {
        "weightages": payload,
        "total_configured_weightage": total_weightage,
        "total_configured_weightage_by_component": total_weightage_by_component,
    }


def upsert_classroom_weightages(classroom, weightages_data):
    from .models import ClassroomTaskTypeWeightage

    with transaction.atomic():
        for item in weightages_data:
            ClassroomTaskTypeWeightage.objects.update_or_create(
                classroom=classroom,
                assessment_component=item["assessment_component"],
                task_type=item["task_type"],
                defaults={
                    "include_in_final": item["include_in_final"],
                    "weightage": item["weightage"],
                },
            )


def build_gradebook_excel_file(classroom, user, component: str):
    if not is_valid_component_filter(component):
        raise ValueError("Invalid component filter")

    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise ImportError("openpyxl is required for Excel export") from exc

    payload = build_classroom_gradebook_payload(
        classroom=classroom,
        user=user,
        component_filter=component,
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = component.capitalize()

    headers = ["Name", "Roll No", "Marks"]
    sheet.append(headers)

    for student in payload["students"]:
        marks = student.get("total_obtained", 0)
        sheet.append([
            student.get("username", ""),
            student.get("roll_no", ""),
            marks if marks is not None else 0,
        ])

    safe_classroom_name = re.sub(r"[^A-Za-z0-9_-]+", "_", classroom.name).strip("_")
    if not safe_classroom_name:
        safe_classroom_name = "classroom"

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)

    filename = f"{safe_classroom_name}_{component}_marks.xlsx"
    return stream.getvalue(), filename
