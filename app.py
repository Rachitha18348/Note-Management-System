
from flask import Flask, render_template, redirect, url_for, request, session

import bcrypt

from database import db

from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from mail import send_email



app = Flask(__name__)

app.secret_key = 'notes@22'
s=URLSafeTimedSerializer(app.secret_key)


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("home.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=['GET', 'POST'])
def register():

    info = request.args.get('info')

    if request.method == 'POST':

        uname = request.form.get('uname')
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = db.cursor()

        # Check whether email already exists
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        if user:
            cursor.close()
            return redirect(
                url_for('register', info="Email already exists")
            )

        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (uname, email, hashed_password)
        )

        # Save changes
        db.commit()

        # Close cursor
        cursor.close()

        # Redirect to login
        return redirect(
            url_for('login', info="Registration successful")
        )

    return render_template("register.html", info=info)


# ---------------- LOGIN ----------------

@app.route("/login", methods=['GET', 'POST'])
def login():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        cursor = db.cursor()

        # Find user by email
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        # Email not found
        if not user:
            cursor.close()
            return redirect(
                url_for('login', info="Email not registered")
            )

        # Check password
        password_check = bcrypt.checkpw(
            password.encode('utf-8'),
            user[3].encode('utf-8')
        )

        # Login successful
        if password_check:

            session['user_id'] = user[0]

            cursor.close()

            return redirect(url_for('dashboard'))

        # Incorrect password
        cursor.close()

        return redirect(
            url_for('login', info="Incorrect password")
        )

    return render_template("login.html", info=info)


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if 'user_id' not in session:
        return redirect(
            url_for('login', info="Please login first")
        )

    cursor = db.cursor()

    # Get logged-in user's name
    cursor.execute(
        "SELECT username FROM users WHERE id=%s",
        (session['user_id'],)
    )

    user = cursor.fetchone()

    # Get user's notes
    cursor.execute(
        "SELECT * FROM notes WHERE user_id=%s",
        (session['user_id'],)
    )

    notes = cursor.fetchall()

    cursor.close()

    return render_template(
        "dashboard.html",
        notes=notes,
        username=user[0]
    )
@app.route('/createnote', methods=['POST'])
def create_note():

    if 'user_id' in session:

        content = request.form.get('note')
        user_id = session['user_id']

        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO notes (user_id, content) VALUES (%s, %s)",
            (user_id, content)
        )

        db.commit()
        cursor.close()

        return redirect(url_for('dashboard'))

    return redirect(url_for('login'))


@app.route('/deletenote/<int:note_id>')
def delete_note(note_id):

    if 'user_id' in session:

        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM notes WHERE id=%s AND user_id=%s",
            (note_id, session['user_id'])
        )

        db.commit()
        cursor.close()

    return redirect(url_for('dashboard'))

@app.route('/editnote/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):


    if 'user_id' in session:

        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':

            new_content = request.form.get('content')

            cursor.execute(
                "UPDATE notes SET content=%s WHERE id=%s AND user_id=%s",
                (new_content, note_id, session['user_id'])
            )

            db.commit()
            cursor.close()

            return redirect(url_for('dashboard'))

        cursor.execute(
            "SELECT * FROM notes WHERE id=%s AND user_id=%s",
            (note_id, session['user_id'])
        )

        note = cursor.fetchone()

        cursor.close()

        if note:
            return render_template(
                'editnote.html',
                note=note
            )

    return redirect(url_for('login'))

@app.route('/readnote/<int:note_id>')
def read_note(note_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notes WHERE id=%s AND user_id=%s",
        (note_id, session['user_id'])
    )

    note = cursor.fetchone()

    cursor.close()

    if note:
        return render_template(
            'readnote.html',
            note=note
        )

    return redirect(url_for('dashboard'))
# ---------------- RESET PASSWORD ----------------

@app.route("/resetpassword/<token>", methods=['GET', 'POST'])
def resetpassword(token):

    try:
        email = s.loads(
            token,
            salt='password-reset-salt',
            max_age=3600
        )

    except SignatureExpired:
        return redirect(
            url_for(
                'forgotpassword',
                info="Token expired. Request a new link."
            )
        )

    info = request.args.get('info')

    if request.method == 'POST':

        newpassword = request.form.get('newspassword')
        confirmpassword = request.form.get('confirmpassword')

        if newpassword == confirmpassword:

            hashed_password = bcrypt.hashpw(
                newpassword.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            cursor = db.cursor()

            cursor.execute(
                "UPDATE users SET password=%s WHERE email=%s",
                (hashed_password, email)
            )

            db.commit()
            cursor.close()

            return redirect(
                url_for(
                    'login',
                    info='Password reset successful'
                )
            )

        return redirect(
            url_for(
                'resetpassword',
                token=token,
                info="Passwords do not match"
            )
        )

    return render_template(
        "resetpassword.html",
        info=info
    )


# ---------------- FORGOT PASSWORD ----------------

@app.route("/forgotpassword", methods=['GET', 'POST'])
def forgotpassword():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')

        cursor = db.cursor()

        cursor.execute(
            "SELECT email FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            token = s.dumps(
                email,
                salt='password-reset-salt'
            )

            reset_url = url_for(
                'resetpassword',
                token=token,
                _external=True
            )

            send_email(
                email,
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}\n\n'
                'This link will expire in 1 hour'
            )

            cursor.close()

            return redirect(
                url_for(
                    'forgotpassword',
                    info='Link sent to your email, please check'
                )
            )

        cursor.close()

        return redirect(
            url_for(
                'forgotpassword',
                info='Email is not registered'
            )
        )

    return render_template(
        "forgotpassword.html",
        info=info
    )


# ---------------- VERIFY ----------------

@app.route("/verify")
def verify():
    return render_template("verify.html")




# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    # Remove all session data
    session.clear()

    # Go to login page
    return redirect(url_for('login', info="Logged out successfully"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)

