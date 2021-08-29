from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_ckeditor import CKEditor
import json
import math
import os
from flask_mail import Mail
from datetime import datetime


with open('config.json', "r") as c:
    params = json.load(c)['parameters']

app = Flask(__name__)
ckeditor = CKEditor(app)

app.secret_key = 'secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)


if(params['local_server']):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']

db = SQLAlchemy(app)



class Contacts(db.Model):
    
    '''
    The default value of unique = False  &  nullable = True that's nullable is sed and unique can be canceled if you want it to be false
    '''


    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(300), nullable=False)
    date = db.Column(db.String(50), nullable=False)


class Posts(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=False, nullable=False)
    tagline = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    img_file = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)




@app.route("/")
def home():
    return render_template('home.html', templateParams=params)



@app.route("/posts")
def posts():

    posts = Posts.query.filter_by().all()
    posts.reverse()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = str(request.args.get('page'))
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

    if page==1:
        prev = '#'
        next = "/posts?page=" + str(page+1)
    elif page==last:
        prev = "/posts?page=" + str(page-1)
        next = '#'
    else:
        prev = "/posts?page=" + str(page-1)
        next = "/posts?page=" + str(page+1)

    # posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    allPosts = Posts.query.all()
    return render_template('index.html', allPosts=allPosts, templateParams=params, page=page, last=last, posts=posts, prev=prev, next=next)



@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', templateParams=params, post=post)



@app.route("/about")
def about():
    return render_template('about.html', templateParams=params)



@app.route("/uploader", methods=['POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded successfully"



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')



@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        posts.reverse()
        return render_template('dashboard.html', templateParams=params, posts=posts)

    if request.method=='POST':
        # Redirect to Admin panel
        username = request.form.get('uname')
        userpassword = request.form.get('password')

        if username == params['admin_user'] and userpassword == params['admin_password']:
            # Set the session variable
            session['user'] = username
            posts = Posts.query.all()

            return render_template('dashboard.html', templateParams=params, posts=posts)

    return render_template('login.html', templateParams=params)



@app.route("/edit/<string:sno>", methods=['GET' ,'POST'])
def edit_route(sno):
    
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('ckeditor')

            # This was for old image input tag in edit.html 
            # img_file = request.form.get('img_file')

            f = request.files['img_file']
            img_file = f.filename

            # print(img_file)
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, tagline=tagline, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.tagline = tagline
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', templateParams=params, sno=sno, post=post)



@app.route("/contact", methods=["GET","POST"])
def contact():
    if (request.method == 'POST'):
        '''Add Entry to the Database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone-num')
        message = request.form.get('message')

        entry_to_db = Contacts(name=name, email=email, phone=phone_num, msg=message, date=datetime.now())
        db.session.add(entry_to_db)
        mail.send_message("New message from " + name,
        sender = email,
        recipients = [params['gmail_user']],
        body = message + '\n\nPhone Num: ' + phone_num
        )
        db.session.commit()
        flash('Thanks for submitting your details. We will get back to you soon!', 'success')

    return render_template('contact.html', templateParams=params)


if __name__ == "__main__":
    app.run()