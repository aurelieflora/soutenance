from flask import Flask, flash, get_flashed_messages, render_template, request, redirect, session, url_for
import mysql.connector
from werkzeug.utils import secure_filename
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "votre_clé_secrète"


# CONFIGURATION ET CONNEXION A LA BASE DE DONNEE
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    db="reference"
)

# Configurer le dossier d'upload
UPLOAD_FOLDER = './static/upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(
    ['jpg', 'jpeg' 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'png', 'webp'])


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# LA PAGE D'ACCUEIL
@app.route("/")
def accueil():
    return render_template("accueil.html")

# LA PAGE A PROPOS DE NOUS


@app.route("/a_propos_de_nous")
def a_propos_de_nous():
    return render_template("a_propos_de_nous.html")

# LA PAGE DES PROFFESIONNELS


@app.route('/professionnels')
def professionnels():
    cursor = mydb.cursor()
    service = request.args.get('service')
    ville = request.args.get('ville')
    print("Service:", service)
    print("Ville:", ville)
    if service and ville:
        cursor.execute(
            "SELECT * FROM professionnel WHERE service=%s AND ville=%s ORDER BY id_professionnel DESC", (service, ville))
    elif service:
        cursor.execute(
            "SELECT * FROM professionnel WHERE service=%s ORDER BY id_professionnel DESC", (service,))
    elif ville:
        cursor.execute(
            "SELECT * FROM professionnel WHERE ville=%s ORDER BY id_professionnel DESC", (ville,))
    else:
        cursor.execute(
            "SELECT * FROM professionnel ORDER BY id_professionnel DESC")

    data = cursor.fetchall()
    print("Nombre de professionnels trouvés:", len(data))
    grouped_data = [data[i:i+6] for i in range(0, len(data), 6)]
    print("Grouped data:", grouped_data)
    return render_template('professionnels.html', grouped_data=grouped_data)


# LA PAGE DE CONTACT
@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

# RECHERCHERCHE DE PROFIL


@app.route("/recherche")
def recherche():
    return render_template("recherche.html")

# LA PAGE DE RESERVATION
# @app.route("/profil")
# def profil():
#     return render_template("profil.html")

# LA PAGE DE PAIEMENT


@app.route("/paiement")
def paiement():
    return render_template("paiement.html")

# LA PAGE DE CHAT


@app.route("/chat")
def chat():
    return render_template("chat.html")


# LA PAGE D'INSCRIPTION DU PROFESSIONNEL

@app.route("/ajouter_services", methods=['GET', 'POST'])
def ajouter_services():
    if request.method == 'POST':
        # Récupération des données du formulaire
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        ville = request.form.get('ville')
        service = request.form.get('service')
        photo = request.files.get('photo')
        mot_de_passe = request.form.get('mot_de_passe')
        confirm_password = request.form.get('confirm-password')

        # Vérification de la correspondance des mots de passe
        if mot_de_passe != confirm_password:
            flash("Les mots de passe ne correspondent pas")
            return redirect(url_for('ajouter_services'))

        # Vérification du type de fichier
        if not allowed_file(photo.filename):
            flash("Type de fichier non autorisé. Seuls les fichiers 'jpg', 'jpeg','pjpeg', 'pjp', 'png', 'webp' sont autorisés.")
            return redirect(url_for('ajouter_services'))

        # Vérification de l'existence de l'email dans la base de données
        cursor = mydb.cursor()
        sql = "SELECT * FROM professionnel WHERE email = %s"
        cursor.execute(sql, (email,))
        utilisateur = cursor.fetchone()
        if utilisateur:
            # L'email existe déjà dans la base de données, afficher un message d'erreur
            flash("L'adresse e-mail existe déjà dans la base de données.")
            return redirect(url_for('ajouter_services'))

        # Sécurisation du nom de fichier de la photo
        filename = secure_filename(photo.filename)

        # Génération du hash du mot de passe
        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        # Enregistrement de la photo sur le serveur
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Insertion des données dans la base de données
        cursor = mydb.cursor()
        sql = "INSERT INTO professionnel (nom, prenom, email, telephone, ville, service, photo, mot_de_passe) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (nom, prenom, email, telephone,
                    ville, service, filename, mot_de_passe_hash))
        mydb.commit()

        # Message de succès et redirection vers la page d'accueil
        flash("Le profil a été ajouté avec succès")
        return redirect(url_for('accueil'))

    # Affichage du formulaire pour l'ajout de profil
    return render_template("ajouter_services.html")

# LA PAGE DE CONNEXION DU PROFESSIONEL


@app.route("/connexion_service", methods=['GET', 'POST'])
def connexion_service():
    if request.method == 'POST':
        # Récupération des données du formulaire
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        mot_de_passe_hache = generate_password_hash(mot_de_passe)

        # Récupération de l'utilisateur depuis la base de données
        cursor = mydb.cursor()
        # sql = "SELECT * FROM professionnel WHERE email = %s"
        sql = ("SELECT * FROM professionnel WHERE email = %s AND mot_de_passe = %s")

        cursor.execute(sql, (email, mot_de_passe_hache))
        utilisateur = cursor.fetchone()

        if utilisateur:
            session['utilisateur_id'] = utilisateur['id_professionnel']
        flash('Connexion réussie !', 'success')
        return redirect(url_for('professionnels'))

    else:
        flash('Adresse e-mail ou mot de passe incorrect.', 'error')

        # Récupération des messages flash de la session
    messages = get_flashed_messages()

    # Affichage de la page de connexion avec les messages flash
    return render_template("connexion_service.html", messages=messages)


# LA PAGE DE DECONNEXION
@app.route("/deconnexion")
def deconnexion():
    # Suppression de l'utilisateur de la session
    session.pop('utilisateur', None)
    return redirect(url_for('accueil'))


# LA PAGE D'INSCRIPTION DE L'UTILISATEUR


@app.route('/inscription_utilisateur', methods=['GET', 'POST'])
def inscription_utilisateur():
    if request.method == 'POST':
        nom_prenoms = request.form['nom_prenoms']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        confirmation_mot_de_passe = request.form['confirmation_mot_de_passe']

        # Vérifier si le mot de passe et sa confirmation correspondent
        if mot_de_passe != confirmation_mot_de_passe:
            flash("Les mots de passe ne correspondent pas.")
            return redirect(url_for('inscription_utilisateur'))

        # Hachage du mot de passe
        mot_de_passe = generate_password_hash(mot_de_passe)

        # Insérer les données de l'utilisateur dans la base de données
        cursor = mydb.cursor()
        query = "INSERT INTO utilisateur (nom_prenoms, email, mot_de_passe) VALUES (%s, %s, %s)"
        values = (nom_prenoms, email, mot_de_passe)
        cursor.execute(query, values)
        mydb.commit()
        flash("Vous êtes inscrit avec succès.")
        return redirect(url_for('connexion_utilisateur'))
    return render_template('inscription_utilisateur.html')


@app.route('/connexion_utilisateur', methods=['GET', 'POST'])
def connexion_utilisateur():
    if request.method == 'POST':
        # Récupération des données du formulaire
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')
        mot_de_passe_hache = generate_password_hash(mot_de_passe)

        # Récupération de l'utilisateur depuis la base de données

        cursor = mydb.cursor()
        # sql = "SELECT * FROM professionnel WHERE email = %s"
        sql = ("SELECT * FROM utilisateur WHERE email = %s AND mot_de_passe = %s")

        cursor.execute(sql, (email, mot_de_passe_hache))
        utilisateur = cursor.fetchone()

        if utilisateur:
            session['utilisateur_id'] = utilisateur['id_utilisateur']
        flash('Connexion réussie !', 'success')
        return redirect(url_for('professionnels'))

    else:
        flash('Adresse e-mail ou mot de passe incorrect.', 'error')

        # Récupération des messages flash de la session
    messages = get_flashed_messages()

    # Affichage de la page de connexion avec les messages flash
    return render_template("connexion_utilisateur.html", messages=messages)


# PROFIL PROFESSIONNEL

@app.route('/profil/<int:id>')
def profil(id):
    # Récupération des éléments de la base de données correspondants à l'ID
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    db="reference"
)
    cursor = mydb.cursor()
    sql = "SELECT * FROM professionnel WHERE id_professionnel=%s"
    cursor.execute(sql, (id,))
    professionnel = cursor.fetchone()

    # Fermeture de la connexion
    cursor.close()
    mydb.close()

    # Affichage des éléments sur la page profil.html
    return render_template("profil.html", professionnel=professionnel)


if __name__ == '__main__':
    app.run(debug=True)
