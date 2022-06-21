from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify
from App import app
import psycopg2
import psycopg2.extras
import re
import werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
from App.memes import get_urls_jbzd, get_urls_kwejk
from datetime import date, datetime
import random
import os
from argparse import Namespace
from flask_login import LoginManager, FlaskLoginClient, login_user, logout_user, current_user, login_required
import json
from flask_mail import Mail, Message



def get_db_connection():
    conn = psycopg2.connect(host='flask-server.postgres.database.azure.com',
                            database='db',
                            user='hrtrex',
                            password='Jebacdisa_12',
                            sslmode='require')
    return conn



@app.route("/memesRanking")
def getMemesSortedByRatings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('select id_mema,tytul,kategoria,CAST(avg(jaka_ocena) as NUMERIC(10,1)) srednia from oceny_memow,memy where memy.id_mema=oceny_memow.Memy_id_mema group by id_mema having avg(jaka_ocena) is not null order by srednia desc;')
    memy = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('memesRanking.html', memy=memy)




@app.route("/")
def home():
    if 'loggedin' in session:
        return render_template('index.html', email=session['email'])
    return render_template("index.html")

@app.route("/<name>")
def user(name):
    return render_template("index.html")

@app.route("/admin")
def admin():
    return redirect(url_for("home"))

@app.route("/jbzd/", defaults={'page': ''})
@app.route("/jbzd/<page>")
def jbzd(page):
    urls, votes = get_urls_jbzd(page)
    data = list(zip(urls, votes))
    return render_template("memy.html", links=data)

@app.route("/kwejk/", defaults={'page': ''})
@app.route("/kwejk/<page>")
def kwejk(page):
    urls, votes = get_urls_kwejk(page)
    data = list(zip(urls, votes))
    return render_template("memy.html", links=data)







#REJESTRACJA
@app.route('/register', methods = ['POST', 'GET'])
def register():
    return render_template('register.html')


@app.route('/userPanel', methods = ['POST', 'GET'])
def userP():
   
    
    password = 0
    password2 = 0
    email = 0

    
    if request.method == 'POST':
        register_data = request.form
        n = Namespace(**register_data)
        user_role_test = 0
        if n.login == 'admin':
            user_role_test = 2
        else:
            user_role_test = 1

    
        if n.password != n.password2:
            return f'Wrong password confirmation'

        

        join = date.today()
        hashed_password = generate_password_hash(n.password)

        login = n.login
        password = hashed_password
        email = n.email
        user_role = user_role_test
        joined = join
        
        

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from uzytkownicy')
        cur.execute("""
        INSERT INTO uzytkownicy (login, haslo, email, typ_uzytkownika, data_dolaczenia)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (login, password, email, user_role, joined))
        
        conn.commit()
        cur.close()
        conn.close()

        return render_template('userPanel.html',register_data = register_data, n=n, user_role = user_role, joined=joined)

    if request.method == 'GET':
        return f"FATAL ERROR"


          
#LOGOWANIE

app.secret_key = 'ashdasuidjnascmioajouwenawicnjkac'

@app.route("/profile")
def profile():

        conn = get_db_connection()
        cur = conn.cursor()
        
        global email
        
        
        cur.execute('SELECT * FROM uzytkownicy WHERE email = %s', (email,));
        account = cur.fetchone()

        login = account[1]
        email = account[3]
        user_role = account[4]
        joined = account[5]

        cur.close()
        conn.close()

        return render_template("profile.html",account=account,login=login,email=email,user_role=user_role,joined=joined)



@app.route('/login', methods=['GET', 'POST'])
def login():
    
    

    conn = get_db_connection()
    cur = conn.cursor()



   
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        global email
        email = request.form['email']
        password = request.form['password']
 
        
        cur.execute('SELECT * FROM uzytkownicy WHERE email = %s', (email,));
        account = cur.fetchone()
        
        
        
        
 
        if account:
            
            password_ch = account[2]
            if check_password_hash(password_ch, password):
                
                session['loggedin'] = True
                session['id'] = account[0]
                session['email'] = account[3]
                
                return render_template("index.html",email=email)

                
                
            else:
                flash('Incorrect email or password')
        else:
            flash('Incorrect email or password')
   
    return render_template('login.html')


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)

   return redirect(url_for('login'))


#RESET HASLA
@app.route('/passwordReset', methods=['GET', 'POST'])
def resetP():

    conn = get_db_connection()
    cur = conn.cursor()


    if request.method == 'POST' and 'email' in request.form and 'old_password' in request.form and 'new_password' in request.form and 'new_password2' in request.form:
        
        email = request.form['email']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        new_password2 = request.form['new_password2']

        if new_password != new_password2:
            return f"Wrong new password confirmation"


        cur.execute('SELECT * FROM uzytkownicy WHERE email = %s', (email,));
        account = cur.fetchone()
        
        password_test = account[2]
        email_test = account[3]
        hashed_password = generate_password_hash(new_password)
        
        sql = """ UPDATE uzytkownicy
                SET haslo = %s
                WHERE email = %s"""

        if check_password_hash(password_test, old_password):
            cur.execute(sql, (hashed_password, email_test))
        else:
            return f"Wrong old password"


        conn.commit()
        cur.close()
        conn.close()  


    return render_template('passwordReset.html')


#ZMIANA EMAILA
@app.route('/emailReset', methods=['GET', 'POST'])
def emailReset():

    conn = get_db_connection()
    cur = conn.cursor()


    if request.method == 'POST' and 'email' in request.form and 'new_email' in request.form and 'new_email2' in request.form:
        
        email = request.form['email']
        new_email = request.form['new_email']
        new_email2 = request.form['new_email2']

      
        cur.execute('SELECT * FROM uzytkownicy WHERE email = %s', (email,));
        account = cur.fetchone()
        
        test_id = account[0]
        email_test = account[3]
        
        sql = """ UPDATE uzytkownicy
                SET email = %s
                WHERE id_uzytkownika = %s"""

        if new_email == new_email2:
            cur.execute(sql, (new_email, test_id))
        else:
            return f"Wrong new email confirmation"


        conn.commit()
        cur.close()
        conn.close()  


    return render_template('emailReset.html')




#EMAIL VERYFICATION
@app.route('/emailCheck', methods=['GET', 'POST'])
def emailcheck():

    conn = get_db_connection()
    cur = conn.cursor()



    if request.method == 'POST' and 'server' in request.form and 'email' in request.form:
        
        server = request.form['server']
        
        email = request.form['email']
        
        

        cur.execute('SELECT * FROM uzytkownicy WHERE email = %s', (email,));
        account = cur.fetchone()

        password_testing = account[2]

        

        app.config['MAIL_SERVER']= server
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USERNAME'] = 'e51fed28a86eac'
        app.config['MAIL_PASSWORD'] = '50d9261ab4b694'
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        mail = Mail(app)
       
        msg = Message('Password recovery', sender =   'usmiechnij_sie_webapp@gmail.com', recipients = [email])
        msg.body = "Hello. Don't forget your password next time :) Your password is: %s" % password_testing
        mail.send(msg)
        return render_template('login.html')

    return render_template('emailCheck.html')

