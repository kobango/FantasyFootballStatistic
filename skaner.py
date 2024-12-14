from bs4 import BeautifulSoup
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 1. Pobieranie danych ze strony za pomocą Selenium
def fetch_html(url):
    # Konfiguracja WebDriver
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Tryb bez interfejsu graficznego
    driver = webdriver.Chrome(service=service, options=options)

    # Otwórz stronę
    driver.get(url)

    # Poczekaj na załadowanie strony (opcjonalnie, dodaj więcej logiki jeśli wymagane)
    driver.implicitly_wait(10)

    # Pobierz zawartość strony
    html_content = driver.page_source

    # Zamknij przeglądarkę
    driver.quit()

    return html_content

# 2. Parsowanie HTML
def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Szukanie tabeli za pomocą selektora CSS
    #/html/body/main/div/div[2]/div/div[1]/table
    table = soup.select_one('#root > div:nth-child(2) > div > div:nth-child(1) > table')
    if not table:
        raise Exception("Tabela nie została znaleziona na stronie.")

    # Wyciągnięcie nagłówków tabeli
    headers = [th.text.strip() for th in table.find('thead').find_all('th')]

    # Wyciągnięcie wierszy danych
    rows = []
    for tr in table.find('tbody').find_all('tr'):
        cells = [td.text.strip() for td in tr.find_all('td')]
        rows.append(cells)


    return headers, rows

# 3. Tworzenie bazy danych i zapis danych
def save_to_database(headers, rows, db_name='fantasy.db', table_name='statistics'):
    # Połączenie z bazą danych SQLite
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Tworzenie tabeli (dynamiczne na podstawie nagłówków)
    columns = ', '.join([f'"{header}" TEXT' for header in headers])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns})')

    # Wstawianie danych
    placeholders = ', '.join(['?' for _ in headers])
    cursor.executemany(f'INSERT INTO {table_name} VALUES ({placeholders})', rows)

    conn.commit()
    conn.close()

# 4. Uruchamianie procesu
if __name__ == '__main__':
    # URL strony
    url = 'https://fantasy.premierleague.com/statistics'

    try:
        # Pobranie zawartości strony
        html_content = fetch_html(url)

        # Parsowanie HTML
        headers, rows = parse_html(html_content)

        # Zapis do bazy danych
        save_to_database(headers, rows)

        print("Dane zostały pomyślnie zapisane w bazie danych.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
