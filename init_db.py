import psycopg2
from conf import DATABASE

connection = psycopg2.connect(
    host=DATABASE['host'],
    database=DATABASE['database'],
    user=DATABASE['user'],
    password=DATABASE['password']
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


def fill_users(num):
    """
    Creates the required number of users
    :param num: number of users
    :return: inserts user data into the DB
    """
    for i in range(1, num+1):
        email = str(i) + '@mail.ru'
        password = str(i)
        user_name = 'user' + str(i)
        cur.execute('INSERT INTO user_site (user_name, email, password) VALUES (%s, %s, %s)',
                    (user_name, email, password))

def fill_recipe():
    """
    Fills recipes based on existing users
    :return: inserts recipe data into the DB
    """
    cur.execute('SELECT id FROM user_site')
    users = cur.fetchall()
    for id in users:
        cur.execute('INSERT INTO recipe (name, addition, number_of_serving, cooking_hour, cooking_minute, user_site_id)'
                    'VALUES (%s, %s, %s, %s, %s, %s)',
                    ('recipe user'+str(id[0]), '12Lorem ipsum dolor sit amet', 2, id[0]+1, id[0]+20, id[0])
                    )


# fill_users(10)
fill_recipe()
connection.commit()
cur.close()
connection.close()
