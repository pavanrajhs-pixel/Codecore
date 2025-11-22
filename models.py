from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------- USER ----------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="owner")  # owner / vet / admin

    city = db.Column(db.String(120))  # optional: for location-based matching

    pets = db.relationship("Pet", backref="owner", lazy=True)


# ---------- PET ----------
class Pet(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(50), nullable=False)  # dog / cat
    image = db.Column(db.String(200))  # filename of uploaded image
    address = db.Column(db.String(255))  # pet exact location / address

    breed = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # male / female
    color = db.Column(db.String(50))
    weight_kg = db.Column(db.Float)

    city = db.Column(db.String(120))  # city of the pet

    is_for_adoption = db.Column(db.Boolean, default=False)
    is_for_mating = db.Column(db.Boolean, default=False)

    vaccinated = db.Column(db.Boolean, default=False)
    dewormed = db.Column(db.Boolean, default=False)
    pedigree_certified = db.Column(db.Boolean, default=False)
    neutered = db.Column(db.Boolean, default=False)

    temperament = db.Column(db.String(120))  # calm / playful / friendly / etc.
    health_notes = db.Column(db.Text)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


# ---------- ADOPTION REQUEST ----------
class AdoptionRequest(db.Model):
    __tablename__ = "adoption_requests"

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pet = db.relationship("Pet", backref="adoption_requests", lazy=True)
    requester = db.relationship("User", foreign_keys=[requester_id])


# ---------- MATING REQUEST ----------
class MatingRequest(db.Model):
    __tablename__ = "mating_requests"

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    requester_pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pet = db.relationship("Pet", foreign_keys=[pet_id])
    requester_pet = db.relationship("Pet", foreign_keys=[requester_pet_id])


# ---------- VET APPOINTMENT ----------
class VetAppointment(db.Model):
    __tablename__ = "vet_appointments"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    vet = db.relationship("User", foreign_keys=[vet_id])
    pet = db.relationship("Pet", foreign_keys=[pet_id])
