import sqlite3

def create_db():
    conn = sqlite3.connect('movies_cache.db')
    cursor = conn.cursor()

    # Crear tabla Movie
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Movie (
        imdbID TEXT PRIMARY KEY,
        title TEXT,
        year TEXT
    )
    ''')

    # Crear tabla Country (ahora incluye un campo para almacenar las imágenes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Country (
        name TEXT PRIMARY KEY,
        flag TEXT  -- Este campo almacenará la URL o los datos de la bandera en base64
    )
    ''')

    # Crear tabla MovieCountry (relaciona películas con países)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MovieCountry (
        imdbID TEXT,
        country_name TEXT,
        FOREIGN KEY(imdbID) REFERENCES Movie(imdbID),
        FOREIGN KEY(country_name) REFERENCES Country(name)
    )
    ''')

    conn.commit()
    conn.close()
create_db()