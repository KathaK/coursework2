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
    app.run(app.config["HOST"])
