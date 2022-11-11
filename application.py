from flask import Flask, render_template, url_for, session, request, redirect, json
from flask_session import Session
from conf import DATABASE
import psycopg2
from psycopg2 import extras
from flask_bcrypt import Bcrypt
import requests

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


def price_ingredient():

	return None

@app.route('/logout')
def logout():
	session['auth'] = False
	# session.clear()
	return redirect('main')


@app.route('/login', methods=['POST', 'GET'])
def login():

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

		cur.close()
		con.close()
	print(request.get_data())
	return redirect('main')


@app.route('/signup', methods=['POST', 'GET'])
def signup():

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
			cur.execute('INSERT INTO user_site (email, user_name, password) VALUES (%s, %s, %s) RETURNING id',
						(email, user_name, pw_hash))
			id_user = cur.fetchone()
			session['id'] = id_user['id']
			session['auth'] = True
			con.commit()
			cur.close()
			con.close()
			return redirect('main')
		cur.close()
		con.close()
	return redirect('main')


@app.route('/profile')
def profile():
	if session.get('auth'):
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
		cur.execute('SELECT * FROM recipe WHERE user_site_id=%s', (session.get('id'),))
		recipes = cur.fetchall()
		cur.close()
		con.close()
		return render_template('profile.html', recipes=recipes)
	return redirect('signup')


@app.route('/recipe/<id>')
def recipe(id):
	con = connect_db()
	cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
	cur.execute('SELECT * FROM recipe WHERE id=%s', (id,))
	recipe = cur.fetchall()

	cur.execute('SELECT * FROM steps WHERE recipe_id=%s', (id,))
	steps = cur.fetchall()

	cur.execute('SELECT * FROM ingredients WHERE recipe_id=%s', (id,))
	ingredients = cur.fetchall()
	cur.close()
	con.close()
	return render_template('recipe.html', recipe=recipe, steps=steps, ingredients=ingredients)


@app.route('/recipe/add', methods=['POST', 'GET'])
@app.route('/recipe/edit/<rid>', methods=['POST', 'GET'])
def add_recipe(rid=None):

	# Если пользователь не авторизован, то редирект на регистрацию
	if not session.get('auth'):
		return redirect('signup')

	# Если авторизован и запрос POST проверяем форму
	elif request.method == 'POST':
		# Соединение с БД
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)


		# Сбор данных с формы
		name_recipe = request.form.get('name_recipe')
		addition = request.form.get('addition')
		number_of_serving = request.form.get('number_of_serving')
		cooking_hour = request.form.get('cooking_hour')
		cooking_minute = request.form.get('cooking_minute')

		name_ingredient = request.form.getlist('name_ingredient[]')
		measure_unit = request.form.getlist('measure_unit[]')
		quantity_ingredient = request.form.getlist('quantity_ingredient[]')
		count_ingredients = len(name_ingredient)

		text_step = request.form.getlist('text_step[]')
		image_step = request.form.getlist('image_step[]')
		count_step = len(text_step)

		# Если пользователь выбрал написать свою категорию рецепта
		if request.form.get('type_recipe'):
			type_recipe = request.form.get('type_recipe')
		else:
			type_recipe = request.form.get('own_type_recipe')

		# Если форма редактирования рецепта
		if rid:
			# Обновляем таблицу рецепта
			cur.execute(
				'UPDATE recipe SET name=%s, addition=%s, number_of_serving=%s, cooking_hour=%s, cooking_minute=%s, '
				'user_site_id=%s, condition=%s, type=%s'
				'WHERE id=%s',
				(name_recipe, addition, number_of_serving, cooking_hour, cooking_minute, session.get('id'),
				 'On moderation', type_recipe, rid))

			# Считаем сколько ингредиентов было в бд
			cur.execute('SELECT count(*) from ingredients WHERE recipe_id=%s', (rid,))
			count_ingredients_db = int(cur.fetchone()[0])

			# Сравниваем, если кол-во ингредиентов равное - обновляем
			if count_ingredients_db == count_ingredients:
				for i in range(0, count_ingredients):
					cur.execute(
						'UPDATE ingredients SET name=%s, measure_unit=%s, quantity=%s WHERE recipe_id=%s',
						(name_ingredient[i], measure_unit[i], quantity_ingredient[i], rid))

			# Если кол-во разное - удаляем старые и добавляем новые
			else:
				# Удаление
				cur.execute('DELETE FROM ingredients WHERE recipe_id=%s', (rid,))
				# Добавление
				for i in range(0, count_ingredients):
					cur.execute('INSERT INTO ingredients (name, measure_unit, quantity, recipe_id)'
								'VALUES (%s, %s, %s, %s)',
								(name_ingredient[i], measure_unit[i], quantity_ingredient[i], rid))

			# Считаем сколько шагов было в бд
			cur.execute('SELECT count(*) from steps WHERE recipe_id=%s', (rid,))
			count_step_db = int(cur.fetchone()[0])

			# Сравниваем, если кол-во шагов равное - обновляем таблицу
			if count_step_db == count_step:
				for i in range(0, count_step):
					# Если есть картинка - добавляем ее
					if image_step[i]:
						cur.execute('UPDATE steps SET text=%s, recipe_id=%s, image=%s',
									(text_step[i], rid, image_step[i]))
					else:
						cur.execute('UPDATE steps SET image=%s, text=%s, recipe_id=%s',
									(None, text_step[i], rid))

			# Если кол-во шагов разное - удаляем старые и добавляем новые
			else:
				# Удаление
				cur.execute('DELETE FROM steps WHERE recipe_id=%s', (rid,))
				# Добавление
				for i in range(0, count_step):
					# Если есть картинка - добавляем ее
					if image_step[i]:
						cur.execute('INSERT INTO steps (text, recipe_id, image)'
									'VALUES (%s, %s, %s)',
									(text_step[i], rid, image_step[i]))
					else:
						cur.execute('INSERT INTO steps (text, recipe_id)'
									'VALUES (%s, %s)',
									(text_step[i], rid))

		# Если форма создания рецепта
		else:

			# Создаем рецепт
			cur.execute(
				'INSERT INTO recipe (name, addition, number_of_serving, cooking_hour, cooking_minute, user_site_id,'
				'condition, type)'
				'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
				(name_recipe, addition, number_of_serving, cooking_hour, cooking_minute, session.get('id'),
				 'On moderation', type_recipe))
			# Берем у созданного рецепта id
			id_recipe = cur.fetchone()['id']

			# Добавление ингредиентов
			for i in range(0, count_ingredients):
				cur.execute('INSERT INTO ingredients (name, measure_unit, quantity, recipe_id)'
							'VALUES (%s, %s, %s, %s)',
							(name_ingredient[i], measure_unit[i], quantity_ingredient[i], id_recipe))

			# Добавление шагов
			for i in range(0, count_step):
				# Если есть картинка - добавляем ее
				if image_step[i]:
					cur.execute('INSERT INTO steps (text, recipe_id, image)'
								'VALUES (%s, %s, %s)',
								(text_step[i], id_recipe, image_step[i]))
				else:
					cur.execute('INSERT INTO steps (text, recipe_id)'
								'VALUES (%s, %s)',
								(text_step[i], id_recipe))

		# Сохраняем изменения и закрываем соединение с бд
		con.commit()
		cur.close()
		con.close()
		return redirect('/profile')
	# Если авторизован и запрос GET
	elif rid and request.method == 'GET':
		# Соединение с БД
		con = connect_db()
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

		# Сбор данных с БД
		cur.execute('SELECT * FROM recipe WHERE id=%s', (rid,))
		recipe = cur.fetchall()

		cur.execute('SELECT * FROM steps WHERE recipe_id=%s', (rid,))
		steps = cur.fetchall()

		cur.execute('SELECT * FROM ingredients WHERE recipe_id=%s', (rid,))
		ingredients = cur.fetchall()
		cur.close()
		con.close()
		return render_template('edit_recipe.html', recipe=recipe, steps=steps, ingredients=ingredients)
	return render_template('add_recipe.html')


@app.route('/delete_recipe/<rid>', methods=['GET', 'POST'])
def delete_recipe(rid):
	if request.method == 'POST':
		con = connect_db()
		cur = con.cursor()
		cur.execute('DELETE FROM recipe WHERE id=%s', (rid,))
		con.commit()
		cur.close()
		con.close()
	return redirect('/profile')


@app.route('/')
@app.route('/main')
def main():

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
