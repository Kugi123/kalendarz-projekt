from flask import send_from_directory
import pathlib
import os
import re
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_mail import Mail, Message

# Konfiguracja
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajnyklucz'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_DOMAIN'] = 'kalendarz-projekt.onrender.com'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail (Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'k05030072@gmail.com'
app.config['MAIL_PASSWORD'] = 'rmaf ivoy xqnx aroz'
app.config['MAIL_DEFAULT_SENDER'] = 'k05030072@gmail.com'

mail = Mail(app)

os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)
CORS(app, supports_credentials=True, origins=["https://kalendarz-projekt.onrender.com"])


login_manager = LoginManager()
login_manager.init_app(app)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Origin', 'https://kalendarz-projekt.onrender.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,DELETE,PUT')  # ← TO DODAJ
    return response


# MODELE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# REJESTRACJA
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if len(data['username']) < 3:
        return jsonify({'error': 'Login musi mieć co najmniej 3 znaki'}), 400
    if len(data['password']) < 6:
        return jsonify({'error': 'Hasło musi mieć co najmniej 6 znaków'}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
        return jsonify({'error': 'Nieprawidłowy adres e-mail'}), 400
    if not re.fullmatch(r"\d{9}", data['phone']):
        return jsonify({'error': 'Numer telefonu musi składać się z 9 cyfr'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Użytkownik już istnieje'}), 400

    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Zarejestrowano pomyślnie'})

# LOGOWANIE
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({'message': 'Zalogowano'})
    return jsonify({'error': 'Błędne dane logowania'}), 401

# WYLOGOWANIE
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'message': 'Wylogowano'})

# SPRAWDZANIE SESJI
@app.route('/check', methods=['GET'])
def check():
    return jsonify({
        'loggedIn': current_user.is_authenticated,
        'isAdmin': current_user.is_authenticated and current_user.is_admin
    })

# POBIERANIE WIZYT
@app.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    appointments = Appointment.query.all()
    result = []
    for appt in appointments:
        result.append({
            'id': appt.id,
            'start': appt.start.isoformat(),
            'end': appt.end.isoformat(),
            'mine': appt.user_id == current_user.id
        })
    return jsonify(result)

# DODAWANIE WIZYTY
@app.route('/appointments', methods=['POST'])
@login_required
def create_appointment():
    data = request.get_json()
    start = datetime.fromisoformat(data['start'])
    end = start + timedelta(minutes=30)

    existing = Appointment.query.filter_by(start=start).first()
    if existing:
        return jsonify({'error': 'Termin zajęty'}), 400

    appt = Appointment(user_id=current_user.id, start=start, end=end)
    db.session.add(appt)
    db.session.commit()

    try:
        msg = Message(
            subject="Potwierdzenie wizyty",
            recipients=[current_user.email],
            body=f"Cześć {current_user.first_name},\n\nZarezerwowano wizytę na: {start.strftime('%Y-%m-%d %H:%M')}.\n\nPozdrawiamy!"
        )
        mail.send(msg)
    except Exception as e:
        print("Błąd podczas wysyłki maila:", e)

    return jsonify({'message': 'Zarezerwowano'})

# USUWANIE WIZYTY (admin)
@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
def delete_appointment(appointment_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403

    appt = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appt)
    db.session.commit()
    return jsonify({'message': 'Wizyta usunięta'})

# EDYCJA WIZYTY (admin)
@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403

    data = request.get_json()
    new_start = datetime.fromisoformat(data['start'])
    new_end = new_start + timedelta(minutes=30)

    appointment = Appointment.query.get_or_404(appointment_id)

    conflict = Appointment.query.filter(
        Appointment.id != appointment.id,
        Appointment.start == new_start
    ).first()
    if conflict:
        return jsonify({'error': 'Termin już zajęty'}), 400

    appointment.start = new_start
    appointment.end = new_end
    db.session.commit()

    return jsonify({'message': 'Wizyta zaktualizowana'})

# START
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='Lekarz',
            email='admin@clinic.com',
            phone='123456789',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Konto admina utworzone.")
    else:
        print("Konto admina już istnieje.")

@app.route('/')
def index():
    return 'Backend działa'

application = app