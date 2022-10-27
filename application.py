from flask import Flask, render_template, url_for
from conf import DATABASE
import psycopg2
from psycopg2 import extras
app = Flask(__name__, template_folder="templates")


def connect_db():
	connection = psycopg2.connect(
		host=DATABASE['host'],
		database=DATABASE['database'],
		user=DATABASE['user'],
		password=DATABASE['password']
	)
	return connection


@app.route('/')
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
