#importazione dei pacchetti necessari
from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, send_from_directory
from datetime import timedelta, datetime
import pytz
from flask_sqlalchemy import SQLAlchemy
import time
import smtplib, ssl
from email.message import EmailMessage
from flask_mail import Mail, Message as MailMessage
from pathlib import Path
from fpdf import FPDF, HTMLMixin
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
class MyPDF(FPDF, HTMLMixin):
    pass

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
    inizio = db.Column("inizio", db.String(30))
    fine = db.Column("fine", db.String(30))
    prezzo = db.Column("prezzo", db.String(10))
    descrizione = db.Column("descrizione", db.String(50))
    targamezzo = db.Column("targamezzo", db.String(20), db.ForeignKey('mezzi.targa'), nullable=False)

    def __init__(self, inizio, fine, prezzo, descrizione, targamezzo):
        self.inizio = inizio
        self.fine = fine
        self.prezzo = prezzo
        self.descrizione = descrizione
        self.targamezzo = targamezzo

def inviamail(ricevente):
    msg = MailMessage('NoReply - Officina', sender='assistenza.mechsite@gmail.com', recipients=[ricevente.email])
    msg.body = "Buongiorno, \n la riparazione sul mezzo: " + ricevente.marca + " " + ricevente.modello + ", a nome: " + ricevente.nome + " " + ricevente.cognome + " è terminata.\nPrezzo Finale: " + ricevente.prezzo + "\nSaluti, MechSite"
    with app.open_resource("/var/www/webApp/webApp/static/blank.pdf") as fp:
        msg.attach("Resoconto.pdf", "application/pdf", fp.read())
    mail.send(msg)
    return 1

def addlog(str):
    tz = pytz.timezone("Europe/Rome")
    stringa = datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + " " + str
    file = open("/var/www/webApp/webApp/static/log.txt", "a")
    file.write(stringa)

@app.route('/static/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    # Appending app path to upload folder path within app root folder
    #uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    # Returning file from appended path
    #return send_from_directory(directory=uploads, filename=filename, as_attachment=True)
    stringa = "/var/www/webApp/webApp/static/" + "blank.pdf"
    return send_file(stringa, as_attachment=True)

def generapdf(ricevente):
    html = """
    <html>
    <head>
    <meta charset="utf-8">
    </head>
    <body>
    <center>
    <p>Riparazione Conclusa</p>
    <p>Buongiorno, <br>La informiamo della conclusione della riparazione sul mezzo """+ ricevente.marca +""" """ +ricevente.modello +""" a nome: """ + ricevente.nome + """ """ + ricevente.cognome+""" </p>
    <br>
    <p>Descrizione della riparazione: """ + ricevente.descrizione + """.</p>
    <br>
    <p>Informazioni sul mezzo:</p>
    <br>
    <table width="100%">
        <tr width="100%">
            <th width="25%">Veicolo</th>
            <th width="25%">Targa</th>
            <th width="25%">Cilindrata</th>
            <th width="25%">Potenza</th>
        </tr>
        <tr width="100%">
            <td width="25%">""" + ricevente.marca + """ """ + ricevente.modello + """</td>
            <td width="25%">""" + ricevente.targa + """</td>
            <td width="25%">""" + ricevente.cilindrata + """ cc</td>
            <td width="25%">""" + ricevente.potenza + """ CV</td>
        </tr>
    </table>
    <br>
    <p>Prezzo Finale: """ + ricevente.prezzo + """ euro.</p>
    <br>
    <p>Saluti, MechSite.</p>
    </center>
    </body>
    </html>
    """
    pdf = MyPDF()
    pdf.add_page()
    pdf.write_html(html)
    pdf.output("/var/www/webApp/webApp/static/blank.pdf", "F")

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
            frase="Email non Trovata"
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
                    return render_template("passwordclienti.html", controllo=1, frase="Password Errata")
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
                if (len(riparazioniincorso)==0):
                    return render_template("riparazioniclienti.html", controllo=0, frase="Nessun Record Trovato")
                return render_template("riparazioniclienti.html", controllo=0, listariparazioni=riparazioniincorso, frase="")
            elif request.form["scelta"]=="In corso":
                riparazioniincorso = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni.fine, Mezzi.marca, Mezzi.modello, Mezzi.targa).filter_by(email=session["cliente"]).all()
                if (len(riparazioniincorso)==0):
                    return render_template("riparazioniclienti.html", controllo=1, frase="Nessun Record Trovato")
                return render_template("riparazioniclienti.html", controllo=1, listariparazioni=riparazioniincorso, frase="")
            elif request.form["scelta"]=="Terminate":
                riparazioniincorso = Riparazioni.query.join(Mezzi, Riparazioni.targamezzo==Mezzi.targa).join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni.fine, Mezzi.marca, Mezzi.modello, Mezzi.targa).filter_by(email=session["cliente"]).all()
                if (len(riparazioniincorso)==0):
                    return render_template("riparazioniclienti.html", controllo=2, frase="Nessun Record Trovato")
                return render_template("riparazioniclienti.html", controllo=2, listariparazioni=riparazioniincorso, frase="")
        else:
            return render_template("riparazioniclienti.html", frase="")
    else:
        return redirect(url_for("accessoclienti"))

@app.route("/mezziclienti")
def mezziclienti():
    if "cliente" in session and "passcliente" in session:
        mezzicliente = Mezzi.query.join(Clienti, Mezzi.cfcliente==Clienti.cf).add_columns(Mezzi.targa, Mezzi.marca, Mezzi.modello, Mezzi.cilindrata, Mezzi.potenza).filter_by(email=session["cliente"]).all()
        if (len(mezzicliente)==0):
            return render_template("mezziclienti.html", frase="Non hai nessun Mezzo registrato")
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
            frase=""
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            email=request.form["email"]
            ntelefono = request.form["ntelefono"]
            if request.form["password"]==request.form["passwordrepeat"] and request.form["password"]!="":
                password=request.form["password"]
                clientein.password=password
                frase += "Password modificata "
            elif request.form["password"]!="":
                frase="Le due password non coincidono"
            if clientein.email != email:
                clientein.email = email
                frase += "Email modificata  "
                session["cliente"]=email
            if clientein.ntelefono != ntelefono:
                clientein.ntelefono = ntelefono
                frase += "Numero di Telefono modificato"
            db.session.commit()
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            return render_template("modificaprofilocliente.html", cliente=clientein, frase=frase)
        else:
            clientein = Clienti.query.filter_by(email=session["cliente"]).first()
            return render_template("modificaprofilocliente.html", cliente=clientein, frase="")
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
            frase="Password Errata"
            return render_template("index.html", frase=frase)
    else:
        return render_template("index.html", frase="")

#Pagina Riparazioni in corso...
@app.route("/riparazioni", methods=["GET", "POST"])
def riparazioni():
    if "pass" in session:
        frase=""
        tz = pytz.timezone("Europe/Rome")
        riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
        if request.method == "POST":
            #Cerca le riparazioni in corso per poi printarle nella pagina
            ids = Riparazioni.query.filter_by(fine="in corso...").all()
            for i in ids:
                if str(i._id) in request.form:
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    ricevente = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns( Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.email, Clienti.nome, Clienti.cognome, Riparazioni.prezzo, Riparazioni.descrizione, Mezzi.cilindrata, Mezzi.potenza, Mezzi.targa).filter_by(_id=i._id).first()
                    riparazione.fine=datetime.now(tz)
                    db.session.commit()
                    generapdf(ricevente)
                    n = inviamail(ricevente)
                    break
            riparazioniincorso = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns(Riparazioni.inizio, Riparazioni.descrizione, Riparazioni.prezzo, Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.nome, Clienti.cognome).filter_by(fine="in corso...").all()
            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso, frase="")
        else:
            if len(riparazioniincorso)==0:
                frase = "Nessuna riparazione in corso"
            return render_template("riparazioni.html", listariparazioniincorso=riparazioniincorso, frase=frase)
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
                if (len(lista)==0 and len(lista2)==0):
                    return render_template("storico.html", controllo=1, listariparazioni=lista2, listamacchine=lista, frase="Nessun Record Trovato")
                else:
                    return render_template("storico.html", controllo=1, listariparazioni=lista2, listamacchine=lista, frase="")
            elif scelta=="Targa":
                #ricerca Riparazioni e Proprietario associati alla Targa inserita
                targain=request.form["ricerca"]
                lista=Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).filter_by(targa=targain).all()
                lista2 = Riparazioni.query.filter_by(targamezzo=targain).all()
                if (len(lista)==0 and len(lista2)==0):
                    return render_template("storico.html", controllo=2, listariparazioni=lista2, listaproprietari=lista, frase="Nessun Record Trovato")
                else:
                    return render_template("storico.html", controllo=2, listariparazioni=lista2, listaproprietari=lista, frase="")
            else:
                return render_template("storico.html", frase="Nessun Record Trovato")
        else:
            #se non viene selezionata un'opzione vengono printati tutte le riparazione, clienti, mezzi, no andrebbe nell'else qua sopra, gg alde
            lista1 = Clienti.query.all()
            lista2 = Mezzi.query.all()
            lista3 = Riparazioni.query.all()
            return render_template("storico.html", controllo=0, listariparazioni=lista3, listamezzi=lista2, listaclienti=lista1, frase="")
    else:
        return redirect(url_for("home"))

#Pagina Gestionale del Database
@app.route("/gestionale", methods=["GET", "POST"])
def gestionale():
    if "pass" in session:
        tz = pytz.timezone("Europe/Rome")
        if request.method=="POST":
            frase=""
            if "scelta" in request.form:
                frase=""
                scelta = request.form["scelta"]
                #In base alla scelta viene printato una tabella differente
                if scelta=="Riparazioni":
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessuna Riparazione Trovata"
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista, frase=frase)
                elif scelta=="Mezzi":
                    lista = Mezzi.query.all()
                    if len(lista)==0:
                        frase="Nessun Mezzo Trovato"
                    return render_template("gestionale.html", controllo=1, listamezzi=lista, frase=frase)
                elif scelta=="Clienti":
                    lista = Clienti.query.all()
                    if len(lista)==0:
                        frase="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=2, listaclienti=lista, frase=frase)
                elif scelta=="Completo":
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessuna Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)
            ids = Riparazioni.query.all()
            for i in ids:
                strdelete = str(i._id) + "delete"
                strcompleto = str(i._id) + "3"
                if str(i._id) in request.form:
                    #Codice per la modifica degli attributi delle Riparazioni
                    riparazione = Riparazioni.query.filter_by(_id=i._id).first()
                    var = str(i._id)
                    if request.form[var + "stato"]=="In corso":
                        riparazione.fine = "in corso..."
                    elif request.form[var + "stato"]=="Terminato":
                        riparazione.fine = datetime.now(tz)
                        ricevente = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns( Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.email, Clienti.nome, Clienti.cognome, Riparazioni.prezzo, Mezzi.targa).filter_by(_id=i._id).first()
                        n = inviamail(ricevente)
                    riparazione.descrizione=request.form[var + "descrizione"]
                    riparazione.prezzo=request.form[var + "prezzo"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista, frase="")
                elif strdelete in request.form:
                    Riparazioni.query.filter_by(_id=i._id).delete()
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessuna Riparazione Trovata"
                    return render_template("gestionale.html", controllo=0, listariparazioni=lista, frase=frase)
                elif strcompleto in request.form:
                    id=strcompleto[:-1]
                    riparazione = Riparazioni.query.filter_by(_id=id).first()
                    if request.form[id + "stato3"]=="In corso":
                        riparazione.fine = "in corso..."
                    elif request.form[id + "stato3"]=="Terminato":
                        riparazione.fine = datetime.now(tz)
                        ricevente = Clienti.query.join(Mezzi, Clienti.cf==Mezzi.cfcliente).join(Riparazioni, Mezzi.targa==Riparazioni.targamezzo).add_columns( Riparazioni._id, Mezzi.marca, Mezzi.modello, Clienti.email, Clienti.nome, Clienti.cognome, Riparazioni.prezzo).filter_by(_id=id).first()
                        n = inviamail(ricevente)
                    riparazione.descrizione=request.form[id + "descrizione3"]
                    riparazione.prezzo=request.form[id + "prezzo3"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    lista1 = Mezzi.query.all()
                    lista2 = Clienti.query.all()
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase="")
                elif strdelete+"3" in request.form:
                    Riparazioni.query.filter_by(_id=i._id).delete()
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessuna Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)

            targhe = Mezzi.query.all()
            for i in targhe:
                strdelete = str(i.targa) + "delete"
                strcompleto = str(i.targa) + "3"
                if str(i.targa) in request.form:
                    mezzo = Mezzi.query.filter_by(targa=i.targa).first()
                    mezzo.marca = request.form[i.targa + "marca"]
                    mezzo.modello = request.form[i.targa + "modello"]
                    mezzo.cilindrata = request.form[i.targa + "cilindrata"]
                    mezzo.potenza = request.form[i.targa + "potenza"]
                    db.session.commit()
                    lista = Mezzi.query.all()
                    return render_template("gestionale.html", controllo=1, listamezzi=lista, frase="")
                elif strdelete in request.form:
                    Riparazioni.query.filter_by(targamezzo=i.targa).delete()
                    Mezzi.query.filter_by(targa=i.targa).delete()
                    db.session.commit()
                    lista = Mezzi.query.all()
                    if len(lista)==0:
                        frase="Nessun Mezzo Trovato"
                    return render_template("gestionale.html", controllo=1, listamezzi=lista, frase=frase)
                elif strcompleto in request.form:
                    targain = strcompleto[:-1]
                    mezzo = Mezzi.query.filter_by(targa=targain).first()
                    mezzo.marca = request.form[targain + "marca3"]
                    mezzo.modello = request.form[targain + "modello3"]
                    mezzo.cilindrata = request.form[targain + "cilindrata3"]
                    mezzo.potenza = request.form[targain + "potenza3"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessun Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)
                elif strdelete+"3" in request.form:
                    Riparazioni.query.filter_by(targamezzo=i.targa).delete()
                    Mezzi.query.filter_by(targa=i.targa).delete()
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessun Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)

            cfs = Clienti.query.all()
            for i in cfs:
                strdelete = str(i.cf) + "delete"
                strcompleto = str(i.cf) + "3"
                if str(i.cf) in request.form:
                    cliente = Clienti.query.filter_by(cf=i.cf).first()
                    cliente.nome = request.form[str(i.cf) + "nome"]
                    cliente.cognome = request.form[str(i.cf) + "cognome"]
                    cliente.ntelefono = request.form[str(i.cf) + "ntelefono"]
                    cliente.email = request.form[str(i.cf) + "email"]
                    db.session.commit()
                    lista = Clienti.query.all()
                    return render_template("gestionale.html", controllo=2, listaclienti=lista, frase="")
                elif strdelete in request.form:
                    targhe = Mezzi.query.filter_by(cfcliente=i.cf).all()
                    for x in targhe:
                        Riparazioni.query.filter_by(targamezzo=x.targa).delete()
                    Mezzi.query.filter_by(cfcliente=i.cf).delete()
                    Clienti.query.filter_by(cf=i.cf).delete()
                    db.session.commit()
                    lista = Clienti.query.all()
                    if len(lista)==0:
                        frase="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=2, listaclienti=lista, frase=frase)
                elif strcompleto in request.form:
                    cfin = strcompleto[:-1]
                    cliente = Clienti.query.filter_by(cf=cfin).first()
                    cliente.nome = request.form[cfin + "nome3"]
                    cliente.cognome = request.form[cfin + "cognome3"]
                    cliente.ntelefono = request.form[cfin + "ntelefono3"]
                    cliente.email = request.form[cfin + "email3"]
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessun Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)
                elif strdelete + "3" in request.form:
                    targhe = Mezzi.query.filter_by(cfcliente=i.cf).all()
                    for x in targhe:
                        Riparazioni.query.filter_by(targamezzo=x.targa).delete()
                    Mezzi.query.filter_by(cfcliente=i.cf).delete()
                    Clienti.query.filter_by(cf=i.cf).delete()
                    db.session.commit()
                    lista = Riparazioni.query.all()
                    if len(lista)==0:
                        frase="Nessun Riparazione Trovata"
                    lista1 = Mezzi.query.all()
                    if len(lista1)==0:
                        frase+="Nessun Mezzo Trovato"
                    lista2 = Clienti.query.all()
                    if len(lista2)==0:
                        frase+="Nessun Cliente Trovato"
                    return render_template("gestionale.html", controllo=3, listariparazioni=lista, listamezzi=lista1, listaclienti=lista2, frase=frase)
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
            inizio = datetime.now(tz)
            fine = "in corso..."
            prezzo = request.form["prezzo"]
            descrizione = request.form["descrizione"]
            targamezzo = request.form["targamezzo"]
            riparazione = Riparazioni(inizio, fine, prezzo, descrizione, targamezzo)
            db.session.add(riparazione)
            db.session.commit()
            return render_template("addriparazioni.html", lista=listamezzi, frase="Nuova Riparazione Aggiunta")
        else:
            return render_template("addriparazioni.html", lista=listamezzi, frase="")
    else:
        return redirect(url_for("home"))

#Pagina per l'aggiunta clienti
@app.route("/aggiuntaclienti", methods=["GET", "POST"])
def aggiuntaclienti():
    if "pass" in session:
        if request.method == "POST":
            cf = request.form["cf"]
            cf = cf.upper()
            nome = request.form["nome"]
            cognome = request.form["cognome"]
            ntelefono = request.form["ntelefono"]
            email = request.form["email"]
            password = None
            check_cliente = Clienti.query.filter_by(cf=cf).first()
            if check_cliente:
                return render_template("addclienti.html", frase="E' già presente un cliente con questo CF")
            else:
                cliente = Clienti(cf, nome, cognome, ntelefono, email, password)
                db.session.add(cliente)
                db.session.commit()
                addlog("Aggiunto un Cliente")
                return render_template("addclienti.html", frase="Nuovo Cliente Aggiunto")
        else:
            return render_template("addclienti.html", frase="")
    else:
        return redirect(url_for("home"))

#Pagina per l'aggiunta mezzi
@app.route("/aggiuntamezzi", methods=["GET", "POST"])
def aggiuntamezzi():
    if "pass" in session:
        listaclienti = Clienti.query.all()
        if request.method == "POST":
            targa = request.form["targa"]
            targa = targa.upper()
            marca = request.form["marca"]
            modello = request.form["modello"]
            cilindrata = request.form["cilindrata"]
            potenza = request.form["potenza"]
            cfcliente = request.form["cfcliente"]
            if cfcliente=="Aggiungi CF":
                return redirect(url_for("aggiuntaclienti"))
            check_mezzo = Mezzi.query.filter_by(targa=targa).first()
            if check_mezzo:
                return render_template("addmezzi.html", lista=listaclienti, frase="E' già presente un mezzo con questa Targa")
            else:
                mezzo = Mezzi(targa, marca, modello, cilindrata, potenza, cfcliente)
                db.session.add(mezzo)
                db.session.commit()
                return render_template("addmezzi.html", lista=listaclienti, frase="Nuovo Mezzo Aggiunto")
        else:

            return render_template("addmezzi.html", lista=listaclienti, frase="")
    else:
        return redirect(url_for("home"))

if __name__ == "__main__":
    #Creazione tabelle Database e Avvio dell'applicazione
    db.create_all()
    app.run(debug = True)
