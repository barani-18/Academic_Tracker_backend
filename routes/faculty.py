import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, User, Course, Enrollment, Submission, AnalysisResult, Assignment
from routes.auth import faculty_required
import json
from analyzer import analyze_student_drift

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/students', methods=['GET'])
@faculty_required()
def get_my_students():
    faculty_id = get_jwt_identity()
    
    # Get courses taught by this faculty
    courses = Course.query.filter_by(faculty_id=faculty_id).all()
    course_ids = [c.id for c in courses]
    
    if not course_ids:
        return jsonify([])
        
    # Get students enrolled in these courses
    enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()
    student_ids = list(set([e.student_id for e in enrollments]))
    
    students = User.query.filter(User.id.in_(student_ids)).all()
    
    return jsonify([{
        "id": s.id,
        "name": s.full_name,
        "idNum": f"ID-2026-{s.id:03d}",
        "dept": s.department.name if s.department else "N/A"
    } for s in students])

@faculty_bp.route('/student/<int:student_id>/profile', methods=['GET'])
@faculty_required()
def get_student_profile(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({"msg": "User is not a student"}), 400
        
    submissions = Submission.query.filter_by(student_id=student_id).order_by(Submission.submitted_at).all()
    
    history = []
    for sub in submissions:
        res = sub.analysis_result
        history.append({
            "submission_id": sub.id,
            "assignment_title": sub.assignment.title,
            "submitted_at": sub.submitted_at.isoformat(),
            "writing_score": res.writing_style_score if res else None,
            "risk_score": res.risk_score if res else None
        })
        
    return jsonify({
        "student_id": student.id,
        "name": student.full_name,
        "history": history
    })

@faculty_bp.route('/pending_submissions', methods=['GET'])
@faculty_required()
def get_pending_submissions():
    faculty_id = get_jwt_identity()
    
    # Get courses taught by this faculty
    courses = Course.query.filter_by(faculty_id=faculty_id).all()
    course_ids = [c.id for c in courses]
    
    # Get unanalyzed submissions for these courses
    # A submission is unanalyzed if it has no AnalysisResult
    # Join with Assignment to check course
    pending = db.session.query(Submission).join(Assignment).filter(
        Assignment.course_id.in_(course_ids),
        ~Submission.analysis_result.has()
    ).all()
    
    return jsonify([{
        "id": sub.id,
        "title": sub.assignment.title if sub.assignment else f"Assignment {sub.assignment_id}",
        "studentName": sub.student.full_name if sub.student else "Unknown",
        "studentId": f"ID-2026-{sub.student_id:03d}",
        "course": sub.assignment.course.name if sub.assignment and sub.assignment.course else "Unknown",
        "submitted_at": sub.submitted_at.isoformat()
    } for sub in pending])

@faculty_bp.route('/analyze/<int:submission_id>', methods=['POST'])
@faculty_required()
def analyze_existing_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    
    if submission.analysis_result:
        return jsonify({"msg": "Already analyzed"}), 400
        
    student_id = submission.student_id
    text_content = submission.text_content
    
    # Get past submissions to establish a baseline
    past_subs = Submission.query.filter(Submission.student_id == student_id, Submission.id != submission_id).all()
    
    # Use analyzer.py
    past_texts = [sub.text_content for sub in past_subs]
    analysis = analyze_student_drift(text_content, past_texts)
    
    result = AnalysisResult(
        submission_id=submission.id,
        writing_style_score=analysis['writing_style_score'],
        ai_probability=analysis['ai_probability'],
        risk_score=analysis['risk_score'],
        generated_insights=json.dumps({"summary": " ".join(analysis['insights'])})
    )
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        "styleScore": analysis['writing_style_score'],
        "aiProbability": analysis['ai_probability'],
        "riskScore": analysis['risk_score'],
        "driftDetected": analysis['risk_score'] > 30,
        "insights": " ".join(analysis['insights'])
    }), 200

@faculty_bp.route('/analyze/submission', methods=['POST'])
@faculty_required()
def analyze_submission():
    """
    CORE ENDPOINT
    Accepts text content and student_id. 
    Simulates NLP analysis using Pandas & Numpy.
    """
    data = request.json
    student_id = data.get('student_id')
    text_content = data.get('text_content')
    assignment_id = data.get('assignment_id')
    
    if not all([student_id, text_content, assignment_id]):
        return jsonify({"msg": "Missing required fields"}), 400
        
    # Get past submissions to establish a baseline
    past_subs = Submission.query.filter_by(student_id=student_id).all()
    
    # 1. Simulate NLP Metrics extraction using random for the NEW text
    random.seed(len(text_content)) # Deterministic simulation based on text length
    new_vocab_complexity = random.uniform(40, 95)
    new_sentence_length_variance = random.uniform(10, 30)
    
    # 2. Establish Baseline from past analysis results
    if past_subs:
        # We'll use basic python to calculate the mean of past scores
        past_results = [s.analysis_result for s in past_subs if s.analysis_result]
        if past_results:
            style_scores = [r.writing_style_score for r in past_results]
            baseline_style = sum(style_scores) / len(style_scores)
        else:
            baseline_style = 70.0
    else:
        baseline_style = 70.0
        
    # 3. Calculate Drift
    # Let's say if vocab complexity is way higher than baseline, it's a huge drift
    # Here we just simulate a formula
    drift_factor = abs(new_vocab_complexity - baseline_style)
    
    # Calculate Risk & AI Probability
    if drift_factor > 20:
        ai_probability = random.uniform(70, 99)
        risk_score = random.uniform(60, 95)
        insights = "Sentence structure complexity increased dramatically. High AI probability detected."
    else:
        ai_probability = random.uniform(0, 15)
        risk_score = random.uniform(0, 20)
        insights = "Writing style is consistent with historical baseline."
        
    # Save the submission
    new_submission = Submission(
        assignment_id=assignment_id,
        student_id=student_id,
        text_content=text_content
    )
    db.session.add(new_submission)
    db.session.flush() # Get the ID
    
    # Save Analysis Result
    result = AnalysisResult(
        submission_id=new_submission.id,
        writing_style_score=new_vocab_complexity,
        ai_probability=ai_probability,
        risk_score=risk_score,
        generated_insights=json.dumps({"summary": insights, "drift": drift_factor})
    )
    db.session.add(result)
    db.session.commit()
    
    return jsonify({
        "submission_id": new_submission.id,
        "writing_style_score": round(new_vocab_complexity, 2),
        "ai_probability": round(ai_probability, 2),
        "risk_score": round(risk_score, 2),
        "insights": insights
    }), 201

@faculty_bp.route('/class_overview', methods=['GET'])
@faculty_required()
def get_class_overview():
    faculty_id = get_jwt_identity()
    faculty = User.query.get(faculty_id)
    
    # Get students in faculty's department
    students = User.query.filter_by(role='student', department_id=faculty.department_id).all()
    
    results = []
    for s in students:
        # Calculate latest integrity score from latest submission
        latest_sub = Submission.query.filter_by(student_id=s.id).order_by(Submission.submitted_at.desc()).first()
        score = latest_sub.analysis_result.risk_score if latest_sub and latest_sub.analysis_result else 90
        
        results.append({
            "id": s.id,
            "name": s.full_name,
            "idNum": f"ID-2026-{s.id:03d}",
            "risk": "safe" if score < 40 else "medium" if score < 70 else "high",
            "score": score,
            "lastSub": "Recently" if latest_sub else "Never",
            "dept": s.department.name if s.department else "N/A",
            "submissions": len(s.submissions)
        })
        
    return jsonify(results)
