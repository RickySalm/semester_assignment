import psycopg2

connection = psycopg2.connect(
    host='localhost',
    database='semester_site',
    user='postgres',
    password='BARSIKETOZLO'
)

cur = connection.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS user_site ('
            'id SERIAL PRIMARY KEY,'
            'user_name varchar(35) NOT NULL UNIQUE,'
            'email varchar(55) NOT NULL,'
            'password varchar(128) NOT NULL,'
            'created_at time WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,'
            'last_login time WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL'
            ');'
            )

cur.execute('CREATE TABLE IF NOT EXISTS recipe('
            'id SERIAL PRIMARY KEY, '
            'name varchar(200) NOT NULL, '
            'created_at time WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, '
            'update_at time WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, '
            'addition text, '
            'main_image varchar(250), '
            'number_of_serving int, '
            'cooking_hour int, '
            'cooking_minute int, '
            'user_site_id int REFERENCES user_site(id) ON DELETE CASCADE '
            ');'
            )

cur.execute('CREATE TABLE IF NOT EXISTS steps('
            'id SERIAL PRIMARY KEY, '
            'image varchar(250), '
            'text text NOT NULL, '
            'recipe_id int REFERENCES recipe(id) ON DELETE CASCADE'
            ');'
            )

cur.execute('CREATE TABLE IF NOT EXISTS ingredients('
            'id SERIAL PRIMARY KEY, '
            'name varchar(50) NOT NULL, '
            'measure_unit varchar(25) NOT NULL, '
            'quantity int NOT NULL, '
            'recipe_id int REFERENCES recipe(id) ON DELETE CASCADE'
            ');'
            )

cur.execute('CREATE TABLE IF NOT EXISTS favorite_recipe('
            'id SERIAL PRIMARY KEY, '
            'recipe_id int REFERENCES recipe(id) ON DELETE CASCADE, '
            'user_site_id int REFERENCES user_site(id) ON DELETE CASCADE '
            ');'
            )

connection.commit()
cur.close()
connection.close()
