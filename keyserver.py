from flask import Flask, g, render_template
import sqlite3
from Crypto.Hash import SHA256
from Crypto.Cipher import ARC4
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
	    values[3] = b64encode(ARC4.new(values[1]).encrypt(values[3]))
	    values[1] = SHA256.new(values[1]).hexdigest()
            q = "INSERT INTO users (username, pwdhash, realname, privkeyenc, pubkey) VALUES (?,?,?,?,?)"
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
    return "mainpage"#render_template("mainpage.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    return "Register"

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        validUser = False# TODO search for user in database        
        if validUser:
            session["logged_in"] = True
            flash("Welcome " + username + " to NapierKeyServer")
            return redirect(url_for("")) # TODO
        else:
            error = "Invalid user credentials!"
    else:
	app.logger.error("Login request is not POST method")
        error = "Invalid request."
    
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You are now logged out")
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(error):
    return "Sorry :( This page does not exist. 404"

if __name__ == "__main__":
    app.logger.debug("Running keyserver on http://" + app.config["HOST"] + ":" + str(app.config["PORT"]))
    app.run(app.config["HOST"], app.config["PORT"])
