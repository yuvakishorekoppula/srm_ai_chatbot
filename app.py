import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google import genai
from dotenv import load_dotenv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "srm_secret_key_123")

DB_PATH = 'srm_assistant.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Configure Gemini API using the modern google-genai SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Validate API Key setup
IS_API_KEY_SETUP = GEMINI_API_KEY not in ["", "YOUR_API_KEY_HERE"]
SELECTED_MODEL = 'models/gemini-flash-latest'
client = None

if IS_API_KEY_SETUP:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Gemini Client initialized. Using model: {SELECTED_MODEL}")
    except Exception as e:
        print(f"Failed to initialize Gemini Client: {e}")
else:
    print("WARNING: GEMINI_API_KEY is not set in .env.")

# Reference Links Context
COLLEGE_CONTEXT = """
Official SRM Reference Links:
Admissions: https://www.srmist.edu.in/admission
Departments: https://www.srmist.edu.in/engineering
Facilities: https://www.srmist.edu.in/campus-life
Library: https://www.srmist.edu.in/library

If students need more information, always refer them to these official links where relevant.
"""

# Expanded FAQ and Data
SRM_DATA = {
    "departments": {
        "computer science engineering": "The CSE department at SRM is one of the largest, featuring state-of-the-art labs like the NVIDIA AI Lab and the Next-Gen Computing Lab. It offers specializations in AI, Cloud Computing, Cybersecurity, and Big Data. Placements for CSE are top-tier with recruiters like Google, Amazon, and Microsoft.",
        "mechanical engineering": "The Mechanical department is known for its Formula Student teams (like Camber Racing) and its focus on Industry 4.0. Labs include Robotics & Mechatronics, CAD/CAM, and Advanced Thermal Engineering. Students work on cutting-edge design and manufacturing projects.",
        "electronics and communication": "ECE at SRM focuses on VLSI design, Signal Processing, and Wireless Communication. It houses advanced labs supported by TI and Intel. Students participate in projects like satellite development (SRMSAT).",
        "biotechnology": "The Biotechnology department is a research powerhouse, focusing on areas like Genomics, Proteomics, and Bioprocess Technology. It has collaborations with leading global research institutes and features advanced wet labs.",
        "management": "The SRM School of Management (SOM) offers BBA and MBA programs with specializations in Finance, Marketing, HR, and Business Analytics. It emphasizes industry interaction, case-study based learning, and entrepreneurial development.",
        "law": "SRM School of Law provides integrated programs like BA LLB and BBA LLB. It features a dedicated Moot Court hall, an extensive legal library, and organizes national-level legal seminars and competitions.",
        "medicine": "The SRM Medical College Hospital and Research Centre (SRM MCHRC) is a premier institute offering MBBS, MD, and MS programs. It is attached to the 1200-bed SRM Global Hospital, providing extensive clinical exposure."
    },
    "rules": {
        "attendance": "Strictly 75% attendance is required in each course to be eligible for end-semester examinations. Students with 65-75% may be allowed only with valid medical reasons and approval.",
        "dress code": "Students are expected to maintain a professional dress code. Formals or semi-formals are preferred. ID cards must be worn at all times while on campus.",
        "ragging": "SRM has a Zero Tolerance policy towards ragging. Any student found guilty will be immediately expelled as per UGC guidelines and legal action will be initiated.",
        "hostel rules": "Hostelers must be back in their rooms by 9:00 PM. Electrical appliances like heaters are not allowed. Visitors are only permitted in common areas with prior permission.",
        "academic integrity": "Plagiarism or cheating during exams leads to immediate disqualification (UFM - Unfair Means) and possible suspension from the university."
    },
    "facilities": {
        "library": "The Sir C.V. Raman Learning Centre is a 15-story architectural marvel with 1.5 lakh books and 900+ national/international journals. It includes a dedicated Research Cell, a Digital Library with 100+ workstations, and is fully air-conditioned. It's open from 8:00 AM to 10:00 PM on weekdays.",
        "labs": "SRM boasts world-class labs like the NVIDIA AI Lab, SAP Next-Gen Lab, and the CISCO Networking Lab. Engineering students have access to the Fab Lab for 3D printing and prototyping, and the supercomputing facility for high-end research projects.",
        "canteens": "The campus features the massive 'Food Court' near the Tech Park, Java Canteen for quick bits, and several multi-cuisine outlets serving anything from Italian pasta to North Indian thalis. All messes are ISO certified for hygiene.",
        "sports": "The SRM Indoor Stadium is of Olympic standards. Facilities include synthetic tennis courts, a turf cricket ground, a 400m athletic track, and high-quality basketball and volleyball courts. Coaching is available for university teams.",
        "hospital": "SRM Global Hospital is a multi-specialty 1200-bed facility with 24/7 trauma care, advanced radiology (MRI/CT), and specialized departments for Cardiology, Orthopedics, and more. Students get subsidized treatment."
    },
    "timetable": {
        "cse_sem_4": "CSE Semester 4: Core subjects include Operating Systems, Design and Analysis of Algorithms, and DBMS. Typical schedule: Classes 8:00 AM - 12:45 PM; Labs 1:30 PM - 4:10 PM.",
        "mech_sem_2": "Mechanical Semester 2: Focus on Thermodynamics and Engineering Mechanics. Workshop sessions occupy most Tuesday and Wednesday afternoons.",
        "ece_sem_6": "ECE Semester 6: Intensive focus on VLSI and Communication Systems. Lab sessions for Embedded Systems are held on Friday mornings.",
        "generic": "General University hours are 8:00 AM to 5:00 PM. For your exact section's timetable, please log in to the Academia portal and check the 'Time Table' tab under 'Student Services'."
    }
}

# Expansion: Load from database
def get_predefined_answer(query):
    query = query.lower()
    conn = get_db_connection()
    
    # Tables to search
    tables = {
        'departments': ('name', 'description'),
        'rules': ('title', 'description'),
        'hostel': ('name', 'description'),
        'facilities': ('name', 'description'),
        'timetable': ('course_name', 'schedule')
    }
    
    # 1. Check specific tables first
    for table, (key_col, val_col) in tables.items():
        rows = conn.execute(f'SELECT {key_col}, {val_col} FROM {table}').fetchall()
        for row in rows:
            if row[key_col].lower() in query:
                conn.close()
                return row[val_col]
                
    # 2. Check legacy college_content table
    content = conn.execute('SELECT category, key, value FROM college_content').fetchall()
    for row in content:
        if row['key'].lower() in query:
            conn.close()
            return row['value']
            
    # 3. Fallback for Timetable specific logic if not matched yet
    if "timetable" in query:
        patterns = {"cse": "cse_sem_4", "mech": "mech_sem_2", "ece": "ece_sem_6"}
        for dept, key in patterns.items():
            if dept in query:
                res = conn.execute('SELECT value FROM college_content WHERE category = "timetable" AND key = ?', (key,)).fetchone()
                if res: 
                    conn.close()
                    return res['value']
        
        generic = conn.execute('SELECT value FROM college_content WHERE category = "timetable" AND key = "generic"').fetchone()
        conn.close()
        return generic['value'] if generic else "University hours are 8:00 AM to 5:00 PM. Check the Academia portal for your specific timetable."

    conn.close()
    return None

def sync_initial_data():
    """Load college_data.json into specific DB tables or college_content"""
    if not os.path.exists('college_data.json'):
        return
        
    try:
        with open('college_data.json', 'r') as f:
            data = json.load(f)
        
        conn = get_db_connection()
        table_map = {
            'departments': 'name',
            'rules': 'title',
            'timetable': 'course_name',
            'hostel': 'name',
            'facilities': 'name'
        }
        
        for category, items in data.items():
            if category in table_map:
                key_col = table_map[category]
                for key, value in items.items():
                    try:
                        conn.execute(f'''
                            INSERT OR REPLACE INTO {category} ({key_col}, {"description" if category != "timetable" else "schedule"})
                            VALUES (?, ?)
                        ''', (key, value))
                    except Exception as e:
                        print(f"Error syncing {category} item {key}: {e}")
            else:
                for key, value in items.items():
                    conn.execute('''
                        INSERT OR IGNORE INTO college_content (category, key, value)
                        VALUES (?, ?, ?)
                    ''', (category, key, value))
        
        conn.commit()
        conn.close()
        print("Database sync from college_data.json completed successfully.")
    except Exception as e:
        print(f"CRITICAL SYNC ERROR: {e}")

sync_initial_data()

def get_gemini_response(prompt, history=[]):
    if not client:
        return "The AI assistant is not fully configured yet."
        
    try:
        # System prompt
        system_instruction = f"You are the SRM Student Support AI Assistant. Your goal is to help students with information about SRM University. Be friendly, helpful, and professional. Use campus-related terms where appropriate.\n\n{COLLEGE_CONTEXT}"
        from google.genai import types
        
        contents = []
        for msg in history:
            role = "user" if msg['role'] == 'user' else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg['content'])]))
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

        response = client.models.generate_content(
            model=SELECTED_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=contents
        )
        # Clean response: ensure proper formatting and clickable links
        text = response.text
        # Ensure URLs are absolute and formatted correctly in next steps (frontend)
        # We don't want to strip too much here
        return text.strip()
    except Exception as e:
        print(f"API ERROR: {e}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now."

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username or Email already exists", 400
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            return "Invalid email or password", 401
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    user_message = request.json.get('message')
    conversation_id = request.json.get('conversation_id')
    
    if not user_message:
        return jsonify({"response": "I didn't hear anything."})

    conn = get_db_connection()
    
    # If no conversation_id, create a new one
    if not conversation_id:
        title = user_message[:30] + "..." if len(user_message) > 30 else user_message
        cur = conn.execute('INSERT INTO conversations (user_id, title) VALUES (?, ?)',
                         (session['user_id'], title))
        conversation_id = cur.lastrowid
        conn.commit()

    # Save user message
    conn.execute('INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)',
                 (conversation_id, 'user', user_message))
    conn.commit()

    # Get history for context
    history_rows = conn.execute('SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC',
                               (conversation_id,)).fetchall()
    history = [dict(row) for row in history_rows]

    # Hybrid Architecture:
    # 1. Check for predefined answers (FAQ database) first
    predefined = get_predefined_answer(user_message)
    if predefined:
        ai_response = predefined
    else:
        # 2. If not found in FAQ, send to Gemini API
        ai_response = get_gemini_response(user_message, history[:-1]) # exclude late msg

    try:
        # Save bot response
        conn.execute('INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)',
                     (conversation_id, 'bot', ai_response))
        conn.commit()
    except sqlite3.Error as e:
        print(f"DATABASE ERROR (Saving bot response): {e}")
    finally:
        conn.close()

    return jsonify({"response": ai_response, "conversation_id": conversation_id})

@app.route('/conversations')
def get_conversations():
    if 'user_id' not in session:
        return jsonify([]), 401
    conn = get_db_connection()
    convs = conn.execute('SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC',
                        (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in convs])

@app.route('/conversation/<int:conv_id>')
def get_messages(conv_id):
    if 'user_id' not in session:
        return jsonify([]), 401
    conn = get_db_connection()
    # Security check: ensure conversation belongs to user
    conv = conn.execute('SELECT * FROM conversations WHERE id = ? AND user_id = ?',
                       (conv_id, session['user_id'])).fetchone()
    if not conv:
        conn.close()
        return jsonify([]), 403
        
    messages = conn.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC',
                           (conv_id,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages])

# --- Admin Routes ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_user'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
        
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_user', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login', error="Please login as admin"))
    
    category = request.args.get('cat', 'departments')
    valid_tables = ['departments', 'rules', 'timetable', 'hostel', 'facilities']
    
    conn = get_db_connection()
    if category in valid_tables:
        items = conn.execute(f'SELECT * FROM {category} ORDER BY last_updated DESC').fetchall()
    else:
        items = conn.execute('SELECT * FROM college_content WHERE category = ? ORDER BY last_updated DESC', 
                            (category,)).fetchall()
    conn.close()
    
    # Standardize column names for the template
    standardized_items = []
    for item in items:
        row = dict(item)
        if 'name' in row: row['key'] = row['name']
        if 'title' in row: row['key'] = row['title']
        if 'course_name' in row: row['key'] = row['course_name']
        
        if 'description' in row: row['value'] = row['description']
        if 'schedule' in row: row['value'] = row['schedule']
        
        standardized_items.append(row)
        
    return render_template('admin_dashboard.html', category=category, items=standardized_items)

@app.route('/admin/update_content', methods=['POST'])
def update_content():
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    content_id = request.form.get('id')
    category = request.form.get('category')
    key = request.form.get('key')
    value = request.form.get('value')
    
    conn = get_db_connection()
    
    # Check if category corresponds to a specific table
    table_map = {
        'departments': ('name', 'description'),
        'rules': ('title', 'description'),
        'timetable': ('course_name', 'schedule'),
        'hostel': ('name', 'description'),
        'facilities': ('name', 'description')
    }
    
    if category in table_map:
        key_col, val_col = table_map[category]
        if content_id:
            conn.execute(f'UPDATE {category} SET {key_col} = ?, {val_col} = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                        (key, value, content_id))
        else:
            conn.execute(f'INSERT INTO {category} ({key_col}, {val_col}) VALUES (?, ?)',
                        (key, value))
    else:
        # Legacy college_content
        if content_id:
            conn.execute('UPDATE college_content SET key = ?, value = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                        (key, value, content_id))
        else:
            conn.execute('INSERT INTO college_content (category, key, value) VALUES (?, ?, ?)',
                        (category, key, value))
            
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard', cat=category))

@app.route('/admin/delete_content/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    category = request.form.get('category', 'departments')
    valid_tables = ['departments', 'rules', 'timetable', 'hostel', 'facilities']
    
    conn = get_db_connection()
    if category in valid_tables:
        conn.execute(f'DELETE FROM {category} WHERE id = ?', (content_id,))
    else:
        conn.execute('DELETE FROM college_content WHERE id = ?', (content_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard', cat=category))

@app.route('/admin/run_scraper', methods=['POST'])
def run_scraper_route():
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    try:
        print("Starting manual scraper run from Admin Dashboard...")
        from scraper import scrape_srm_data
        scrape_srm_data()
        sync_initial_data()
        print("Manual scraper run and sync completed successfully.")
    except Exception as e:
        print(f"SCRAPER ROUTE ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('admin_dashboard', cat='departments'))

if __name__ == '__main__':
    app.run(debug=True)
