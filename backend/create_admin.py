from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Sprawdź, czy admin już istnieje
    if User.query.filter_by(username='admin').first():
        print("Admin już istnieje.")
    else:
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
        print("Konto admina zostało utworzone.")