from flask import Flask, render_template, request, jsonify
import requests
import json
import movies_db
import sqlite3

app = Flask(__name__)
apikey = "79076a6d"

def searchfilms(search_text):
    conn = sqlite3.connect('movies_cache.db')
    cursor = conn.cursor()

    cursor.execute('SELECT imdbID, title, year FROM Movie WHERE title LIKE ?', ('%' + search_text + '%',))
    movies = cursor.fetchall()

    if movies:
        return {"Search": [{"imdbID": movie[0], "Title": movie[1], "Year": movie[2]} for movie in movies]}

    url = "https://www.omdbapi.com/?s=" + search_text + "&apikey=" + apikey
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "Search" in data:
            cursor.executemany('''
            INSERT OR IGNORE INTO Movie (imdbID, title, year) VALUES (?, ?, ?)
            ''', [(movie["imdbID"], movie["Title"], movie["Year"]) for movie in data["Search"]])
            conn.commit()
        conn.close()
        return data
    else:
        print("Failed to retrieve search results.")
        conn.close()
        return None

    
def getmoviedetails(movie):
    conn = sqlite3.connect('movies_cache.db')
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')

        cursor.execute('SELECT imdbID, title, year FROM Movie WHERE imdbID = ?', (movie["imdbID"],))
        movie_data = cursor.fetchone()

        if movie_data:
            cursor.execute('SELECT country_name FROM MovieCountry WHERE imdbID = ?', (movie["imdbID"],))
            countries = cursor.fetchall()
            if countries:
                countries_data = [{"name": country[0], "flag": get_country_flag(country[0])} for country in countries]
                cursor.execute('COMMIT')
                return {"Title": movie_data[1], "Year": movie_data[2], "Country": ",".join([country[0] for country in countries])}
            else:
                url = "https://www.omdbapi.com/?i=" + movie["imdbID"] + "&apikey=" + apikey
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    if "Country" in data:
                        countries = data["Country"].split(",")
                        cursor.executemany('''
                        INSERT OR IGNORE INTO Country (name, flag) VALUES (?, ?)''', 
                        [(country.strip(), get_country_flag(country.strip())) for country in countries])
                        cursor.executemany(''' 
                        INSERT OR IGNORE INTO MovieCountry (imdbID, country_name) VALUES (?, ?)''', 
                        [(movie["imdbID"], country.strip()) for country in countries])
                        cursor.execute('COMMIT')

                        return {"Title": movie_data[1], "Year": movie_data[2], "Country": ",".join(countries)}
                    else:
                        cursor.execute('ROLLBACK')
                        conn.close()
                        return None
                else:
                    cursor.execute('ROLLBACK')
                    conn.close()
                    return None
        else:
            print(f"No movie data found for IMDb ID: {movie['imdbID']}")
            cursor.execute('ROLLBACK')
            conn.close()
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        cursor.execute('ROLLBACK')
        conn.close()
        return None

def get_country_flag(fullname):
    if not fullname:
        print("Country name is empty, skipping flag request.")
        return None 

    conn = sqlite3.connect('movies_cache.db')
    cursor = conn.cursor()

    try:
        cursor.execute('BEGIN TRANSACTION')

        cursor.execute('SELECT flag FROM Country WHERE name = ?', (fullname,))
        flag_data = cursor.fetchone()

        if flag_data:
            cursor.execute('COMMIT')  
            return flag_data[0]

        url = f"https://restcountries.com/v3.1/name/{fullname}?fullText=true"
        response = requests.get(url)

        if response.status_code == 200:
            country_data = response.json()
            if country_data:
                flag_url = country_data[0].get("flags", {}).get("svg", None)
                if flag_url:
                    cursor.execute('''INSERT OR IGNORE INTO Country (name, flag) VALUES (?, ?)''', (fullname, flag_url))
                    conn.commit()  
                    conn.close()
                    return flag_url
            else:
                print(f"No data returned for country: {fullname}")
                cursor.execute('ROLLBACK')  
        else:
            print(f"Error fetching flag for {fullname}, status code: {response.status_code}")  
            cursor.execute('ROLLBACK')  

    except Exception as e:
        print(f"Error occurred: {e}")
        cursor.execute('ROLLBACK')  

    conn.close()
    return None


def merge_data_with_flags(filter):
    filmssearch = searchfilms(filter)
    # print("filmssearch es: ", filmssearch)
    moviesdetailswithflags = []
    if filmssearch and "Search" in filmssearch:
        for movie in filmssearch["Search"]:
            moviedetails = getmoviedetails(movie)
            countriesNames = moviedetails["Country"].split(",")
            # print("moviedetails es", moviedetails)
            countries = []
            for country in countriesNames:
                # print("country es", country)
                countrywithflag = {
                    "name": country.strip(),
                    "flag": get_country_flag(country.strip())
                }
                countries.append(countrywithflag)
            moviewithflags = {
                "title": moviedetails["Title"],
                "year": moviedetails["Year"],
                "countries": countries
            }
            moviesdetailswithflags.append(moviewithflags)

    return moviesdetailswithflags

@app.route("/")
def index():
    filter = request.args.get("filter", "").upper()
    return render_template("index.html", movies = merge_data_with_flags(filter))

@app.route("/api/movies")
def api_movies():
    filter = request.args.get("filter", "")
    return jsonify(merge_data_with_flags(filter))    

if __name__ == "__main__":
    app.run(debug=True)

