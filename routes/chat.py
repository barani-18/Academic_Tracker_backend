from flask import Blueprint, request, jsonify
from models import db, User, Course, Submission, Assignment

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/ask', methods=['POST'])
def ask_chatbot():
    data = request.json
    query = data.get('query', '').lower()
    
    if not query:
        return jsonify({"reply": "Please ask a question."})

    # Basic keyword matching to query the MySQL database
    if 'student' in query:
        student_count = User.query.filter_by(role='student').count()
        return jsonify({"reply": f"We currently have {student_count} registered students in the system. They can submit their assignments through the portal for NLP analysis."})
        
    elif 'faculty' in query:
        faculty_count = User.query.filter_by(role='faculty').count()
        return jsonify({"reply": f"There are {faculty_count} faculty members managing courses. They use the Analysis Lab to check incoming submissions for academic integrity."})
        
    elif 'admin' in query:
        admin_count = User.query.filter_by(role='admin').count()
        return jsonify({"reply": f"The system is managed by {admin_count} administrators who oversee global analytics and risk heatmaps."})
        
    elif 'course' in query or 'class' in query:
        course_count = Course.query.count()
        return jsonify({"reply": f"There are currently {course_count} active courses hosted in the LABIA system."})
        
    elif 'submission' in query or 'assignment' in query:
        sub_count = Submission.query.count()
        assign_count = Assignment.query.count()
        return jsonify({"reply": f"Students have made a total of {sub_count} submissions across {assign_count} assignments so far."})
        
    elif 'integrity' in query or 'nlp' in query or 'analysis' in query:
        return jsonify({"reply": "The Integrity Analytics engine uses NLP (spaCy and NLTK) to analyze lexical diversity, sentence length, and POS patterns to establish a unique writing fingerprint for each student."})
        
    elif 'hello' in query or 'hi' in query:
        return jsonify({"reply": "Hello! I am the LABIA System Assistant. I am directly connected to the MySQL database. Ask me about students, faculty, courses, or submissions!"})
        
    else:
        return jsonify({"reply": "I'm not sure about that. Try asking about 'students', 'faculty', 'courses', or 'submissions' to query the live database."})
