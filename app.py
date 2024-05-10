from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import LoginManager, UserMixin, login_user,logout_user,login_required, current_user

app = Flask(__name__)
app.secret_key = 'cyber_security'  # Change this to a random secret key
login_manager = LoginManager(app)

# MySQL database connection configuration
db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Chandrika1+",
    database="cstp"
)
cursor = db.cursor(buffered=True)

# Check if the users table exists, if not, create it
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        user_id INT,
        course1 INT DEFAULT 0,
        course2 INT DEFAULT 0,
        course3 INT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_scores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        quiz_id INT,
        score INT
    )
""")

# Database models
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(id=user_data[0], username=user_data[1], password=user_data[2])
    else:
        return None

# Routes
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user_data = cursor.fetchone()
    
    if user_data:
        user = User(id=user_data[0], username=user_data[1], password=user_data[2])
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('training_platform'))
    else:
        flash('Login unsuccessful. Please check your credentials.', 'danger')
        return redirect(url_for('welcome'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Check if the username already exists
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        else:
            # Insert new user into the database
            insert_query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (username, password, email))
            db.commit()

            # Get the user ID of the newly registered user
            user_id = cursor.lastrowid
            
            # Initialize enrollment values to 0 for the new user
            insert_enrollment_query = "INSERT INTO enrollments (user_id, course1, course2, course3) VALUES (%s, 0, 0, 0)"
            cursor.execute(insert_enrollment_query, (user_id,))
            db.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('welcome'))


@app.route('/training_platform')
@login_required
def training_platform():
    # Check if the user is enrolled in each course
    query = "SELECT * FROM enrollments WHERE user_id = %s"
    cursor.execute(query, (current_user.id,))
    enrollment_data = cursor.fetchone()

    # Fetch column names
    column_names = [desc[0] for desc in cursor.description]
    
    # Convert fetched data to dictionary
    enrollment_dict = dict(zip(column_names, enrollment_data))
    
    # Check the scores of each course
    course_scores = {
        'course1': get_course_score(current_user.id, 1),
        'course2': get_course_score(current_user.id, 2),
        'course3': get_course_score(current_user.id, 3)
    }

    return render_template('training_platform.html', enrollment=enrollment_dict, course_scores=course_scores)

def get_course_score(user_id, course_id):
    # Query the database to get the score for the given user and course
    query = "SELECT score FROM quiz_scores WHERE user_id = %s AND quiz_id = %s"
    cursor.execute(query, (user_id, course_id))
    score_data = cursor.fetchone()
    if score_data:
        return score_data[0]
    else:
        return 0


@app.route('/enroll/<course>')
@login_required
def enroll(course):
    # Update the enrollment status in the database
    update_query = f"UPDATE enrollments SET {course} = 1 WHERE user_id = %s"
    cursor.execute(update_query, (current_user.id,))
    db.commit()
    flash('Enrolled successfully!', 'success')
    return redirect(url_for(course))

@app.route('/course1')
def course1():
    return render_template('course1.html')

@app.route('/course2')
def course2():
    return render_template('course2.html')

@app.route('/course3')
def course3():
    return render_template('course3.html')

@app.route('/phishing_scenario')
def phishing_scenario():
    return render_template('phishing_scenario.html')

@app.route('/quiz1')
def quiz1():
    return render_template('quiz1.html')

@app.route('/quiz2')
def quiz2():
    return render_template('quiz2.html')

@app.route('/quiz3')
def quiz3():
    return render_template('quiz3.html')

@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    if request.method == 'POST':
        user_id = current_user.id  # Get the current user's ID
        score = int(request.form['score'])
        quiz_id = int(request.form['quiz_id'])  # Add quiz_id parameter

        # Check if user already has a score for this quiz
        query = "SELECT * FROM quiz_scores WHERE user_id = %s AND quiz_id = %s"
        cursor.execute(query, (user_id, quiz_id))
        existing_score = cursor.fetchone()

        if existing_score:
            if score > existing_score[3]:  # Compare new score with existing score
                # Update the score in the database
                update_query = "UPDATE quiz_scores SET score = %s WHERE user_id = %s AND quiz_id = %s"
                cursor.execute(update_query, (score, user_id, quiz_id))
                db.commit()
                flash('Score updated successfully!', 'success')
            else:
                flash('Your previous score is higher. Score not updated.', 'warning')
        else:
            # Save the score in the database
            save_score_to_database(user_id, quiz_id, score)
            flash('Score saved successfully!', 'success')
        
        # Redirect to the respective score page based on the quiz number
        return redirect(url_for('score1', score=score, quiz_id=quiz_id))


def save_score_to_database(user_id, quiz_id, score):
    try:
        # Save the score in the database
        query = "INSERT INTO quiz_scores (user_id,quiz_id, score) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, quiz_id, score))
        db.commit()
        print("Score saved successfully.")
    except Exception as e:
        print("Error:", e)
        db.rollback()  # Rollback the transaction in case of an error

@app.route('/score1/<int:score>/<int:quiz_id>')
def score1(score, quiz_id):
    return render_template('score1.html', score=score, quiz_id=quiz_id)


@app.route('/certificate1')
@login_required
def certificate1():
    return render_template('certificate1.html', current_user=current_user)


@app.route('/certificate2')
@login_required
def certificate2():
    return render_template('certificate2.html', current_user=current_user)


@app.route('/certificate3')
@login_required
def certificate3():
    return render_template('certificate3.html', current_user=current_user)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=True)
