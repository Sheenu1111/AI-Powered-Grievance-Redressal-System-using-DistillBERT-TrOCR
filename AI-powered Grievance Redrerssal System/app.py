from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Import configuration
from config import *

# Import database
from database.db_setup import init_database, get_db_connection
from database.models import ComplaintModel

# Import ML models
from models.ocr_model import get_ocr_model
from models.classifier import get_classifier
from models.sentiment_analyzer import get_sentiment_analyzer

# Import utilities
from utils.image_processor import ImageProcessor
from utils.ticket_generator import TicketGenerator

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
init_database()

# ML models are initialized lazily to avoid blocking app startup when
# large ML downloads are unavailable or slow.
ocr_model = None
classifier = None
sentiment_analyzer = None


def get_runtime_models():
    """Load AI models on demand instead of at import time."""
    global ocr_model, classifier, sentiment_analyzer

    if classifier is None:
        classifier = get_classifier()
    if sentiment_analyzer is None:
        sentiment_analyzer = get_sentiment_analyzer()
    return classifier, sentiment_analyzer


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def landing():
    """Landing page - System introduction"""
    return render_template('landing.html')


@app.route('/submit')
def submit_page():
    """Complaint submission form"""
    return render_template('index.html', categories=CATEGORIES)


@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """Handle complaint submission"""
    try:
        complaint_text = None
        original_filename = None
        
        # Check if text complaint or image upload
        if 'complaint_text' in request.form and request.form['complaint_text'].strip():
            # Direct text input
            complaint_text = request.form['complaint_text'].strip()
        
        elif 'complaint_file' in request.files:
            # File upload
            file = request.files['complaint_file']
            
            if file and file.filename and allowed_file(file.filename):
                # Save uploaded file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                original_filename = filename
                
                # Validate image
                if not ImageProcessor.validate_image(filepath):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid image file'
                    }), 400
                
                # Preprocess image
                preprocessed_path = ImageProcessor.preprocess_image(filepath)
                
                # Extract text using OCR when available; otherwise report a clean
                # user-friendly error instead of failing the whole app startup.
                if ocr_model is None:
                    ocr_model = get_ocr_model()
                complaint_text = ocr_model.extract_text(preprocessed_path)

                if not complaint_text:
                    return jsonify({
                        'success': False,
                        'error': 'Could not extract text from image. Please try a clearer image or enter the complaint text manually.'
                    }), 400
        
        else:
            return jsonify({
                'success': False,
                'error': 'Please provide either text or upload an image'
            }), 400
        
        # Analyze complaint using AI models, loading them lazily when needed.
        classifier, sentiment_analyzer = get_runtime_models()
        classification_result = classifier.analyze_complaint(complaint_text)
        category = classification_result['category']
        priority = classification_result['priority']

        sentiment = sentiment_analyzer.analyze_sentiment(complaint_text)
        
        # Assign department
        department = DEPARTMENT_MAPPING.get(category, 'General Administration')
        
        # Generate ticket ID
        ticket_id = TicketGenerator.generate_ticket_id()
        
        # Store in database
        ComplaintModel.create_complaint(
            ticket_id=ticket_id,
            complaint_text=complaint_text,
            category=category,
            priority=priority,
            sentiment=sentiment,
            department=department,
            original_filename=original_filename
        )
        
        # Get resolution timeline
        timeline = RESOLUTION_TIMELINE.get(priority, '7-14 days')
        
        return jsonify({
            'success': True,
            'ticket_id': ticket_id,
            'category': category,
            'priority': priority,
            'sentiment': sentiment,
            'department': department,
            'timeline': timeline,
            'complaint_text': complaint_text
        })
    
    except Exception as e:
        print(f"Error in submit_complaint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your complaint'
        }), 500


@app.route('/check_status')
def check_status():
    """Status checker page"""
    return render_template('status.html')


@app.route('/get_status/<ticket_id>')
def get_status(ticket_id):
    """Get complaint status by ticket ID"""
    try:
        # Validate ticket ID format
        if not TicketGenerator.validate_ticket_id(ticket_id):
            return jsonify({
                'success': False,
                'error': 'Invalid ticket ID format'
            }), 400
        
        # Get complaint from database
        complaint = ComplaintModel.get_complaint_by_ticket_id(ticket_id)
        
        if not complaint:
            return jsonify({
                'success': False,
                'error': 'Ticket ID not found'
            }), 404
        
        # Get resolution timeline
        timeline = RESOLUTION_TIMELINE.get(complaint['priority'], '7-14 days')
        complaint['timeline'] = timeline
        
        return jsonify({
            'success': True,
            'complaint': complaint
        })
    
    except Exception as e:
        print(f"Error in get_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred'
        }), 500


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin and Departmental login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check Super Admin
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['is_super_admin'] = True
            session['department'] = None
            return redirect(url_for('admin_dashboard'))
        
        # Check Department User
        dept_name = ComplaintModel.get_department_user(username, password)
        if dept_name:
            session['admin_logged_in'] = True
            session['is_super_admin'] = False
            session['department'] = dept_name
            return redirect(url_for('admin_dashboard'))
            
        return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Logout for all admin types"""
    session.pop('admin_logged_in', None)
    session.pop('is_super_admin', None)
    session.pop('department', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    """Consolidated dashboard for Super Admin and Department Users"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    is_super = session.get('is_super_admin', False)
    dept = session.get('department')
    
    return render_template('admin.html', 
                          is_super_admin=is_super, 
                          department=dept)


@app.route('/admin/get_complaints')
def get_complaints():
    """Get complaints filtered by department if assigned"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        status_filter = request.args.get('status')
        # If department user, force department filter
        department = session.get('department')
        
        complaints = ComplaintModel.get_all_complaints(status_filter, department)
        
        return jsonify({
            'success': True,
            'complaints': complaints
        })
    
    except Exception as e:
        print(f"Error in get_complaints: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred'
        }), 500


@app.route('/admin/update_status', methods=['POST'])
def update_status():
    """Update complaint status"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        new_status = data.get('status')
        admin_notes = data.get('admin_notes', '')
        
        ComplaintModel.update_complaint_status(ticket_id, new_status, admin_notes)
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully'
        })
    
    except Exception as e:
        print(f"Error in update_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred'
        }), 500


@app.route('/admin/get_statistics')
def get_statistics():
    """Get statistics filtered by department if assigned"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        department = session.get('department')
        stats = ComplaintModel.get_statistics(department)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        print(f"Error in get_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred'
        }), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("STARTING FLASK SERVER...")
    print("Visit: http://127.0.0.1:5000")
    print("Admin Panel: http://127.0.0.1:5000/admin/login")
    print("="*50 + "\n")
    
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)
