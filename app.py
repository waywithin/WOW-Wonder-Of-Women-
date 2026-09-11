import os
import sqlite3
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='.')
CORS(app)  # Enables CORS for all routes so the frontend can connect seamlessly

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
DATABASE = 'wow_awards.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB Limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nominations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            business_name TEXT NOT NULL,
            business_category TEXT NOT NULL,
            business_address TEXT NOT NULL,
            years_in_business INTEGER NOT NULL,
            website TEXT,
            achievements TEXT NOT NULL,
            description TEXT NOT NULL,
            brand_logo_path TEXT,
            business_doc_path TEXT NOT NULL,
            business_photo_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_upload_file(file_obj):
    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(file_obj.filename)
        unique_name = f"{os.urandom(4).hex()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file_obj.save(filepath)
        return unique_name
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/nominate', methods=['POST'])
def nominate():
    try:
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        business_name = request.form.get('business_name')
        business_category = request.form.get('business_category')
        business_address = request.form.get('business_address')
        years_in_business = request.form.get('years_in_business')
        website = request.form.get('website', '')
        achievements = request.form.get('achievements')
        description = request.form.get('description')

        # Log fields to terminal for debugging
        print("Received Form Data:", request.form)
        print("Received Files:", request.files)

        if not all([full_name, email, business_name, business_category, business_address, years_in_business, achievements, description]):
            return jsonify({'error': 'Missing required text fields'}), 400

        brand_logo_file = request.files.get('brand_logo')
        business_doc_file = request.files.get('business_doc')
        business_photo_file = request.files.get('business_photo')

        if not business_doc_file or not business_photo_file:
            return jsonify({'error': 'Business Proof/Document and Business Photo are required'}), 400

        logo_path = save_upload_file(brand_logo_file) if brand_logo_file else None
        doc_path = save_upload_file(business_doc_file)
        photo_path = save_upload_file(business_photo_file)

        if not doc_path or not photo_path:
            return jsonify({'error': 'Invalid file format uploaded'}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO nominations (
                full_name, email, business_name, business_category, business_address,
                years_in_business, website, achievements, description,
                brand_logo_path, business_doc_path, business_photo_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            full_name, email, business_name, business_category, business_address,
            int(years_in_business), website, achievements, description,
            logo_path, doc_path, photo_path
        ))
        conn.commit()
        conn.close()

        print("Database insert successful!")
        return jsonify({'message': 'Nomination submitted successfully!'}), 200

    except Exception as e:
        print("Error on form submission:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)