from flask import Flask, g, render_template, session, render_template, url_for, flash, request, redirect
import sqlite3
import re
from Crypto.Hash import SHA256
from Crypto.Cipher import ARC4
from Crypto.PublicKey import RSA
from Crypto import Random
from base64 import b64encode, b64decode

app = Flask(__name__)
app.config.from_envvar("NAPIER_KEYSERVER_CONFIG")

################################################################
# database 

def connect_db():
    return sqlite3.connect(app.config["DATABASE"])

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = connect_db()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def fill_db():
    print("Filling database with examples")
    with app.app_context():
        db = get_db()
        file = open("exampledata/users.example", "r")
        for line in file:
            line = line.rstrip("\n")
            print(line.split("-"))
            values = line.split("-")
	    rnd = Random.new().read
            key = RSA.generate(1024, rnd)
            pub = key.publickey().exportKey()
            privenc = b64encode(ARC4.new(values[1]).encrypt(key.exportKey()))
            values.append(privenc)
            values.append(pub)
	    values[1] = SHA256.new(values[1]).hexdigest()

            print values
            q = "INSERT INTO users (username, pwdhash, realname, gender, privkeyenc, pubkey) VALUES (?,?,?,?,?,?)"
            query_db(q, values)
        db.commit()
        file = open("exampledata/friends.example", "r")
        for line in file:
            line = line.rstrip("\n")
            print(line.split("-"))
	    user1, user2 = line.split("-")
	    q = "INSERT INTO friends (user1, user2) VALUES (?,?)"
	    query_db(q, [user1, user2])
	    query_db(q, [user2, user1])
        db.commit()

	file = open("exampledata/messages.example")
        for line in file:
            line = line.rstrip("\n")
            print(line.split("-"))
            sender, receiver, message = line.split("-")

            q = "SELECT pubkey FROM users WHERE username = ?"
            pubkey_receiver = RSA.importKey(query_db(q, [receiver], one=True)[0])
            message_enc = b64encode(pubkey_receiver.encrypt(message, 77)[0])

            q = "INSERT INTO messages (sender, receiver, content) VALUES (?,?,?)"
            query_db(q, [sender, receiver, message_enc])
        db.commit()

def init_db():
    print("Initializing database.")
    with app.app_context():
        db = get_db()
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()
        fill_db()
#
################################################################

@app.route("/")
def mainpage():
    return render_template("mainpage.html")


@app.route("/register", methods=["GET", "POST"])
def register():
   error = None
   if request.method == "POST":
       print request.form["gender"]
       if "accept" in request.form:

	   if "gender" in request.form:
               username = request.form["username"]
               password = request.form["password"]
               repeat_password = request.form["repeat_password"]
               first_name = request.form["first_name"]
               last_name = request.form["last_name"]

               gender = request.form["gender"]
               accept = request.form["accept"]
                

               q = "SELECT username FROM users WHERE username = ?"
               if not error and username and not query_db(q, [username], one = True):
                   if password and re.match(r"[A-Za-z0-9@#$%^&+=]+", password):
                       if repeat_password and password == repeat_password:
                            
                           pwdhash = SHA256.new(password).hexdigest()
                            
                           rnd = Random.new().read
                           key = RSA.generate(1024, rnd)
                           pub = key.publickey().exportKey()
                           privenc = b64encode(ARC4.new(password).encrypt(key.exportKey()))
                  
                           realname = first_name + " " + last_name
                            
                           q = "INSERT INTO users (username, pwdhash, realname, gender, privkeyenc, pubkey) VALUES (?,?,?,?,?,?)"
                           query_db(q, [username, pwdhash, realname, gender, privenc, pub])
                           get_db().commit()

                           session["logged_in"] = True
                           session["user"] = username
			   session["locked"] = True
                           return redirect(url_for("show_profile"))
                       else:
                           error = "Passwords do not match."
                   else:
                       error = "Password must only contain letters A-Z/a-z, numbers 0-9 and the following signs @#$%^&+="
               else:
                   error = "Username already taken."
           else:
               error = "Please specify your gender."
       else:
           error = "You have to accept the terms and conditions of Napier Public Key Server"

   return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
	res = query_db("SELECT pwdhash FROM users WHERE username = ?", [username], one=True)
        if res:
            pwdhash = res[0]
            if pwdhash and SHA256.new(password).hexdigest() == pwdhash:
                session["logged_in"] = True
                session["user"] = username
		session["locked"] = True
                return redirect(url_for("show_profile"))
            else:
                error = "Invalid user credentials!"
        else:
	    error = "Invalid user credentials!"
    
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("user", None)
    session.pop("locked", None)
    flash("You are now logged out")
    return redirect(url_for("login"))

def get_user_info(username):

    q = "SELECT realname, pubkey, gender FROM users WHERE username = ?"
    realname, pubkey, gender = query_db(q, [username], one=True)

    q = "SELECT user2 FROM friends WHERE user1 = ?"
    res = query_db(q, [username])
    friends = [friend[0] for friend in res]

    q = "SELECT sender, content FROM messages WHERE receiver=?"
    messages = query_db(q, [username])

    if not session.get("locked") and username == session.get("user"):
        password = session.get("password")
        tmp = []
        for (user, message) in messages:
            content_enc = b64decode(message)

            q = "SELECT privkeyenc FROM users WHERE username = ?"
            res = query_db(q, [username], one=True)[0]
            priv_receiver = ARC4.new(password).decrypt(b64decode(res))
            key = RSA.importKey(priv_receiver)
            message = key.decrypt(content_enc)

            tmp.append((user, message))

        messages = tmp

    info = {"realname":realname, "pubkey":pubkey, "friends":friends, "gender":gender, "messages":messages}

    return info

@app.route("/profile")
def show_profile():
    if not session.get("logged_in"):
        redirect(url_for("login"))

    user = session.get("user")

    q = "SELECT realname, pubkey FROM users WHERE username = ?"
    realname, pubkey = query_db(q, [user], one=True)

    q = "SELECT user2 FROM friends WHERE user1 = ?"
    res = query_db(q, [user])
    friends = [friend[0] for friend in res]
	
    info = get_user_info(user)
    
    return render_template("profile.html", username=user, friends=info["friends"], realname=info["realname"], pubkey=info["pubkey"], gender=info["gender"], messages=info["messages"])

@app.route("/profile/lock")
def lock_profile():
    session["locked"] = True
    session.pop("password", None)
    return redirect(url_for("show_profile"))

@app.route("/profile/unlock", methods=["GET", "POST"])
def unlock_profile():
    error = None
    username = session.get("user")
    password = request.form["password"]

    if request.method == "POST":
        pwdhash = query_db("SELECT pwdhash FROM users WHERE username = ?", [username], one=True)[0]
        if pwdhash and SHA256.new(password).hexdigest() == pwdhash:
            session["password"] = password
            session["locked"] = False
        else:
            flash("Invalid password.")

    return redirect(url_for("show_profile"))


@app.route("/user/<username>")
def show_user(username):
    info = get_user_info(username)
 
    already_friends = False
    if session.get("logged_in"):
        q = "SELECT user1, user2 FROM friends WHERE (user1 = ? AND user2 = ?)"
        if query_db(q, [username, session.get("user")]):
            already_friends = True

    return render_template("profile.html", username=username, friends=info["friends"], realname=info["realname"], pubkey=info["pubkey"], gender=info["gender"], already_friends=already_friends, messages=info["messages"])


@app.route("/user/<username>/add")
def add_friend(username):
    user = session.get("user")
    q = "INSERT INTO friends (user1, user2) VALUES (?,?)"
    query_db(q, [user, username])
    query_db(q, [username, user])
    get_db().commit()

    return redirect(url_for("show_user", username=username))

@app.route("/search")
def search():
    error = None
    username = request.args["u"]

    q = "SELECT username FROM users WHERE username = ?"
    res = query_db(q, [username])
    print res
    if res:
        return redirect(url_for("show_user", username=username))
    else:
        flash("This user does not exist.")
    
    return redirect(request.referrer)


@app.route("/info")
def info():
    return render_template("info.html")

@app.errorhandler(404)
def page_not_found(error):
    return "Sorry :( This page does not exist. 404"

if __name__ == "__main__":
    app.logger.debug("Running keyserver on http://" + app.config["HOST"] + ":" + str(app.config["PORT"]))
    app.run(host=app.config["HOST"], port=app.config["PORT"])
