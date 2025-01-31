from flask import Flask, render_template, request, redirect, url_for, session
from Modules.Recommender import content_based_recommender
from flask_mysqldb import MySQL
from Modules.Data import *
import MySQLdb.cursors
import re

# Load the Dataframes
load()

# Preprocess the Dataframes
df = pre_process()
print("\n----- df -----")
print(df.head(5))

# Create the tfidf matrix from the dataframe
tfidf_matrix = create_tfidf_vector(df)

# Compute the Cosine Similarities
cosine_similarities = calculate_cosine(tfidf_matrix)

# Initialise Flask
app = Flask(__name__)

# Initialise the secret key
app.secret_key = "your secret key"

# Configure the Database Connection Details
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "admin"  # Change it to your SQL password
app.config["MYSQL_DB"] = "pythonlogin"

# Intialize MySQL
mysql = MySQL(app)

@app.route("/", methods=["GET", "POST"])
def home_login():
    msg = ""
    if "loggedin" in session:
        # User is loggedin show them the home page
        return render_template("home.html", username=session["username"])
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == "POST" and "username" in request.form and "password" in request.form:
        # Create variables for easy access
        username = request.form["username"]
        password = request.form["password"]
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s", (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            # Redirect to home page
            return redirect(url_for("home_login"))
        else:
            # Account doesnt exist or username/password incorrect
            msg = "Incorrect username/password!"
    # Show the login form with message (if any)
    return render_template("index.html", msg=msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    # Output message if something goes wrong...
    msg = ""
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == "POST" and "username" in request.form and "password" in request.form and "email" in request.form:
        # Create variables for easy access
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        account = cursor.fetchone()
        url = "home"
        # If account exists show error and validation checks
        if account:
            msg = "Account already exists!"
            url = "index"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email address!"
            url = "register"
        elif not re.match(r"[A-Za-z0-9]+", username):
            msg = "Username must contain only characters and numbers!"
            url = "register"
        elif not username or not password or not email:
            msg = "Please fill out the form!"
            url = "register"
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO accounts VALUES (NULL, %s, %s, %s)", (username, password, email,))
            mysql.connection.commit()
            msg = "You have successfully registered!"
            cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s", (username, password,))
            # Fetch one record and return result
            account = cursor.fetchone()
            if account:
                # Create session data, we can access this data in other routes
                session["loggedin"] = True
                session["id"] = account["id"]
                session["username"] = account["username"]
        return render_template(url + ".html", username=username, msg=msg)
    elif request.method == "POST":
        # Form is empty... (no POST data)
        msg = "Please fill out the form!"
    # Show registration form with message (if any)
    return render_template("register.html", msg=msg)

@app.route("/home", methods=["GET", "POST"])
def home():
    # Check if user is loggedin
    if "loggedin" in session:
        # User is loggedin show them the home page
        return render_template("home.html", username=session["username"])
    # User is not loggedin redirect to login page
    return redirect(url_for("home_login", msg="Successfully Logged out"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    # Check if user is loggedin
    if "loggedin" in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (session["id"],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template("profile.html", account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for("home_login"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    # Remove session data, this will log the user out
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    # Redirect to login page
    return render_template("index.html", msg="Successfully Logged out")

@app.route("/generate_recommendations", methods=["GET", "POST"])
def generate_recommendations():
    if "loggedin" in session:
        # Get the closes names to the game name provided by the user
        closest_titles = closest_names(df, request.form["gamename"])
        return render_template("generate_recommendations.html", default_closest_name=closest_titles[0], closest_names=closest_titles[1:])
    return redirect(url_for("home_login"))

@app.route("/display_recommendations", methods=["GET", "POST"])
def display_recommendations():
    if "loggedin" in session:
        recommended_games = content_based_recommender(
            request.form["gamename_from_dropdown"],
            request.form["platform"],
            float(request.form["min_score"]),
            int(request.form["how_many"]),
            request.form["sort_option"],
            int(request.form["min_year"]),
            )

        recommended_games = recommended_games.to_dict("index")
        print(recommended_games)

        return render_template("display_recommendations.html", recommended_games=recommended_games)
    
    return redirect(url_for("home_login"))

#app.run(debug=True, use_debugger=False, use_reloader=True)
app.run()