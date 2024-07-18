from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
import datetime
from forum.models import User, Post, Comment, Subforum, valid_content, valid_title, db, generateLinkPath, error
from forum.user import username_taken, email_taken, valid_username

rt = Blueprint('routes', __name__, template_folder='templates')

@rt.route('/action_login', methods=['POST'])
def action_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user)
    else:
        errors = []
        errors.append("Username or password is incorrect!")
        return render_template("login.html", errors=errors)
    return redirect("/")

@rt.route('/action_logout')
@login_required
def action_logout():
    logout_user()
    return redirect("/")

@rt.route('/action_createaccount', methods=['POST'])
def action_createaccount():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    errors = []
    retry = False
    if username_taken(username):
        errors.append("Username is already taken!")
        retry=True
    if email_taken(email):
        errors.append("An account already exists with this email!")
        retry = True
    if not valid_username(username):
        errors.append("Username is not valid!")
        retry = True
    if retry:
        return render_template("login.html", errors=errors)
    user = User(email=email, username=username, password=password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect("/")

@rt.route('/subforum')
def subforum():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")
    posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
    subforumpath = generateLinkPath(subforum.id)
    subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
    return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforumpath)

@rt.route('/loginform')
def loginform():
    return render_template("login.html")

@rt.route('/addpost')
@login_required
def addpost():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")
    return render_template("createpost.html", subforum=subforum)

@rt.route('/viewpost')
def viewpost():
    postid = int(request.args.get("post"))
    post = Post.query.filter(Post.id == postid).first()
    if not post:
        return error("That post does not exist!")
    generateLinkPath(post.subforum.id)
    comments = Comment.query.filter(Comment.post_id == postid).order_by(Comment.id.desc())
    return render_template("viewpost.html", post=post, comments=comments)

@rt.route('/action_comment', methods=['POST', 'GET'])
@login_required
def comment():
    post_id = int(request.args.get("post"))
    post = Post.query.filter(Post.id == post_id).first()
    if not post:
        return error("That post does not exist!")
    content = request.form['content']
    postdate = datetime.datetime.now()
    comment = Comment(content=content, timestamp=postdate, post_id=post.id, user_id=current_user.id)
    db.session.add(comment)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post.id))

@rt.route('/action_post', methods=['POST'])
@login_required
def action_post():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return redirect(url_for("rt.subforum"))
    user = current_user
    title = request.form['title']
    content = request.form['content']
    errors = []
    retry = False
    if not valid_title(title):
        errors.append("Title must be between 4 and 140 characters long!")
        retry = True
    if not valid_content(content):
        errors.append("Post must be between 10 and 5000 characters long!")
        retry = True
    if retry:
        return render_template("createpost.html", subforum=subforum, errors=errors)
    post = Post(title=title, content=content, timestamp=datetime.datetime.now(), user_id=user.id, subforum_id=subforum.id)
    db.session.add(post)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post.id))