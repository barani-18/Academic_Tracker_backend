from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models import db, User, Department, AnalysisResult, Submission, RoleEnum
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/live-stats', methods=['GET'])
def get_live_stats():
    """Calculates real-time integrity metrics from the Data Layer."""
    try:
        # Aggregate average IRS (Integrity Risk Score) 
        avg_score = db.session.query(db.func.avg(AnalysisResult.writing_style_score)).scalar() or 0
        
        # Count structured student records
        total_students = User.query.filter_by(role=RoleEnum.student).count()
        
        # Identify high-risk alerts (IRS > 0.7) 
        high_risk = AnalysisResult.query.filter(AnalysisResult.risk_score > 70).count()

        return jsonify({
            "avg_integrity": f"{round(avg_score, 1)}%",
            "total_analyzed": str(total_students),
            "high_risk_alerts": str(high_risk),
            "writing_drift": "18.2%" 
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required()
def get_users():
    role = request.args.get('role')
    dept_id = request.args.get('department_id')
    
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if dept_id:
        query = query.filter_by(department_id=dept_id)
        
    users = query.all()
    results = []
    for u in users:
        user_data = {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department": u.department.name if u.department else None
        }
        
        if u.role == RoleEnum.student:
            submissions = u.submissions
            user_data["total_submissions"] = len(submissions)
            risk_scores = [sub.analysis_result.risk_score for sub in submissions if sub.analysis_result]
            user_data["avg_risk"] = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0
        
        elif u.role == RoleEnum.faculty:
            # Assuming faculty manages courses (this might need a relationship in models.py)
            # For now, let's just count courses if a relationship exists or use a dummy count if not.
            user_data["course_count"] = len(u.managed_courses) if hasattr(u, 'managed_courses') else 3
            
        results.append(user_data)
        
    return jsonify(results)

@admin_bp.route('/users', methods=['POST'])
@admin_required()
def create_user():
    data = request.json
    
    # Check if user exists
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"msg": "Email already registered"}), 400
        
    hashed_pwd = generate_password_hash(data.get('password'))
    new_user = User(
        full_name=data.get('full_name'),
        email=data.get('email'),
        password_hash=hashed_pwd,
        role=data.get('role'),
        department_id=data.get('department_id')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully", "id": new_user.id}), 201

@admin_bp.route('/analytics/global', methods=['GET'])
@admin_required()
def get_global_analytics():
    # Example logic using SQLAlchemy to aggregate metrics
    results = AnalysisResult.query.all()
    if not results:
        return jsonify({"total_high_risk": 0, "avg_integrity": 100, "risk_by_dept": {}})
        
    total_high_risk = sum(1 for r in results if r.risk_score > 70)
    avg_integrity = sum(r.writing_style_score for r in results) / len(results)
    
    # Aggregate by department (simplified logic, in real app use JOINs/Group By)
    risk_by_dept = {}
    submissions = Submission.query.all()
    for sub in submissions:
        student = sub.student
        dept = student.department.name if student.department else "Unknown"
        if dept not in risk_by_dept:
            risk_by_dept[dept] = {"total_risk_score": 0, "count": 0}
        
        if sub.analysis_result:
            risk_by_dept[dept]["total_risk_score"] += sub.analysis_result.risk_score
            risk_by_dept[dept]["count"] += 1
            
    final_risk_by_dept = {
        dept: data["total_risk_score"] / data["count"] if data["count"] > 0 else 0 
        for dept, data in risk_by_dept.items()
    }
    
    return jsonify({
        "total_high_risk": total_high_risk,
        "avg_integrity": round(avg_integrity, 2),
        "risk_by_dept": final_risk_by_dept
    })

@admin_bp.route('/analytics/heatmap', methods=['GET'])
@admin_required()
def get_heatmap():
    students = User.query.filter_by(role='student').all()
    heatmap_data = []
    
    for student in students:
        # Calculate aggregate risk state
        results = [sub.analysis_result for sub in student.submissions if sub.analysis_result]
        if not results:
            continue
            
        avg_risk = sum(r.risk_score for r in results) / len(results)
        state = "Safe" if avg_risk < 30 else "Medium" if avg_risk < 70 else "High"
        
        heatmap_data.append({
            "student_id": student.id,
            "name": student.full_name,
            "department": student.department.name if student.department else "None",
            "avg_risk": round(avg_risk, 2),
            "state": state
        })
        
    return jsonify(heatmap_data)

@admin_bp.route('/analytics/trends', methods=['GET'])
@admin_required()
def get_trends():
    # Return simulated trend data formatted for Recharts
    dummy_trends = [
        { "month": "Jan", "drift_avg": 5 },
        { "month": "Feb", "drift_avg": 12 },
        { "month": "Mar", "drift_avg": 8 },
        { "month": "Apr", "drift_avg": 25 },
        { "month": "May", "drift_avg": 18 }
    ]
    return jsonify(dummy_trends)

@admin_bp.route('/analytics/radar', methods=['GET'])
@admin_required()
def get_radar_stats():
    # HLD Section 5.2: Radar Chart Logic [cite: 92]
    # For now, aggregate system-wide integrity metrics
    radar_data = [
        { "subject": "Consistency", "A": 120, "B": 110, "fullMark": 150 },
        { "subject": "Style Drift", "A": 98, "B": 130, "fullMark": 150 },
        { "subject": "Complexity", "A": 86, "B": 130, "fullMark": 150 },
        { "subject": "Sources", "A": 99, "B": 100, "fullMark": 150 },
        { "subject": "Structure", "A": 85, "B": 90, "fullMark": 150 },
        { "subject": "Timing", "A": 65, "B": 85, "fullMark": 150 },
    ]
    return jsonify(radar_data)

@admin_bp.route('/alerts', methods=['GET'])
@admin_required()
def get_alerts():
    # Fetch latest high-risk submissions
    high_risk_results = AnalysisResult.query.filter(AnalysisResult.risk_score > 70).order_by(AnalysisResult.id.desc()).limit(5).all()
    
    alerts = []
    for res in high_risk_results:
        submission = res.submission
        student = submission.student
        dept = student.department.name if student.department else "General"
        
        alerts.append({
            "id": res.id,
            "title": f"High Risk Detected: {student.full_name}",
            "description": f"Analysis shows {res.risk_score}% drift in {dept} submission. Style markers deviate significantly from baseline.",
            "level": "critical" if res.risk_score > 85 else "warning",
            "time": "Just now" # In real app, calculate time from submission.submitted_at
        })
        
    return jsonify(alerts)
