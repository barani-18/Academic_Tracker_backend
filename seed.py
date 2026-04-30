import os
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash
import json

from app import create_app
from models import db, User, Department, Course, Enrollment, Assignment, Submission, AnalysisResult, RoleEnum

app = create_app()

def seed_database():
    with app.app_context():
        # Reset database
        print("Dropping all tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()

        print("Seeding Departments...")
        cs_dept = Department(name="Computer Science")
        arts_dept = Department(name="Liberal Arts")
        db.session.add_all([cs_dept, arts_dept])
        db.session.commit()

        print("Seeding Users...")
        admin = User(
            full_name="System Admin", 
            email="admin@labia.edu", 
            password_hash=generate_password_hash("admin123"),
            role=RoleEnum.admin
        )
        
        fac1 = User(
            full_name="Dr. Alan Turing", 
            email="alan@labia.edu", 
            password_hash=generate_password_hash("fac123"),
            role=RoleEnum.faculty,
            department_id=cs_dept.id
        )
        fac2 = User(
            full_name="Dr. Ada Lovelace", 
            email="ada@labia.edu", 
            password_hash=generate_password_hash("fac123"),
            role=RoleEnum.faculty,
            department_id=cs_dept.id
        )
        
        db.session.add_all([admin, fac1, fac2])
        db.session.commit()

        # Seed 10 Students
        print("Seeding Students...")
        students = []
        for i in range(1, 11):
            student = User(
                full_name=f"Student {i}",
                email=f"student{i}@labia.edu",
                password_hash=generate_password_hash("stud123"),
                role=RoleEnum.student,
                department_id=cs_dept.id if i % 2 == 0 else arts_dept.id
            )
            students.append(student)
        
        db.session.add_all(students)
        db.session.commit()

        print("Seeding Courses and Enrollments...")
        course1 = Course(name="Data Structures 101", faculty_id=fac1.id)
        course2 = Course(name="AI Ethics", faculty_id=fac2.id)
        db.session.add_all([course1, course2])
        db.session.commit()

        # Enroll all students in both courses for simplicity
        enrollments = []
        for s in students:
            enrollments.append(Enrollment(student_id=s.id, course_id=course1.id))
            enrollments.append(Enrollment(student_id=s.id, course_id=course2.id))
        db.session.add_all(enrollments)
        db.session.commit()

        print("Seeding Assignments...")
        now = datetime.utcnow()
        assignments = [
            Assignment(title="Tree Traversal Lab", course_id=course1.id, deadline=now - timedelta(days=30)),
            Assignment(title="Graph Theory Project", course_id=course1.id, deadline=now - timedelta(days=15)),
            Assignment(title="Final Algorithms Exam", course_id=course1.id, deadline=now + timedelta(days=10)),
            Assignment(title="Utilitarianism Essay", course_id=course2.id, deadline=now - timedelta(days=20)),
            Assignment(title="AI Bias Report", course_id=course2.id, deadline=now - timedelta(days=5)),
        ]
        db.session.add_all(assignments)
        db.session.commit()

        print("Seeding Submissions and Analysis Results...")
        submissions = []
        results = []
        
        # Make one student consistently high risk (Student 3)
        high_risk_student_id = students[2].id

        for student in students:
            for assignment in assignments[:-1]: # Don't submit the future assignment yet
                # Random submission time
                sub_time = assignment.deadline - timedelta(hours=random.randint(-5, 48))
                
                sub = Submission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    text_content=f"This is a dummy submission by student {student.id} for assignment {assignment.id}.",
                    submitted_at=sub_time
                )
                db.session.add(sub)
                db.session.flush() # get sub.id

                # Generate Analysis Result
                is_high_risk = student.id == high_risk_student_id
                
                if is_high_risk and assignment.id > 1:
                    # Simulate Drift!
                    style_score = random.uniform(85, 99)
                    ai_prob = random.uniform(80, 95)
                    risk_score = random.uniform(85, 100)
                    insights = "Drastic change in vocabulary. High correlation with GPT-4 signature."
                else:
                    style_score = random.uniform(40, 70)
                    ai_prob = random.uniform(0, 15)
                    risk_score = random.uniform(0, 20)
                    insights = "Writing style consistent with past submissions."
                
                res = AnalysisResult(
                    submission_id=sub.id,
                    writing_style_score=style_score,
                    ai_probability=ai_prob,
                    risk_score=risk_score,
                    generated_insights=json.dumps({"summary": insights})
                )
                db.session.add(res)
                
        db.session.commit()
        print("Database seeding complete!")

if __name__ == '__main__':
    seed_database()
