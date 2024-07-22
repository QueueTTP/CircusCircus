# Add jsonify for dynamic likes and dislikes -Peter
from flask import jsonify, request
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from forum.models import User, Post, Comment, Subforum, Message, valid_content, valid_title, db, generateLinkPath, error
from forum.user import username_taken, email_taken, valid_username
import markdown 

##
# This file needs to be broken up into several, to make the project easier to work on.
##

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

@rt.route('/private_messages', methods=['GET', 'POST'])
@login_required
def private_messages():
    if request.method == 'POST':
        receiver_username = request.form['receiver']
        message_content = request.form['message']

        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            flash('User not found', 'error')
            return redirect(url_for('routes.private_messages'))

        new_message = Message(sender_id=current_user.id, receiver_id=receiver.id, message=message_content)
        db.session.add(new_message)
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('routes.private_messages'))

    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.postdate.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.postdate.desc()).all()
    
    return render_template('private_messages.html', received_messages=received_messages, sent_messages=sent_messages)

@login_required
@rt.route('/action_logout')
def action_logout():
    #todo
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
    # if not valid_password(password):
    #   errors.append("Password is not valid!")
    #   retry = True
    if retry:
        return render_template("login.html", errors=errors)
    user = User(email, username, password)
    if user.username == "admin":
        user.admin = True
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
    if not subforum.path:
        subforumpath = generateLinkPath(subforum.id)

    subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
    return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforumpath)

@rt.route('/loginform')
def loginform():
    return render_template("login.html")


@login_required
@rt.route('/addpost')
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
    if not post.subforum.path:
        subforumpath = generateLinkPath(post.subforum.id)
    comments = Comment.query.filter(Comment.post_id == postid).order_by(Comment.id.desc()) # no need for scalability now
    post_content_html = markdown.markdown(post.content)

    return render_template("viewpost.html", post=post, post_content_html=post_content_html, path=subforumpath, comments=comments)

@login_required
@rt.route('/action_comment', methods=['POST', 'GET'])
def comment():
    post_id = int(request.args.get("post"))
    post = Post.query.filter(Post.id == post_id).first()
    if not post:
        return error("That post does not exist!")
    content = request.form['content']
    postdate = datetime.datetime.now()
    comment = Comment(content, postdate)
    current_user.comments.append(comment)
    post.comments.append(comment)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post_id))

@login_required
@rt.route('/action_post', methods=['POST'])
def action_post():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return redirect(url_for("subforums"))

    user = current_user
    title = request.form['title']
    content = request.form['content']
    image_url=request.form.get('image_url')  # Get the image URL from the form
    video_url=request.form.get('video_url')  # Get the video URL from the form

    # Get the value of the checkbox
    public_view = request.form.get('public_view') == '1'
    #check for valid posting
    errors = []
    retry = False
    if not valid_title(title):
        errors.append("Title must be between 4 and 140 characters long!")
        retry = True
    if not valid_content(content):
        errors.append("Post must be between 10 and 5000 characters long!")
        retry = True
    if retry:
        return render_template("createpost.html",subforum=subforum,  errors=errors)

    # Create the post object with the public_view value
    post = Post(
        title=title, 
        content=content, 
        postdate=datetime.datetime.now(), 
        public_view=public_view, 
        image_url=image_url, 
        video_url=video_url
    )
    subforum.posts.append(post)
    user.posts.append(post)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post.id))


# # Added likes and dislikes capability here -Peter
@rt.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    print(f"Received request to like post with ID: {post_id}") # Debug log
    post = Post.query.get_or_404(post_id)
    print(f"Current like count: {post.like_count}") # Debug log
    post.like_count = (post.like_count or 0) + 1
    db.session.commit()
    print(f"New like count: {post.like_count}") # Debug log
    return jsonify(success=True, like_count=post.like_count)

@rt.route('/dislike_post/<int:post_id>', methods=['POST'])
@login_required
def dislike_post(post_id):
    post = Post.query.get_or_404(post_id)
    print(f"Disliking post with ID: {post_id}, current dislike count: {post.dislike_count}")
    post.dislike_count = (post.dislike_count or 0) + 1
    db.session.commit()
    print(f"New dislike count: {post.dislike_count}")
    return jsonify(success=True, dislike_count=post.dislike_count)

@rt.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.form.get('theme') == 'true'
    current_user.theme = theme
    db.session.commit()
    return '', 204  # No content

