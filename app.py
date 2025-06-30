from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yourpassword',
    'database': 'governance_db'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        flash(f"Database connection error: {e}", 'error')
        return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.context_processor
def inject_current_date():
    return {'current_date': datetime.now().date()}

# Home/Dashboard
@app.route('/')
@app.route('/dashboard')
def dashboard():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        # Get upcoming meetings
        cursor.execute("""
            SELECT * FROM BoardMeeting 
            WHERE Date >= CURDATE() 
            ORDER BY Date ASC 
            LIMIT 5
        """)
        upcoming_meetings = cursor.fetchall()
        
        # Convert Time to proper format
        for meeting in upcoming_meetings:
            if isinstance(meeting['Time'], timedelta):
                # Convert timedelta to time object
                meeting['Time'] = (datetime.min + meeting['Time']).time()
        
        cursor.close()
        connection.close()
        
        return render_template('dashboard.html',
                           upcoming_meetings=upcoming_meetings,
                           today=datetime.now().date())

# STAKEHOLDERS ROUTES
@app.route('/stakeholders')
def stakeholders():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Stakeholder")
        stakeholders = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('stakeholders.html', stakeholders=stakeholders)
    return redirect(url_for('dashboard'))

@app.route('/add_stakeholder', methods=['POST'])
def add_stakeholder():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        contact = request.form['contact']
        shares = request.form['shares']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Stakeholder (Name, Role, ContactInfo, SharesOwned) VALUES (%s, %s, %s, %s)",
                    (name, role, contact, shares)
                )
                connection.commit()
                flash('Stakeholder added successfully!', 'success')
            except Error as e:
                flash(f"Error adding stakeholder: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('stakeholders'))

@app.route('/stakeholder/<int:stakeholder_id>/edit', methods=['GET', 'POST'])
def edit_stakeholder(stakeholder_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Handle form submission
            name = request.form['name']
            role = request.form['role']
            contact = request.form['contact']
            shares = request.form['shares']
            
            try:
                cursor.execute(
                    """UPDATE Stakeholder 
                    SET Name=%s, Role=%s, ContactInfo=%s, SharesOwned=%s 
                    WHERE StakeholderID=%s""",
                    (name, role, contact, shares, stakeholder_id)
                )
                connection.commit()
                flash('Stakeholder updated successfully!', 'success')
                return redirect(url_for('stakeholders'))
            except Error as e:
                flash(f"Error updating stakeholder: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
        
        # GET request - show edit form
        cursor.execute("SELECT * FROM Stakeholder WHERE StakeholderID = %s", (stakeholder_id,))
        stakeholder = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if stakeholder:
            return render_template('edit_stakeholder.html', stakeholder=stakeholder)
    
    flash('Stakeholder not found', 'error')
    return redirect(url_for('stakeholders'))

@app.route('/stakeholder/<int:stakeholder_id>/delete', methods=['POST'])
def delete_stakeholder(stakeholder_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM Stakeholder WHERE StakeholderID = %s", (stakeholder_id,))
            connection.commit()
            flash('Stakeholder deleted successfully!', 'success')
        except Error as e:
            flash(f'Error deleting stakeholder: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('stakeholders'))

@app.route('/update_stakeholder/<int:stakeholder_id>', methods=['POST'])
def update_stakeholder(stakeholder_id):
    connection = get_db_connection()
    try:
        
        cursor = connection.cursor()
        cursor.execute("SET innodb_lock_wait_timeout = 10;")
        connection.start_transaction()
    
        cursor.execute("""
            SELECT * FROM Stakeholder 
            WHERE StakeholderID = %s 
            FOR UPDATE;
        """, (stakeholder_id,))
       
        cursor.execute("""
            UPDATE Stakeholder
            SET SharesOwned = %s
            WHERE StakeholderID = %s;
        """, (request.form['shares'], stakeholder_id))
        
        cursor.execute("""
            INSERT INTO TransactionLog
            (TransactionID, OperationType, TableName, RecordID, OldValue, NewValue)
            VALUES (UUID(), 'UPDATE', 'Stakeholder', %s, %s, %s);
        """, (stakeholder_id, request.form['old_shares'], request.form['shares']))
        connection.commit()
        flash('Update successful', 'success')
    except Error as e:
        connection.rollback()
        flash(f'Update failed: {e}', 'error')
    finally:
        if connection:
            connection.close()
            
# MEETINGS ROUTES
@app.route('/meetings')
def meetings():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BoardMeeting ORDER BY Date DESC")
        meetings = cursor.fetchall()
        
        # Convert Time to proper format
        for meeting in meetings:
            if isinstance(meeting['Time'], timedelta):
                meeting['Time'] = (datetime.min + meeting['Time']).time()
            elif isinstance(meeting['Time'], str):
                try:
                    meeting['Time'] = datetime.strptime(meeting['Time'], '%H:%M:%S').time()
                except ValueError:
                    meeting['Time'] = None
        
        cursor.close()
        connection.close()
        return render_template('meetings.html', meetings=meetings)
    return redirect(url_for('dashboard'))

@app.route('/add_meeting', methods=['POST'])
def add_meeting():
    date = request.form['date']
    time = request.form.get('time')  # Optional field
    agenda = request.form['agenda']
    location = request.form['location']
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Pass NULL if time is empty
            cursor.execute(
                "INSERT INTO BoardMeeting (Date, Time, Agenda, Location) VALUES (%s, %s, %s, %s)",
                (date, time if time else None, agenda, location)
            )
            connection.commit()
            flash('Meeting scheduled successfully!', 'success')
        except Error as e:
            flash(f"Error scheduling meeting: {e}", 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('meetings'))
@app.route('/meeting/<int:id>')
def view_meeting(id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BoardMeeting WHERE MeetingID = %s", (id,))
        meeting = cursor.fetchone()
        
        if meeting:
            # Convert Time if needed (same conversion as in meetings route)
            if isinstance(meeting['Time'], timedelta):
                meeting['Time'] = (datetime.min + meeting['Time']).time()
            elif isinstance(meeting['Time'], str):
                try:
                    meeting['Time'] = datetime.strptime(meeting['Time'], '%H:%M:%S').time()
                except ValueError:
                    meeting['Time'] = None
            
            cursor.close()
            connection.close()
            return render_template('view_meeting.html', meeting=meeting)
        
        cursor.close()
        connection.close()
        flash('Meeting not found', 'error')
    return redirect(url_for('meetings'))

# COMPLIANCE DOCUMENTS ROUTES
@app.route('/compliance')
def compliance():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT *,
                   days_until_expiry(ExpiryDate) AS days_remaining
            FROM ComplianceDocument
        """)
        documents = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('compliance.html', 
                           documents=documents,
                           today=datetime.now().date())  # Add this line
    return redirect(url_for('dashboard'))

@app.route('/add_document', methods=['POST'])
def add_document():
    if request.method == 'POST':
        name = request.form['name']
        doc_type = request.form['type']
        expiry_date = request.form['expiry_date'] if request.form['expiry_date'] else None
        
        # File upload handling
        if 'document_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('compliance'))
            
        file = request.files['document_file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('compliance'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        """INSERT INTO ComplianceDocument 
                        (Name, Type, ExpiryDate, Status, FilePath) 
                        VALUES (%s, %s, %s, 'Active', %s)""",
                        (name, doc_type, expiry_date, filepath)
                    )
                    connection.commit()
                    flash('Document added successfully!', 'success')
                except Error as e:
                    flash(f"Error adding document: {e}", 'error')
                finally:
                    cursor.close()
                    connection.close()
        else:
            flash('Allowed file types are pdf, doc, docx', 'error')
    return redirect(url_for('compliance'))

@app.route('/document/<int:id>')  # Now using 'id'
def view_document(id):  # Parameter name matches
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ComplianceDocument WHERE DocumentID = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if document:
            return render_template('view_document.html', document=document)
    
    flash('Document not found', 'error')
    return redirect(url_for('compliance'))

@app.route('/download/<int:id>')
def download_document(id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT FilePath FROM ComplianceDocument WHERE DocumentID = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if document and document['FilePath'] and os.path.exists(document['FilePath']):
            return send_from_directory(
                directory=os.path.dirname(document['FilePath']),
                path=os.path.basename(document['FilePath']),
                as_attachment=True
            )
    flash('Document not found or file missing', 'error')
    return redirect(url_for('compliance'))

# DECISIONS ROUTES
@app.route('/decisions')
def decisions():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, bm.Date as meeting_date 
            FROM Decision d
            LEFT JOIN BoardMeeting bm ON d.MeetingID = bm.MeetingID
            ORDER BY bm.Date DESC
        """)
        decisions = cursor.fetchall()
        cursor.close()
        
        # Get meetings for the dropdown
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT MeetingID, Date, Agenda FROM BoardMeeting ORDER BY Date DESC")
        meetings = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('decisions.html', decisions=decisions, meetings=meetings)
    return redirect(url_for('dashboard'))

@app.route('/add_decision', methods=['POST'])
def add_decision():
    if request.method == 'POST':
        meeting_id = request.form['meeting_id']
        description = request.form['description']
        rationale = request.form['rationale']
        status = request.form['status']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """INSERT INTO Decision 
                    (MeetingID, Description, Rationale, Status) 
                    VALUES (%s, %s, %s, %s)""",
                    (meeting_id, description, rationale, status)
                )
                connection.commit()
                flash('Decision recorded successfully!', 'success')
            except Error as e:
                flash(f"Error recording decision: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('decisions'))

@app.route('/decision/<int:id>')
def view_decision(id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, bm.Date as meeting_date, bm.Agenda as meeting_agenda
            FROM Decision d
            JOIN BoardMeeting bm ON d.MeetingID = bm.MeetingID
            WHERE d.DecisionID = %s
        """, (id,))
        decision = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if decision:
            return render_template('view_decision.html', decision=decision)
    
    flash('Decision not found', 'error')
    return redirect(url_for('decisions'))

@app.route('/decision/update/<int:id>', methods=['GET', 'POST'])
def update_decision_status(id):
    if request.method == 'POST':
        new_status = request.form['status']
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "UPDATE Decision SET Status = %s WHERE DecisionID = %s",
                    (new_status, id)
                )
                connection.commit()
                flash('Decision status updated!', 'success')
            except Error as e:
                flash(f"Error updating decision: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
        return redirect(url_for('decisions'))
    
    # GET request - show update form
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Decision WHERE DecisionID = %s", (id,))
        decision = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if decision:
            return render_template('update_decision.html', decision=decision)
    
    flash('Decision not found', 'error')
    return redirect(url_for('decisions'))

# ===== AUDIT ROUTES =====
@app.route('/audits')
def audits():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Audit ORDER BY Date DESC")
        audits = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('audits.html', audits=audits)
    return redirect(url_for('dashboard'))

@app.route('/add_audit', methods=['POST'])
def add_audit():
    if request.method == 'POST':
        date = request.form['date']
        findings = request.form['findings']
        recommendations = request.form['recommendations']
        status = request.form['status']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Audit (Date, Findings, Recommendations, Status) VALUES (%s, %s, %s, %s)",
                    (date, findings, recommendations, status)
                )
                connection.commit()
                flash('Audit record added successfully!', 'success')
            except Error as e:
                flash(f"Error adding audit: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('audits'))

# ===== POLICY ROUTES =====
@app.route('/policies')
def policies():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Policy ORDER BY ApprovalDate DESC")
        policies = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('policies.html', policies=policies)
    return redirect(url_for('dashboard'))

@app.route('/add_policy', methods=['POST'])
def add_policy():
    if request.method == 'POST':
        name = request.form['name']
        version = request.form['version']
        approval_date = request.form['approval_date']
        category = request.form['category']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Policy (Name, Version, ApprovalDate, Category) VALUES (%s, %s, %s, %s)",
                    (name, version, approval_date, category)
                )
                connection.commit()
                flash('Policy added successfully!', 'success')
            except Error as e:
                flash(f"Error adding policy: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('policies'))

# ===== PERFORMANCE EVALUATION ROUTES =====
@app.route('/evaluations')
def evaluations():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT pe.*, s.Name as StakeholderName 
            FROM PerformanceEvaluation pe
            JOIN Stakeholder s ON pe.StakeholderID = s.StakeholderID
            ORDER BY pe.EvaluationID DESC
        """)
        evaluations = cursor.fetchall()
        cursor.close()
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT StakeholderID, Name FROM Stakeholder")
        stakeholders = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('evaluations.html', 
                            evaluations=evaluations,
                            stakeholders=stakeholders)
    return redirect(url_for('dashboard'))
@app.route('/add_evaluation', methods=['POST'])
def add_evaluation():
    if request.method == 'POST':
        stakeholder_id = request.form['stakeholder_id']
        metrics = request.form['metrics']
        feedback = request.form['feedback']
        score = request.form['score']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """INSERT INTO PerformanceEvaluation 
                    (StakeholderID, Metrics, Feedback, Score) 
                    VALUES (%s, %s, %s, %s)""",
                    (stakeholder_id, metrics, feedback, score)
                )
                connection.commit()
                flash('Evaluation added successfully!', 'success')
            except Error as e:
                flash(f"Error adding evaluation: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('evaluations'))

# ===== CONFLICT OF INTEREST ROUTES =====
@app.route('/conflicts')
def conflicts():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT co.*, s.Name as StakeholderName 
            FROM ConflictOfInterest co
            JOIN Stakeholder s ON co.StakeholderID = s.StakeholderID
            ORDER BY co.ConflictID DESC
        """)
        conflicts = cursor.fetchall()
        cursor.close()
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT StakeholderID, Name FROM Stakeholder")
        stakeholders = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('conflicts.html', 
                            conflicts=conflicts,
                            stakeholders=stakeholders)
    return redirect(url_for('dashboard'))

@app.route('/add_conflict', methods=['POST'])
def add_conflict():
    if request.method == 'POST':
        stakeholder_id = request.form['stakeholder_id']
        description = request.form['description']
        status = request.form['status']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """INSERT INTO ConflictOfInterest 
                    (StakeholderID, Description, Status) 
                    VALUES (%s, %s, %s)""",
                    (stakeholder_id, description, status)
                )
                connection.commit()
                flash('Conflict record added successfully!', 'success')
            except Error as e:
                flash(f"Error adding conflict: {e}", 'error')
            finally:
                cursor.close()
                connection.close()
    return redirect(url_for('conflicts'))
def create_triggers():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                DELIMITER //
                CREATE TRIGGER validate_stakeholder_name
                BEFORE INSERT ON Stakeholder
                FOR EACH ROW
                BEGIN
                    IF NEW.Name REGEXP '[0-9!@#$%^&*(),.?":{}|<>]' THEN
                        SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Stakeholder name cannot contain numbers or special characters';
                    END IF;
                END//
                DELIMITER ;
            """)
            
            cursor.execute("""
                DELIMITER //
                CREATE TRIGGER set_default_meeting_time
                BEFORE INSERT ON BoardMeeting
                FOR EACH ROW
                BEGIN
                    IF NEW.Time IS NULL THEN
                        SET NEW.Time = '09:00:00';
                    END IF;
                END//
                DELIMITER ;
            """)
            
            connection.commit()
            print("Triggers created successfully")
        except Error as e:
            print(f"Error creating triggers: {e}")
        finally:
            cursor.close()
            connection.close()
def create_database_functions():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                DELIMITER //
                CREATE FUNCTION IF NOT EXISTS days_until_expiry(expiry_date DATE) 
                RETURNS INT
                DETERMINISTIC
                BEGIN
                    DECLARE days_left INT;
                    SET days_left = DATEDIFF(expiry_date, CURDATE());
                    RETURN IF(days_left >= 0, days_left, -1);
                END//
                DELIMITER ;
            """)
            connection.commit()
            print("Function created successfully")
        except Error as e:
            print(f"Error creating function: {e}")
        finally:
            cursor.close()
            connection.close()

# Call this function during application startup
create_database_functions()

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
