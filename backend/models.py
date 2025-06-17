from db import db

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    start = db.Column(db.String(100))
    end = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.name,
            'email': self.email,
            'start': self.start,
            'end': self.end
        }
