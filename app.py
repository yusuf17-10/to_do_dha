from flask import Flask , render_template,request,redirect,session
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import nullslast


 
app=Flask(__name__)
app.secret_key="my_secrect"

#configure sql alchemy
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

#database model

#user details 
class User(db.Model):
    #class variables
    id  = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(25),unique=True,nullable=False)
    password = db.Column(db.String(150),nullable=False)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    def set_pass(self,password):
        self.password=generate_password_hash(password)
    
    def check_pass(self,password):
        return check_password_hash(self.password,password)

#task details in database
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))

    timer_duration = db.Column(db.String(10))
    schedule_at = db.Column(db.DateTime)

    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)




#routes
@app.route("/")
def home():
    if "username" in session:
        return redirect("/dashboard")
    return render_template("index.html")

#login route 
@app.route("/login",methods=["POST"])
def login():
    #collects the data 
    username=request.form.get("username")
    password=request.form.get("password")
    user = User.query.filter_by(username=username).first()
    if user and user.check_pass(password):
        session["username"]=username
        return redirect("/dashboard")
    else:
        return redirect("/")


#register 
@app.route("/register",methods=["POST","GET"])
def register():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user=User.query.filter_by(username=username).first()
        if user:
            return render_template("index.html",error="user already exist")
        else:
            new_user=User(username=username)
            new_user.set_pass(password)
            new_user.email=request.form.get("email")
            new_user.name=request.form.get("name")
            new_user.phone=request.form.get("phone")
            db.session.add(new_user)
            db.session.commit()
            session["username"] = username
            return redirect("/dashboard")
    else:
        return render_template("register.html")



#logout 
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    username=session["username"]
    user=User.query.filter_by(username=username).first()
    tasks=Task.query.filter_by(user_id=user.id,completed=False).order_by(nullslast(Task.schedule_at)).all()
    return render_template("dashboard.html",name=user.name,tasks=tasks)

@app.route("/create", methods=["GET", "POST"])
def create():
    if "username" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form.get("title")
        if  title:
            description = request.form.get("description")
            timer_duration = request.form.get("timer_duration")
            schedule_at_str = request.form.get("schedule_at")
            schedule_at = None
            if schedule_at_str:
                schedule_at = datetime.strptime(schedule_at_str,"%Y-%m-%dT%H:%M")
            task = Task(
                title=title,
                description=description,
                timer_duration=timer_duration,
                schedule_at=schedule_at,
                user_id=User.query.filter_by(
                    username=session["username"]
                ).first().id
            )
            db.session.add(task)
            db.session.commit()
            return redirect("/dashboard")  
    return render_template("create.html")

@app.route("/task/<int:task_id>")
def task(task_id):
    if "username" not in session:
        return redirect("/login")
    task=Task.query.get(task_id)
    return render_template("task.html",task=task)

@app.route("/task/<int:task_id>/update",methods=["POST"])
def update(task_id):
    if "username" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        timer_duration = request.form.get("timer_duration")
        schedule_at_str = request.form.get("schedule_at")
        schedule_at = None
        if schedule_at_str:
            schedule_at = datetime.strptime(schedule_at_str,"%Y-%m-%dT%H:%M")
        task = Task.query.get(task_id)
        task.title=title
        task.description=description
        task.timer_duration=timer_duration
        task.schedule_at=schedule_at
        db.session.commit()
    return redirect("/dashboard")

@app.route("/delete/<int:task_id>",methods=["POST"])
def  delete(task_id):
    if "username" not in session:
        return redirect("/login")
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/finish/<int:task_id>",methods=["POST"])
def finish(task_id):
    task=Task.query.get(task_id)
    task.completed=True
    db.session.commit()
    return redirect("/dashboard")

@app.route("/finished")
def finished_tasks():
    if "username" not in session:
        return redirect("/login")

    user = User.query.filter_by(username=session["username"]).first()

    tasks = Task.query.filter_by(user_id=user.id, completed=True).order_by(nullslast(Task.schedule_at)).all()

    return render_template("finished.html",name=user.name,tasks=tasks)




if __name__ in "__main__":
    with app.app_context():
        db.create_all()



    app.run(debug=True)
