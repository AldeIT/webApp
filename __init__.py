from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class clienti(db.Model):
    cf = db.Column("cf", db.String(16), primary_key=True)
    nome = db.Column("nome", db.String(30))
    cognome = db.Column("cognome", db.String(30))
    ntelefono = db.Column("ntelefono", db.String(10))
    email = db.Column("email", db.String(100))
    password = db.Column("password", db.String(20))

    def __init__(self, cf,  nome, cognome, ntelefono, email, password):
        self.cf = cf
        self.nome = nome
        self.cognome = cognome
        self.ntelefono = ntelefono
        self.email = email
        self.password = password


@app.route("/", methods=["GET", "POST"])
def home():
    password = "meccanico"
    frase=""
    if request.method == "POST":
        session.permanent = True
        user = request.form["n"]
        if user==password:
            session["pass"] = user
            return redirect(url_for("riparazioni"))
        else:
            frase="password errata"
            return render_template("index.html", frase=frase)
    else:
        return render_template("index.html", frase="")

@app.route("/riparazioni")
def riparazioni():
    if "pass" in session:
        return render_template("riparazioni.html")
    else:
        return redirect(url_for("home"))

@app.route("/storico")
def storico():
    if "pass" in session:
        return render_template("riparazioni.html")
    else:
        return redirect(url_for("home"))


@app.route("/aggiuntariparazioni")
def aggiuntariparazioni():
    if "pass" in session:
        return render_template("riparazioni.html")
    else:
        return redirect(url_for("home"))


@app.route("/aggiuntaclienti", methods=["GET", "POST"])
def aggiuntaclienti():
    if "pass" in session:
        if request.method == "POST":
            cf = request.form["cf"]
            nome = request.form["nome"]
            cognome = request.form["cognome"]
            ntelefono = request.form["ntelefono"]
            email = request.form["email"]
            password = None
            check_cliente = clienti.query.filter_by(cf=cf).first()
            if check_cliente:
                return render_template("addclienti.html", frase="cf già inserito")
            else:
                cliente = clienti(cf, nome, cognome, ntelefono, email, password)
                db.session.add(cliente)
                db.session.commit()
                return render_template("addclienti.html", frase="aggiunto")
        else:
            return render_template("addclienti.html")
    else:
        return redirect(url_for("home"))


@app.route("/aggiuntamezzi")
def aggiuntamezzi():
    if "pass" in session:
        return render_template("riparazioni.html")
    else:
        return redirect(url_for("home"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug = True)
