from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta, datetime
import pytz
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Clienti(db.Model):
    cf = db.Column("cf", db.String(16), primary_key=True)
    nome = db.Column("nome", db.String(30))
    cognome = db.Column("cognome", db.String(30))
    ntelefono = db.Column("ntelefono", db.String(10))
    email = db.Column("email", db.String(100))
    password = db.Column("password", db.String(20))
    mecchina = db.relationship("Mezzi", backref="clienti", lazy=True)
    def __init__(self, cf,  nome, cognome, ntelefono, email, password):
        self.cf = cf
        self.nome = nome
        self.cognome = cognome
        self.ntelefono = ntelefono
        self.email = email
        self.password = password

class Mezzi(db.Model):
    targa = db.Column("targa", db.String(10), primary_key=True)
    marca = db.Column("marca", db.String(30))
    modello = db.Column("modello", db.String(30))
    cilindrata = db.Column("cilindrata", db.String(10))
    potenza = db.Column("potenza", db.String(10))
    cfcliente = db.Column("cfcliente", db.String(20), db.ForeignKey('clienti.cf'), nullable=False)
    riparazione = db.relationship("Riparazioni", backref="mezzi", lazy=True)

    def __init__(self, targa, marca, modello, cilindrata, potenza, cfcliente):
        self.targa = targa
        self.marca = marca
        self.modello = modello
        self.cilindrata = cilindrata
        self.potenza = potenza
        self.cfcliente = cfcliente

class Riparazioni(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    stato = db.Column("stato", db.Boolean, default=False)
    inizio = db.Column("inizio", db.String(30))
    fine = db.Column("fine", db.String(30))
    prezzo = db.Column("prezzo", db.String(10))
    descrizione = db.Column("descrizione", db.String(50))
    targamezzo = db.Column("targamezzo", db.String(20), db.ForeignKey('mezzi.targa'), nullable=False)

    def __init__(self, stato, inizio, fine, prezzo, descrizione, targamezzo):
        self.stato = stato
        self.inizio = inizio
        self.fine = fine
        self.prezzo = prezzo
        self.descrizione = descrizione
        self.targamezzo = targamezzo


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

@app.route("/riparazioni", methods=["GET", "POST"])
def riparazioni():
    if "pass" in session:
        tz = pytz.timezone("Europe/Rome")
        riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
        if request.method == "POST":
            ids = Riparazioni.query.filter_by(fine="in corso...").all()
            for i in ids:
                if str(i._id) in request.form:
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    riparazione.stato=True
                    riparazione.fine=datetime.now(tz)
                    db.session.commit()
                    break
            riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso)
        else:

            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso)
    else:
        return redirect(url_for("home"))

@app.route("/storico", methods=["GET", "POST"])
def storico():
    if "pass" in session:
        if request.method=="POST":
            scelta = request.form["scelta"]
            if scelta=="CF":
                cfin = request.form["ricerca"]
                lista=Mezzi.query.filter_by(cfcliente=cfin).all()
                lista2 = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).filter_by(cf=cfin).all()
                return render_template("storico.html", controllo=1, listariparazioni=lista2, listamacchine=lista)
            elif scelta=="Targa":
                targain=request.form["ricerca"]
                lista=Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).filter_by(targa=targain).all()
                lista2 = Riparazioni.query.filter_by(targamezzo=targain).all()
                return render_template("storico.html", controllo=2, listariparazioni=lista2, listaproprietari=lista)
        else:
            lista1 = Clienti.query.all()
            lista2 = Mezzi.query.all()
            lista3 = Riparazioni.query.all()
            return render_template("storico.html", controllo=0, listariparazioni=lista3, listamezzi=lista2, listaclienti=lista1)
    else:
        return redirect(url_for("home"))

@app.route("/gestionale", methods=["GET", "POST"])
def gestionale():
    if "pass" in session:
        if request.method=="POST":
            if "scelta" in request.form:
                scelta = request.form["scelta"]
                if scelta=="Riparazioni":

                    lista = Riparazioni.query.all()
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista)
                elif scelta=="Mezzi":
                    lista = Mezzi.query.all()
                    return render_template("gestionale.html", controllo=1, listamezzi=lista)
                elif scelta=="Clienti":
                    lista = Clienti.query.all()
                    return render_template("gestionale.html", controllo=2, listaclienti=lista)
            ids = Riparazioni.query.all()
            for i in ids:
                if str(i._id) in request.form:
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    var = str(i._id)
                    if request.form[var + "stato"]=="False":
                        riparazione.stato=False
                    else:
                        riparazione.stato=True
                    riparazione.descrizione=request.form[var + "descrizione"]
                    riparazione.prezzo=request.form[var + "prezzo"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista)
            targhe = Mezzi.query.all()
            for i in targhe:
                if str(i.targa) in request.form:
                    mezzo = Mezzi.query.filter_by(targa=i.targa).first()
                    mezzo.marca = request.form[i.targa + "marca"]
                    mezzo.modello = request.form[i.targa + "modello"]
                    mezzo.cilindrata = request.form[i.targa + "cilindrata"]
                    mezzo.potenza = request.form[i.targa + "potenza"]
                    db.session.commit()
                    lista = Mezzi.query.all()
                    return render_template("gestionale.html", controllo=1, listamezzi=lista)
            cfs = Clienti.query.all()
            for i in cfs:
                if str(i.cf) in request.form:
                    cliente = Clienti.query.filter_by(cf=i.cf).first()
                    cliente.nome = request.form[i.cf + "nome"]
                    cliente.cognome = request.form[i.cf + "cognome"]
                    cliente.ntelefono = request.form[i.cf + "ntelefono"]
                    cliente.email = request.form[i.cf + "email"]
                    db.session.commit()
                    lista = Clienti.query.all()
                    return render_template("gestionale.html", controllo=2, listaclienti=lista)
            return render_template("gestionale.html")

        else:
            return render_template("gestionale.html")
    else:
        return redirect(url_for("home"))

@app.route("/aggiuntariparazioni", methods=["GET", "POST"])
def aggiuntariparazioni():
    if "pass" in session:
        tz = pytz.timezone("Europe/Rome")
        listamezzi = Mezzi.query.all()
        if request.method == "POST":
            stato = False
            inizio = datetime.now(tz)
            fine = "in corso..."
            prezzo = request.form["prezzo"]
            descrizione = request.form["descrizione"]
            targamezzo = request.form["targamezzo"]
            riparazione = Riparazioni(stato, inizio, fine, prezzo, descrizione, targamezzo)
            db.session.add(riparazione)
            db.session.commit()
            return render_template("addriparazioni.html", lista=listamezzi, frase="aggiunto")
        else:
            return render_template("addriparazioni.html", lista=listamezzi)
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
            check_cliente = Clienti.query.filter_by(cf=cf).first()
            if check_cliente:
                return render_template("addclienti.html", frase="cf già inserito")
            else:
                cliente = Clienti(cf, nome, cognome, ntelefono, email, password)
                db.session.add(cliente)
                db.session.commit()
                return render_template("addclienti.html", frase="aggiunto")
        else:
            return render_template("addclienti.html")
    else:
        return redirect(url_for("home"))


@app.route("/aggiuntamezzi", methods=["GET", "POST"])
def aggiuntamezzi():
    if "pass" in session:
        listaclienti = Clienti.query.all()
        if request.method == "POST":
            targa = request.form["targa"]
            marca = request.form["marca"]
            modello = request.form["modello"]
            cilindrata = request.form["cilindrata"]
            potenza = request.form["potenza"]
            cfcliente = request.form["cfcliente"]
            check_mezzo = Mezzi.query.filter_by(targa=targa).first()
            if check_mezzo:
                return render_template("addmezzi.html", lista=listaclienti, frase="targa già inserita")
            else:
                mezzo = Mezzi(targa, marca, modello, cilindrata, potenza, cfcliente)
                db.session.add(mezzo)
                db.session.commit()
                return render_template("addmezzi.html", lista=listaclienti, frase="aggiunto")
        else:

            return render_template("addmezzi.html", lista=listaclienti)
    else:
        return redirect(url_for("home"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug = True)
