from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bcrypt import Bcrypt
from datetime import datetime, date

app = Flask(__name__)

# Security & Database Configuration
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:dataengineer2026@localhost:5432/heatmap_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ----------------------------
# USER TABLE
# ----------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------------
# TASK TABLE (SaaS Grade)
# ----------------------------

class Task(db.Model):
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="Pending")
    priority = db.Column(db.String(50), default="Medium")
    due_date = db.Column(db.Date, nullable=True)
    
    # Collaboration Logic
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="tasks_created")
    assignee = db.relationship("User", foreign_keys=[assigned_to], backref="tasks_assigned")

# ----------------------------
# HEATMAP TABLE
# ----------------------------

class Heatmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    day_index = db.Column(db.Integer)
    value = db.Column(db.Integer, default=0)

# ----------------------------
# NOTIFICATION TABLE
# ----------------------------

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------
# LOGIC HELPERS
# ----------------------------

def update_heatmap_for_today(user_id, status_type):
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    day_index = (today - start_of_year).days

    record = Heatmap.query.filter_by(user_id=user_id, day_index=day_index).first()

    if record:
        # Increment intensity for completions (Max 4)
        if status_type == 1:
            record.value = min(record.value + 1, 4)
        else:
            record.value = status_type
    else:
        record = Heatmap(user_id=user_id, day_index=day_index, value=status_type)
        db.session.add(record)
    
    db.session.commit()

def check_overdue_tasks(user_id):
    today = date.today()
    overdue_tasks = Task.query.filter(
        Task.created_by == user_id,
        Task.due_date < today,
        Task.status != "Completed"
    ).all()

    if overdue_tasks:
        update_heatmap_for_today(user_id, 3) # Red/Overdue

# ----------------------------
# CORE ROUTES
# ----------------------------

@app.route("/")
@login_required
def home():
    check_overdue_tasks(current_user.id)
    
    # Dashboard Metrics
    total_tasks = Task.query.filter_by(created_by=current_user.id).count()
    completed = Task.query.filter_by(created_by=current_user.id, status="Completed").count()
    pending = Task.query.filter_by(created_by=current_user.id, status="Pending").count()
    inprogress = Task.query.filter_by(created_by=current_user.id, status="In Progress").count()
    
    rate = round((completed / total_tasks) * 100, 2) if total_tasks > 0 else 0

    return render_template("index.html", 
                           total_tasks=total_tasks, 
                           completed_tasks=completed, 
                           pending_tasks=pending, 
                           inprogress_tasks=inprogress, 
                           completion_rate=rate)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        user = User(username=request.form["username"], email=request.form["email"], password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/tasks")
@login_required
def tasks():
    filter_type = request.args.get("filter")
    users = User.query.all()
    today = date.today()

    query = Task.query.filter((Task.created_by == current_user.id) | (Task.assigned_to == current_user.id))

    if filter_type == "completed": query = query.filter(Task.status == "Completed")
    elif filter_type == "pending": query = query.filter(Task.status == "Pending")
    elif filter_type == "overdue": query = query.filter(Task.due_date < today, Task.status != "Completed")

    return render_template("tasks.html", tasks=query.all(), users=users, current_date=today)

@app.route("/create_task", methods=["POST"])
@login_required
def create_task():
    due = request.form["due_date"]
    due_date = datetime.strptime(due, "%Y-%m-%d").date() if due else None
    
    task = Task(
        title=request.form["title"],
        description=request.form["description"],
        priority=request.form["priority"],
        assigned_to=request.form["assigned_to"],
        created_by=current_user.id,
        due_date=due_date
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/update_status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get(task_id)
    if task:
        status = request.form["status"]
        # Heatmap Mapping: 1:Success | 2:Active | 5:Blocked
        if status == "Completed": update_heatmap_for_today(current_user.id, 1)
        elif status == "In Progress": update_heatmap_for_today(current_user.id, 2)
        elif status == "Blocked": update_heatmap_for_today(current_user.id, 5)
        
        task.status = status
        db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/data")
@login_required
def get_data():
    records = Heatmap.query.filter_by(user_id=current_user.id).all()
    return jsonify({r.day_index: r.value for r in records})

@app.route("/chart-data")
@login_required
def chart_data():
    tasks = Task.query.filter_by(created_by=current_user.id, status="Completed").all()
    counts = {}
    for t in tasks:
        day = t.created_at.strftime("%Y-%m-%d")
        counts[day] = counts.get(day, 0) + 1
    return jsonify({"labels": list(counts.keys()), "values": list(counts.values())})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)