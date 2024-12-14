from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('fantasy.db')
    conn.row_factory = sqlite3.Row  # Pozwala na zwrócenie wyników jako słownik
    return conn

@app.route('/', methods=['GET'])
def get_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pobranie wszystkich danych z tabeli statistics
    cursor.execute('SELECT * FROM statistics')
    rows = cursor.fetchall()

    # Konwersja danych na listę słowników
    data = [dict(row) for row in rows]

    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
