from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os
from werkzeug.utils import secure_filename  # Corrected import statement
from . import create_app
from .models import Post, Subforum, User  # Import the Subforum and User classes

db = SQLAlchemy()
login_manager = LoginManager()

app = create_app()
app.config['SITE_NAME'] = 'Schooner'
app.config['SITE_DESCRIPTION'] = 'a schooner forum'
app.config['FLASK_DEBUG'] = 1

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messaging.db'
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SITE_NAME'] = 'Schooner'
    app.config['SITE_DESCRIPTION'] = 'a schooner forum'
    app.config['FLASK_DEBUG'] = 1

    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from forum.routes import rt as forum_routes
    from forum.messaging import messaging_bp as messaging_routes

    app.register_blueprint(forum_routes)
    app.register_blueprint(messaging_routes, url_prefix='/messages')

    # Initialize database and subforums
    with app.app_context():
        db.create_all()
        init_site()

    @app.route('/')
    def index():
        subforums = Subforum.query.filter(Subforum.parent_id.is_(None)).order_by(Subforum.id)
        return render_template("subforums.html", subforums=subforums)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ... rest of the code ...

def init_site():
    print("creating initial subforums")
    admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here")
    add_subforum("Announcements", "View forum announcements here",admin)
    add_subforum("Bug Reports", "Report bugs with the forum here", admin)
    add_subforum("General Discussion", "Use this subforum to post anything you want")
    add_subforum("Other", "Discuss other things here")

def add_subforum(title, description, parent=None):
    sub = Subforum(title, description)
    if parent:
        for subforum in parent.subforums:
            if subforum.title == title:
                return
        parent.subforums.append(sub)
    else:
        subforums = Subforum.query.filter(Subforum.parent_id == None).all()
        for subforum in subforums:
            if subforum.title == title:
                return
        db.session.add(sub)
    print("adding " + title)
    db.session.commit()
    return sub

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)

with app.app_context():
    db.create_all() # TODO this may be redundant
    if not Subforum.query.all():
        init_site()

@app.route('/')
def index():
    subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
    return render_template("subforums.html", subforums=subforums)



#Qian
@app.route('/createpost',methods=['Get','Post'])
def create_post():
    if request.method == 'Post':
        title = request.form['title']
        content = request.form['content']
        filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_PHOTO'], filename))
        post = Post(title=title, content=content, image_filename=filename)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('createpost.html')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)