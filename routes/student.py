from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import db, User, Course, Submission, Assignment

student_bp = Blueprint('student', __name__)

@student_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assignment():
    student_id = get_jwt_identity()
    data = request.json
    
    assignment_id = data.get('assignment_id')
    text_content = data.get('text_content')
    
    if not assignment_id or not text_content:
        return jsonify({"msg": "Missing assignment_id or text_content"}), 400
        
    new_submission = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        text_content=text_content
    )
    db.session.add(new_submission)
    db.session.commit()
    
    return jsonify({"msg": "Submission successful", "id": new_submission.id}), 201

@student_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    submissions = Submission.query.filter_by(student_id=user_id).order_by(Submission.submitted_at.desc()).all()
    
    history = []
    for sub in submissions:
        res = sub.analysis_result
        course_name = "General"
        if sub.assignment and sub.assignment.course:
            course_name = sub.assignment.course.name
            
        history.append({
            "id": sub.id,
            "title": sub.assignment.title if sub.assignment else f"Assignment {sub.assignment_id}",
            "course": course_name,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else "",
            "status": "Analyzed" if res else "Pending Analysis",
            "risk": "Safe" if res and res.risk_score < 30 else ("Medium" if res and res.risk_score < 70 else ("High" if res else "Pending"))
        })
        
    return jsonify(history)

@student_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    # Return all courses since department filtering isn't in this schema version
    courses = Course.query.all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "instructor": c.faculty.full_name if c.faculty else "TBA"
    } for c in courses])

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    student = User.query.get(user_id)
    if not student:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify({
        "name": student.full_name,
        "email": student.email,
        "studentId": f"ID-2024-{student.id:03d}",
        "dept": student.department.name if student.department else "General"
    }), 200
