import sys
import time
import signal
import logging
from datetime import datetime
from connector import authorize, establish_connection, api_diskspace
from tenacity import retry, stop_never, stop_after_attempt, wait_fixed
from dotenv import load_dotenv
import os
import psycopg2
import concurrent.futures
load_dotenv()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIME_INERVAL = 10.0

URL_LOGIN = os.getenv("URL_LOGIN")


host = os.getenv("HOST")
port = os.getenv("PORT")
database = os.getenv("DATABASE")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
connect_timeout = os.getenv("connect_timeout")

# Конфигурация для подключения к базе данных
DATABASE = database
USER = user
PASSWORD = password
HOST = host
PORT = port

# Параметры подключения к PostgreSQL
db_params = {
    'host': host,
    'port': port,
    'database': database,
    'user': user,
    'password': password,
    'connect_timeout': connect_timeout
}

def connect_to_postgres():
    logger.info("gbfddffd")
    return establish_connection(DATABASE, USER, PASSWORD, HOST, PORT)


def handle_interrupt(signal, frame):
    sys.exit(0)


# Функция для выполнения SQL-запроса к PostgreSQL
def execute_query(query):
    while True:
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            cursor.execute(query)

            # Если запрос начинается с SELECT, получаем результат
            if query.strip().lower().startswith('select'):
                # Получение метаданных о столбцах
                column_names = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
            else:
                result = None

            connection.commit()

            cursor.close()
            connection.close()

            # Возвращаем результат и названия столбцов
            logger.info("execute_query")
            return result, column_names if 'column_names' in locals() else None


        except psycopg2.OperationalError as e:
            print(f"Ошибка при выполнении запроса: {e}")
            print("Повторная попытка подключения через 5 секунд...")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return None


def process_table(index, table_data):
    headers = {"content-type": "application/json"}
    logger.info(f"Обработка таблицы: {table_data[0]}")

    connection = connect_to_postgres()
    cursor = connection.cursor()

    DATA_LOGIN = {"login": table_data[2], "password": table_data[3], "remember": True}

    URL_DISKSPACE = f"http://{table_data[1]}/api/v2.0/disks"
    data = api_diskspace(URL_DISKSPACE, authorize(URL_LOGIN, DATA_LOGIN, headers))

    total = sum(ppp['size'] for ppp in data if not ppp['props']['rdcache'])
    total_cap_array = total / (1024 * 1024 * 1024)

    URL_POOLSPACE = f"http://{table_data[1]}/api/v2.0/pools"
    data = api_diskspace(URL_POOLSPACE, authorize(URL_LOGIN, DATA_LOGIN, headers))

    used_cap_all = 0
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    datetime_object = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S.%f")

    def convert_to_gb(size_str):
        unit = size_str[-1]
        size = float(size_str[:-1])
        if unit == 'T':
            size *= 1024
        elif unit == 'K':
            size /= 1024 * 1024
        elif unit == 'M':
            size /= 1024
        return size

    i = 1
    for ppp in data['pools']:
        size = ppp['props']['size']
        used = ppp['props']['used']
        name = ppp['name']

        if used != '0':
            used = convert_to_gb(used)
            size = convert_to_gb(size)
            cursor.execute(
                f'INSERT INTO "{table_data[0]}" (sn, "object type", object, time, "Capacity usage(%%)", "Total capacity(GB)", "Used capacity(GB)", array_num) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                ("20240207000000", "Storage Pool", f"StoragePool00{i}", datetime_object,
                 (used / size) * 100, size,
                 used, "Array1"))
            used_cap_all += used
        i += 1

    percent = used_cap_all / total_cap_array * 100

    cursor.execute(
        f'INSERT INTO "{table_data[0]}" (sn, array_num, "object type", object, time, "Capacity usage(%%)", "Total capacity(GB)", "Used capacity(GB)") VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        ("20240207000000", "Array1", "Array", "System", datetime_object, percent, total_cap_array,
         used_cap_all))

    connection.commit()
    cursor.close()
    connection.close()
    logger.info(f"Обработка таблицы {table_data[0]} завершена.")

def main():
    headers = {"content-type": "application/json"}

    while True:
        shd, _ = execute_query("select name, ip, login, password from shd_s")

        if not shd:
            logger.warning("Нет записей в таблице shd_s. Повторная попытка через 10 секунд...")
            time.sleep(TIME_INERVAL)
            continue

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(shd)) as executor:
                futures = [executor.submit(process_table, z, shd[z]) for z in range(len(shd))]

                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Ошибка в потоке: {e}")

        except Exception as e:
            logger.error(f"Произошла ошибка при обработке таблиц: {e}")

        logger.info("Все таблицы обработаны. Ожидание перед следующей проверкой...")
        time.sleep(TIME_INERVAL)

if __name__ == "__main__":
    main()
