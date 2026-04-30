import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# HLD Module 03: Analytics Module Integration
from analyzer import analyze_student_drift
from models import db, User, AnalysisResult, Submission, RoleEnum

# Load environment variables (Database URI, API Keys)
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # ─── CONFIGURATION & SECURITY ───
    # HLD Section 7.1: Role-based access control and JWT configuration
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:5175", 
        "http://localhost:5176", 
        "http://127.0.0.1:5176",
        "https://academic-tracker-dun.vercel.app"
    ])
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///labia.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-labia-key-for-dev')
    
    # Initialize Extensions
    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)
    
    # ─── BLUEPRINT REGISTRATION ───
    # HLD Section 3.3: Decoupled Controller tier
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.faculty import faculty_bp
    from routes.student import student_bp
    from routes.chat import chat_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # ─── SYSTEM HEALTH ───
    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "LABIA API is running"}

    # ─── HOME ROUTE ───
    @app.route('/')
    def home():
        return {"message": "Welcome to the Academic Tracker API!"}

    # ─── FACULTY RISK DETECTION ROUTES ───
    # HLD Module 04: Risk Detection Module 
    @app.route('/api/faculty/analyze', methods=['POST'])
    def analyze_submission():
        """
        Executes the sequential analytical pipeline:
        Preprocessing -> NLP Analytics -> Risk Evaluation
        """
        data = request.json
        text = data.get('text', '')
        student_id = data.get('student_id')

        if not text or not student_id:
            return jsonify({"error": "Missing text or student ID"}), 400

        try:
            # 1. Access Data Layer for longitudinal baseline
            past_submissions = Submission.query.filter_by(student_id=student_id).all()
            past_texts = [s.text_content for s in past_submissions]

            # 2. Trigger Analytics Module (NLTK Stylistic Fingerprinting) 
            analysis = analyze_student_drift(text, past_texts)

            # 3. Risk Evaluation: Compute IRS and generate actionable insights 
            return jsonify({
                "styleScore": analysis['writing_style_score'],
                "riskScore": analysis['risk_score'],
                "aiProbability": analysis['ai_probability'],
                "driftDetected": analysis['risk_score'] > 70, # Threshold from HLD 
                "insights": analysis['insights']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    # Use Render's dynamically assigned PORT, or fall back to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)