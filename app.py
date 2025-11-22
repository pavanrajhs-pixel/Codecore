from flask import Flask, render_template, redirect, url_for, request, flash
import os
from werkzeug.utils import secure_filename

from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, abort

from config import Config
from models import db, User, Pet, AdoptionRequest, MatingRequest, VetAppointment

app = Flask(__name__)
app.config.from_object(Config)

# File upload config
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "images", "pets")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_admin_and_vet():
    # Create default admin user
    if not User.query.filter_by(email="admin@janvar.com").first():
        admin_hash = bcrypt.generate_password_hash("admin123").decode("utf-8")
        admin = User(
            name="Super Admin",
            email="admin@janvar.com",
            password_hash=admin_hash,
            role="admin",
        )
        db.session.add(admin)

    # Create default vet user
    if not User.query.filter_by(email="vet@example.com").first():
        vet_hash = bcrypt.generate_password_hash("vet123").decode("utf-8")
        vet = User(
            name="Dr. Meow Bark",
            email="vet@example.com",
            password_hash=vet_hash,
            role="vet",
        )
        db.session.add(vet)

    db.session.commit()



@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form.get("role", "owner")

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(name=name, email=email, password_hash=pw_hash, role=role)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("auth_register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("auth_login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    pets = Pet.query.filter_by(owner_id=current_user.id).all()
    upcoming_appointments = VetAppointment.query.filter_by(owner_id=current_user.id).all()
    return render_template("dashboard.html", pets=pets, appointments=upcoming_appointments)


@app.route("/pets")
@login_required
def pets():
    all_pets = Pet.query.all()
    return render_template("pets.html", all_pets=all_pets)


@app.route("/pets/add", methods=["POST"])
@login_required
def add_pet():
    name = request.form["name"]
    species = request.form["species"]
    breed = request.form.get("breed")
    age = int(request.form.get("age") or 0)
    gender = request.form.get("gender")
    is_for_adoption = "is_for_adoption" in request.form
    is_for_mating = "is_for_mating" in request.form
    health_notes = request.form.get("health_notes")

    # 🔹 Handle image upload
    image_file = request.files.get("image")
    image_filename = None

    if image_file and image_file.filename and allowed_file(image_file.filename):
        safe_name = secure_filename(image_file.filename)
        image_filename = safe_name
        image_path = os.path.join(UPLOAD_FOLDER, safe_name)
        image_file.save(image_path)

    pet = Pet(
        name=name,
        species=species,
        breed=breed,
        age=age,
        gender=gender,
        is_for_adoption=is_for_adoption,
        is_for_mating=is_for_mating,
        health_notes=health_notes,
        owner_id=current_user.id,
        image=image_filename,  # 👈 store filename in DB
    )

    db.session.add(pet)
    db.session.commit()

    flash("Pet added successfully", "success")
    return redirect(url_for("dashboard"))



@app.route("/adopt/<int:pet_id>", methods=["POST"])
@login_required
def adopt_pet(pet_id):
    message = request.form.get("message", "")
    req = AdoptionRequest(
        pet_id=pet_id,
        requester_id=current_user.id,
        message=message,
    )
    db.session.add(req)
    db.session.commit()
    flash("Adoption request submitted", "success")
    return redirect(url_for("pets"))


@app.route("/mating/request/<int:pet_id>", methods=["POST"])
@login_required
def request_mating(pet_id):
    requester_pet_id = int(request.form["requester_pet_id"])

    req = MatingRequest(
        pet_id=pet_id,
        requester_pet_id=requester_pet_id
    )
    db.session.add(req)
    db.session.commit()
    flash("Mating request submitted", "success")
    return redirect(url_for("pets"))


@app.route("/appointments")
@login_required
def appointments():
    if current_user.role == "vet":
        appts = VetAppointment.query.filter_by(vet_id=current_user.id).all()
        users = []
    else:
        appts = VetAppointment.query.filter_by(owner_id=current_user.id).all()
        users = User.query.all()
    return render_template("vet_appointments.html", appointments=appts, users=users)


@app.route("/appointments/book", methods=["POST"])
@login_required
def book_appointment():
    pet_id = int(request.form["pet_id"])
    vet_id = int(request.form["vet_id"])
    time_str = request.form["appointment_time"]
    reason = request.form.get("reason", "")

    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")

    appt = VetAppointment(
        owner_id=current_user.id,
        pet_id=pet_id,
        vet_id=vet_id,
        appointment_time=dt,
        reason=reason
    )
    db.session.add(appt)
    db.session.commit()
    flash("Appointment booked", "success")
    return redirect(url_for("appointments"))

@app.route("/admin")
@login_required
def admin_dashboard():
    # Only admins allowed
    if current_user.role != "admin":
        flash("Admin access only.", "danger")
        return redirect(url_for("dashboard"))

    users = User.query.all()
    pets = Pet.query.all()
    adoptions = AdoptionRequest.query.all()
    matings = MatingRequest.query.all()
    appointments = VetAppointment.query.all()

    return render_template(
        "admin_dashboard.html",
        users=users,
        pets=pets,
        adoptions=adoptions,
        matings=matings,
        appointments=appointments,
    )


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        create_admin_and_vet()
        print("Database initialized with sample vet user.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin_and_vet()
    app.run(debug=True)
