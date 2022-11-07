import json

from flask import Flask, render_template, url_for, session, request, redirect, json
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


# def insert_db()

# def select():
# 	command = 'SELECT %s FROM %s'

@app.route('/logout')
def logout():
	session['auth'] = False
	# session.clear()
	return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login():
	#TODO добавить флеши сообщения если что-то не введено
	if request.method == 'POST':
		# Берем из формы логин и пароль
		user_name = request.form.get('user_name')
		email = request.form.get('email')
		password = request.form.get('password')

		# соединение с БД
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		# запрос в БД
		cur.execute('SELECT * FROM user_site WHERE user_name=%s and email=%s', (user_name, email))
		user = cur.fetchone()
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
		user_name = request.form.get('user_name')
		email = request.form.get('email')
		password1 = request.form.get('password1')
		password2 = request.form.get('password2')
		print(request.form)
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT * FROM user_site WHERE user_name=%s and email=%s', (user_name, email))
		user = cur.fetchall()
		if not user and password1 == password2:
			pw_hash = bcrypt.generate_password_hash(password1).decode('utf8')
			cur.execute('INSERT INTO user_site (email, user_name, password) VALUES (%s, %s, %s) RETURNING id', (email, user_name, pw_hash))
			id_user = cur.fetchone()
			session['id'] = id_user['id']
			session['auth'] = True
			con.commit()
			cur.close()
			con.close()
			return redirect('main')
		cur.close()
		con.close()
	return render_template('signup.html')


@app.route('/profile')
def profile():
	if session.get('auth') == True:
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		cur.execute('SELECT * FROM recipe WHERE user_site_id=%s', (session.get('id'),))
		recipes = cur.fetchall()
		cur.close()
		con.close()
		return render_template('profile.html', recipes=recipes)
	return redirect('signup')


@app.route('/add_recipe', methods=['POST', 'GET'])
def add_recipe():
	if not session.get('auth'):
		return redirect('signup')
	elif request.method == 'POST':
		print('прошел')
		#TODO отправка форм в бд
		#TODO название не должно быть пустым
		#TODO минуты тоже не ложны быть пустыми

		#TODO сначала заполняем в БД рецепт, потом ингредиенты,
		# потом просматриваем request.files на наличие фото и с этими фото заполняем
		# шаги. Если все ок отправляем на страницу модерации

		#TODO добавить значение по вкусу, тогда значения кол-во убирается

		#TODO при обновлении страницы, отправляется форма, исправить

		#TODO в ингредиентах кол-во и единица измерения появлентся только тогда когда заполнен name

		# Могут быть пустыми( )
		name_recipe = request.form.get('name_recipe')
		addition = request.form.get('addition')
		number_of_serving = request.form.get('number_of_serving')
		cooking_hour = request.form.get('cooking_hour')
		cooking_minute = request.form.get('cooking_minute')

		if request.form.get('type_recipe'):
			type_recipe = request.form.get('type_recipe')
		else:
			type_recipe = request.form.get('own_type_recipe')

		print(name_recipe)
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

		cur.execute('INSERT INTO recipe (name, addition, number_of_serving, cooking_hour, cooking_minute, user_site_id,'
					'condition, type)'
					'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
					(name_recipe, addition, number_of_serving, cooking_hour, cooking_minute, session.get('id'),
					 'On moderation', type_recipe))
		id_recipe = cur.fetchone()['id']

		name_ingredient = request.form.getlist('name_ingredient[]')
		measure_unit = request.form.getlist('measure_unit[]')
		quantity_ingredient = request.form.getlist('quantity_ingredient[]')

		count_ingredients = len(name_ingredient)
		for i in range(0, count_ingredients):
			cur.execute('INSERT INTO ingredients (name, measure_unit, quantity, recipe_id)'
						'VALUES (%s, %s, %s, %s)',
						(name_ingredient[i], measure_unit[i], quantity_ingredient[i], id_recipe)
						)

		text_step = request.form.getlist('text_step[]')
		image_step = request.form.getlist('image_step[]')

		len_step = len(text_step)
		for i in range(0, len_step):
			if image_step[i]:
				cur.execute('INSERT INTO steps (text, recipe_id, image)'
							'VALUES (%s, %s, %s)',
							(text_step[i], id_recipe, image_step[i])
							)
			else:
				cur.execute('INSERT INTO steps (text, recipe_id)'
						'VALUES (%s, %s)',
						(text_step[i], id_recipe)
						)

		con.commit()
		cur.close()
		con.close()

		print(name_recipe,number_of_serving,cooking_hour,cooking_minute,addition,name_ingredient,quantity_ingredient,measure_unit,text_step)
	return render_template('add_recipe.html')

@app.route('/')
@app.route('/main')
def main():
	""" Вывод всех рецептов
	Сортировка(по времени готовки, по типу рецепта, ВОЗМОЖНО ПО ЦЕНЕ)
	Поиск по названиям
	"""
	print(session.get('id'))
	con = connect_db()
	cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
	cur.execute('SELECT * FROM recipe')
	recipes = cur.fetchall()
	cur.close()
	con.close()
	return render_template('main.html', recipes=recipes)


if __name__ == '__main__':
	app.run(host='127.0.0.1', port=5000, debug=True)
