#importazione dei pacchetti necessari
from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta, datetime
import pytz
from flask_sqlalchemy import SQLAlchemy
import time
import smtplib, ssl
from email.message import EmailMessage
from flask_mail import Mail, Message as MailMessage
#parametri di configurazione dell'app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'assistenza.mechsite@gmail.com'
app.config['MAIL_PASSWORD'] = 'Dnstoro123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
#Classe/Tabella DB CLienti(cf*, nome, cognome, ntelefono, email, password)
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

#Classe/Tabella DB Mezzi(targa*, marca, modello, cilindrata, potenza, cfcliente->)
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

#Classe/Tabella DB Riparazioni(id*, stato, inizio, fine, prezzo, descrizione, targamezzo->)
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

def inviamail(ricevente):
    msg = MailMessage('NoReply - Officina', sender='assistenza.mechsite@gmail.com', recipients=[ricevente.email])
    msg.body = "Buongiorno, \n la riparazione sul mezzo: " + ricevente.marca + " " + ricevente.modello + ", a nome: " + ricevente.nome + " " + ricevente.cognome + "è terminata.\nPrezzo Finale: " + ricevente.prezzo + "\nSaluti, MechSite"
    mail.send(msg)
    return 1
#pagina di login degli utenti
@app.route("/", methods=["GET", "POST"])
def accessoclienti():
    frase=""
    if request.method == "POST":
        session.permanent = True
        user = request.form["email"]
        check_mail = Clienti.query.filter_by(email=user).first()
        if check_mail:
            session["cliente"] = user
            return redirect(url_for("passwordclienti"))
        else:
            frase="email non trovata"
            return render_template("accessoclienti.html", frase=frase)
    else:
        return render_template("accessoclienti.html", frase="")

@app.route("/passwordclienti", methods=["GET", "POST"])
def passwordclienti():
    if "cliente" in session:
        if request.method == "POST":
            if "primapassword" in request.form:
                cliente = Clienti.query.filter_by(email=session["cliente"]).first()
                password = request.form["password"]
                passwordrepeat = request.form["passwordrepeat"]
                if password==passwordrepeat:
                    session.permanent = True
                    cliente.password=password
                    db.session.commit()
                    session["passcliente"]=password
                    return redirect(url_for("passwordclienti"))
                else:
                    return render_template("passwordclienti.html", controllo=0, frase="Password non coincidono")
            elif "accessopassword" in request.form:
                cliente = Clienti.query.filter_by(email=session["cliente"]).first()
                password = request.form["password"]
                if cliente.password==password:
                    session["passcliente"]=password
                    return redirect(url_for("riparazioniclienti"))
                else:
                    return render_template("passwordclienti.html", controllo=1, frase="Password errata")
        else:
            cliente = Clienti.query.filter_by(email=session["cliente"]).first()
            if cliente.password == None:
                return render_template("passwordclienti.html", controllo=0)
            else:
                return render_template("passwordclienti.html", controllo=1)
    else:
        return redirect(url_for("accessoclienti"))

#pagina che printa le riparazioni di un determinato utente
@app.route("/riparazioniclienti", methods=["GET", "POST"])
def riparazioniclienti():
    if "cliente" in session and "passcliente" in session:
        if request.method == "POST":
            if request.form["scelta"]=="Tutte":
                riparazioniincorso = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni.fine, Mezzi.marca, Mezzi.modello, Mezzi.targa).filter_by(email=session["cliente"]).all()
                return render_template("riparazioniclienti.html", controllo=0, listariparazioni=riparazioniincorso)
            elif request.form["scelta"]=="In corso":
                riparazioniincorso = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni.fine, Mezzi.marca, Mezzi.modello, Mezzi.targa).filter_by(email=session["cliente"]).all()
                return render_template("riparazioniclienti.html", controllo=1, listariparazioni=riparazioniincorso)
            elif request.form["scelta"]=="Terminate":
                riparazioniincorso = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni.fine, Mezzi.marca, Mezzi.modello, Mezzi.targa).filter_by(email=session["cliente"]).all()
                return render_template("riparazioniclienti.html", controllo=2, listariparazioni=riparazioniincorso)
        else:
            return render_template("riparazioniclienti.html")
    else:
        return redirect(url_for("accessoclienti"))

@app.route("/mezziclienti")
def mezziclienti():
    if "cliente" in session and "passcliente" in session:
        mezzicliente = Mezzi.query.join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Mezzi.targa, Mezzi.marca, Mezzi.modello, Mezzi.cilindrata, Mezzi.potenza).filter_by(email=session["cliente"]).all()
        return render_template("mezziclienti.html", listamezzi=mezzicliente)
    else:
        return redirect(url_for("accessoclienti"))

@app.route("/profilo", methods=["GET", "POST"])
def profilocliente():
    if "cliente" in session and "passcliente" in session:
        if request.method == "POST":
            return redirect(url_for("modificaprofilocliente"))
        else:
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            return render_template("profilocliente.html", cliente=clientein)
    else:
        return redirect(url_for("accessoclienti"))

@app.route("/modificaprofilo", methods=["GET", "POST"])
def modificaprofilocliente():
    if "cliente" in session and "passcliente" in session:
        if request.method == "POST":
            frase="Modificati: "
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            email=request.form["email"]
            ntelefono = request.form["ntelefono"]
            if request.form["password"]==request.form["passwordrepeat"]:
                password=request.form["password"]
                clientein.password=password
                frase += "Si Password "
            else:
                frase += "No Password"
            if clientein.email != email:
                clientein.email = email
                frase += "Si Email "
                session["cliente"]=email
            else:
                frase += "No Email"
            if clientein.ntelefono != ntelefono:
                clientein.ntelefono = ntelefono
                frase += "Si Ntelefono "
            else:
                frase += "No Ntelefono"
            db.session.commit()
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            return render_template("modificaprofilocliente.html", cliente=clientein, frase=frase)
        else:
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            return render_template("modificaprofilocliente.html", cliente=clientein)
    else:
        return redirect(url_for("accessoclienti"))

@app.route("/logoutcliente")
def logoutcliente():
    if "cliente" in session and "passcliente" in session:
        session.pop("cliente", None)
        session.pop("passcliente", None)
        return redirect(url_for("accessoclienti"))
    else:
        return redirect(url_for("accessoclienti"))

#Pagina di accesso Meccanico/Utenti(Da completare)
@app.route("/meccanico", methods=["GET", "POST"])
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

#Pagina Riparazioni in corso...
@app.route("/riparazioni", methods=["GET", "POST"])
def riparazioni():
    if "pass" in session:
        tz = pytz.timezone("Europe/Rome")
        riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
        if request.method == "POST":
            #Cerca le riparazioni in corso per poi printarle nella pagina
            ids = Riparazioni.query.filter_by(fine="in corso...").all()
            for i in ids:
                if str(i._id) in request.form:
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    ricevente = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns( Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.email, Clienti.nome, Clienti.cognome, Riparazioni.prezzo).filter_by(_id=i._id).first()
                    riparazione.stato=True
                    riparazione.fine=datetime.now(tz)
                    db.session.commit()
                    #n = inviamail(ricevente)
                    break
            riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso)
        else:

            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso)
    else:
        return redirect(url_for("home"))

#Pagina Storico Database
@app.route("/storico", methods=["GET", "POST"])
def storico():
    if "pass" in session:
        if request.method=="POST":
            scelta = request.form["scelta"]
            if scelta=="CF":
                #ricerca Mezzi e Riparazioni associate al CF inserito
                cfin = request.form["ricerca"]
                lista=Mezzi.query.filter_by(cfcliente=cfin).all()
                lista2 = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).filter_by(cf=cfin).all()
                return render_template("storico.html", controllo=1, listariparazioni=lista2, listamacchine=lista)
            elif scelta=="Targa":
                #ricerca Riparazioni e Proprietario associati alla Targa inserita
                targain=request.form["ricerca"]
                lista=Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).filter_by(targa=targain).all()
                lista2 = Riparazioni.query.filter_by(targamezzo=targain).all()
                return render_template("storico.html", controllo=2, listariparazioni=lista2, listaproprietari=lista)
            else:
                return render_template("storico.html", frase="record non trovati")
        else:
            #se non viene selezionata un'opzione vengono printati tutte le riparazione, clienti, mezzi
            lista1 = Clienti.query.all()
            lista2 = Mezzi.query.all()
            lista3 = Riparazioni.query.all()
            return render_template("storico.html", controllo=0, listariparazioni=lista3, listamezzi=lista2, listaclienti=lista1)
    else:
        return redirect(url_for("home"))

#Pagina Gestionale del Database
@app.route("/gestionale", methods=["GET", "POST"])
def gestionale():
    if "pass" in session:
        tz = pytz.timezone("Europe/Rome")
        if request.method=="POST":
            if "scelta" in request.form:
                scelta = request.form["scelta"]
                #In base alla scelta viene printato una tabella differente
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
                strdelete = str(i._id) + "delete"
                if str(i._id) in request.form:
                    #Codice per la modifica degli attributi delle Riparazioni
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    var = str(i._id)
                    if request.form[var + "stato"]=="In corso":
                        riparazione.stato=False
                        riparazione.fine = "in corso..."
                    elif request.form[var + "stato"]=="Terminato":
                        riparazione.stato=True
                        riparazione.fine = datetime.now(tz)
                    riparazione.descrizione=request.form[var + "descrizione"]
                    riparazione.prezzo=request.form[var + "prezzo"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista)
                elif strdelete in request.form:
                    Riparazioni.query.filter_by(_id=i._id).delete()
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista)

            targhe = Mezzi.query.all()
            for i in targhe:
                strdelete = str(i.targa) + "delete"
                if str(i.targa) in request.form:
                    mezzo = Mezzi.query.filter_by(targa=i.targa).first()
                    mezzo.marca = request.form[i.targa + "marca"]
                    mezzo.modello = request.form[i.targa + "modello"]
                    mezzo.cilindrata = request.form[i.targa + "cilindrata"]
                    mezzo.potenza = request.form[i.targa + "potenza"]
                    db.session.commit()
                    lista = Mezzi.query.all()
                    return render_template("gestionale.html", controllo=1, listamezzi=lista)
                elif strdelete in request.form:
                    Riparazioni.query.filter_by(targamezzo=i.targa).delete()
                    Mezzi.query.filter_by(targa=i.targa).delete()
                    db.session.commit()
                    lista = Mezzi.query.all()
                    return render_template("gestionale.html", controllo=1, listamezzi=lista)


            cfs = Clienti.query.all()
            for i in cfs:
                strdelete = str(i.cf) + "delete"
                if str(i.cf) in request.form:
                    cliente = Clienti.query.filter_by(cf=i.cf).first()
                    cliente.nome = request.form[i.cf + "nome"]
                    cliente.cognome = request.form[i.cf + "cognome"]
                    cliente.ntelefono = request.form[i.cf + "ntelefono"]
                    cliente.email = request.form[i.cf + "email"]
                    db.session.commit()
                    lista = Clienti.query.all()
                    return render_template("gestionale.html", controllo=2, listaclienti=lista)
                elif strdelete in request.form:
                    targhe = Mezzi.query.filter_by(cfcliente=i.cf).all()
                    for x in targhe:
                        Riparazioni.query.filter_by(targamezzo=x.targa).delete()
                    Mezzi.query.filter_by(cfcliente=i.cf).delete()
                    Clienti.query.filter_by(cf=i.cf).delete()
                    db.session.commit()
                    lista = Clienti.query.all()
                    return render_template("gestionale.html", controllo=2, listaclienti=lista)
            return render_template("gestionale.html")

        else:
            return render_template("gestionale.html")
    else:
        return redirect(url_for("home"))

#Pagina per l'aggiunta riparazioni
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

#Pagina per l'aggiunta clienti
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

#Pagina per l'aggiunta mezzi
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
            if cfcliente=="Aggiungi CF":
                return redirect(url_for("aggiuntaclienti"))
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
    #Creazione tabelle Database e Avvio dell'applicazione
    db.create_all()
    app.run(debug = True)
