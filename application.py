import json

from flask import Flask, render_template, url_for, session, request, redirect
from flask_session import Session
from conf import DATABASE
import psycopg2
from psycopg2 import extras
from flask_bcrypt import Bcrypt


app = Flask(__name__, template_folder="templates")

app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = '94jf9j38fj934kf340fk495jf93j94fj39jf03'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

bcrypt = Bcrypt()

def connect_db():
	connection = psycopg2.connect(
		host=DATABASE['host'],
		database=DATABASE['database'],
		user=DATABASE['user'],
		password=DATABASE['password']
	)
	return connection


# def select():
# 	command = 'SELECT %s FROM %s'

@app.route('/logout')
def logout():
	# session['auth'] = None
	session.clear()
	return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login():
	#TODO добавить флеши сообщения если что-то не введено
	if request.method == 'POST':
		login = request.form.get('login')
		password = request.form.get('password')

		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT * FROM user_site WHERE user_name=%s', (login,))
		user = cur.fetchone()
		print()
		print(password)
		if user and bcrypt.check_password_hash(user['password'], password):
			session['auth'] = True
			cur.close()
			con.close()
			return redirect('main')
		cur.close()
		con.close()
	return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
	# TODO: сделать вывод ошибки если user существует
	# TODO: сделать signup всплывающим окном
	if request.method == 'POST':
		login = request.form.get('login')
		password1 = request.form.get('password1')
		password2 = request.form.get('password2')

		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		cur.execute('SELECT * FROM user_site WHERE user_name=%s', (login,))
		user = cur.fetchall()
		print(user)
		if not user and password1 == password2:
			pw_hash = bcrypt.generate_password_hash(password1).decode('utf8')
			cur.execute('INSERT INTO user_site (email, user_name, password) VALUES (%s, %s, %s)', ('email', login, pw_hash))
			session['login'] = login
			session['auth'] = True
			con.commit()
			cur.close()
			con.close()
			return redirect('main')
		cur.close()
		con.close()
	return render_template('signup.html')


@app.route('/user')
def user():
	if 'login' in session and session['auth']:
		return render_template('user.html')
	return redirect('signup')

# @app.route('/logout')
# def logout():
# 	session['auth'] = False
# 	return render_template()


@app.route('/add_recipe')
def add_recipe():
	return render_template('add_recipe.html')

@app.route('/')
@app.route('/main')
def main():
	""" Вывод всех рецептов
	Сортировка(по времени готовки, по типу рецепта, ВОЗМОЖНО ПО ЦЕНЕ)
	Поиск по названиям
	"""

	con = connect_db()
	cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
	cur.execute('SELECT * FROM recipe')
	recipes = cur.fetchall()
	cur.close()
	con.close()
	return render_template('main.html', recipes=recipes)


if __name__ == '__main__':
	app.run(host='127.0.0.1', port=5000, debug=True)
