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
		# Берем из формы логин и пароль
		login = request.form.get('login')
		password = request.form.get('password')

		# соединение с БД
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		# запрос в БД
		cur.execute('SELECT * FROM user_site WHERE user_name=%s', (login,))
		user = cur.fetchone()
		print()
		print(password)
		# если пользователь есть в БД и пароль совпадает,
		# в сессии указываем, что пользователь авторизован,
		# закрываем соединение с БД и переходим на главную страницу
		if user and bcrypt.check_password_hash(user['password'], password):
			session['auth'] = True
			cur.close()
			con.close()
			return redirect('main')
		# Если пользователя нет в БД или пароль не совпадает,
		# оставляем на той же странице и предупреждаем что авторизация не удалась
		# TODO сделать сообщение, что вход не удался
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
	#TODO доделать user и улучшить проверку по sessions(до конца понять детали)
	if 'login' in session and session['auth']:
		return render_template('user.html')
	return redirect('signup')

# @app.route('/logout')
# def logout():
# 	session['auth'] = False
# 	return render_template()


@app.route('/add_recipe', methods=['POST', 'GET'])
def add_recipe():
	if not session.get('auth'):
		return redirect('signup')
	elif request.method == 'POST':
		#TODO отправка форм в бд
		#TODO название не должно быть пустым
		#TODO минуты тоже не ложны быть пустыми

		#TODO сначала заполняем в БД рецепт, потом ингредиенты,
		# потом просматриваем request.files на наличие фото и с этими фото заполняем
		# шаги. Если все ок отправляем на страницу модерации
		name_recipe = request.form.get('name_recipe')
		addition = request.form.get('addition')
		number_of_serving = request.form.get('number_of_serving')
		cooking_hour = request.form.get('cooking_hour')
		cooking_minute = request.form.get('cooking_minute')


		name_ingredient = request.form.get('name_ingredient')
		measure_unit = request.form.get('measure_unit')
		quantity_ingredient = request.form.get('quantity_ingredient')


		text_step = request.form.get('text_step')

		# print(name_recipe,number_of_serving,cooking_hour,cooking_minute,addition,name_ingredient,quantity_ingredient,measure_unit,text_step)
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
