from flask import flash,redirect,url_for,session,logging,request
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
           return f(*args, **kwargs)
        else:
            flash("You must be logged in to view this page!","warning")
            return redirect(url_for("login"))
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            flash("You must be logged out to view this page!","warning")
            return redirect(url_for("index"))
        else:
            return f(*args, **kwargs)    
    return decorated_function