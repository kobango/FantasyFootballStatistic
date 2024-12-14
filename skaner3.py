from bs4 import BeautifulSoup
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 1. Pobieranie danych ze strony za pomocą Selenium
def fetch_html(driver):
    # Pobierz zawartość strony
    html_content = driver.page_source
    return html_content

# 2. Parsowanie HTML
def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Szukanie tabeli za pomocą selektora CSS
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

# 4. Funkcja do paginacji za pomocą przycisków
def fetch_all_pages(base_url):
    all_rows = []
    headers = None

    # Konfiguracja WebDriver
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless")  # Tryb bez interfejsu graficznego
    driver = webdriver.Chrome(service=service, options=options)

    # Otwórz stronę
    driver.get(base_url)
    driver.implicitly_wait(10)
    while True:
        html_content = fetch_html(driver)
        page_headers, page_rows = parse_html(html_content)

        if headers is None:
            headers = page_headers

        all_rows.extend(page_rows)

        try:
            # Znajdź element statusu i pobierz maksymalną liczbę stron
            status_element = driver.find_element(By.XPATH, "/html/body/main/div/div[2]/div/div[1]/div[3]/div")
            max_pages = int(status_element.text.split()[-1])

            # Znajdź i kliknij przycisk "Next"
            next_button = driver.find_element(By.XPATH, "/html/body/main/div/div[2]/div/div[1]/div[3]/button[3]")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(2)  # Opcjonalnie: dodaj opóźnienie między żądaniami
            else:
                break

            # Sprawdź, czy osiągnięto maksymalną liczbę stron
            current_page = int(status_element.text.split()[0])
            if current_page >= max_pages:
                break
        except Exception as e:
            print(f"Nie udało się kliknąć przycisku 'Next' lub pobrać statusu: {e}")
            break

    driver.quit()
    return headers, all_rows

# 5. Uruchamianie procesu
if __name__ == '__main__':
    # URL strony
    base_url = 'https://fantasy.premierleague.com/statistics'

    try:
        # Pobranie zawartości wszystkich stron
        headers, rows = fetch_all_pages(base_url)

        # Zapis do bazy danych
        save_to_database(headers, rows)

        print("Dane zostały pomyślnie zapisane w bazie danych.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
