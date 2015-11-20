from Flask import Flask


app = Flask(__name__)

@app.route("/")
def mainpage():
    return render_template("mainpage.html")


@app.route("/register", methods=["GET", "POST"])
def register():


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
            return redirect(url_for(""))
        else:
            error = "Invalid user credentials!"
    else:
        error = "Invalid request."
    
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You are now logged out")
    return redirect(url_for("login"))
