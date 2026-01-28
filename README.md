Gradus - Internal Mark Evaluation System is website for tracking and maintaining the students internal marks . <br>

#tasks to do

1. add logout view
2. edit or add profile details as per teacher or students
 logic : 
 how to know either user is student or teacher
 1.By adding the field "is_student" in User by overriding the abstractuser class
    2. Giving two options while login, login as teacher or students and set context <br>

1/27
1.Add the url to view the profile of any user: user/<username> -> just retrieve only ✅
2. Teacher can edit, update and delete the classrooms :(pending)
 2.1.Notify the students if the classroom is deleted so that they can download the important file.
3.Students can join the classrooms but can't leave after joining .(tick)
4. Refactor the classroom join view (tick)
5. View the classroom details (tick)
6. Add students by teacher with roll no or username.

GET /api/v1/accounts/students?search=<q> → returns a slim list of students (id, username, roll_no, name). Supports search by roll_no/username/name.

POST /api/v1/classrooms/<id>/students/ with body { roll_no: "THA079BEI042" } (or { user_id: "<uuid>" }) → adds that student if found. Backend validates role (student only), avoids duplicates, and returns 200/201 with classroom info.
