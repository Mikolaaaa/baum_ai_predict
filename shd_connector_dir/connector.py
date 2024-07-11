import requests
import psycopg2
from tenacity import retry, stop_never, stop_after_attempt, wait_fixed


def establish_connection(database, user, password, host, port):
    def connect():
        try:
            print("Trying connection ...")
            return psycopg2.connect(
                                database=database,
                                user=user,
                                password=password,
                                host=host,
                                port=port
                            )
        except psycopg2.OperationalError:
            raise
    return connect()

def authorize(url_login, data_login, headers_login):
    try:
        response_login = requests.post(
                url_login,json=data_login,
                headers=headers_login,
                verify=False
            )
        
        session_id = response_login.cookies.get("BAUMSID")
        return {"Cookie": f"BAUMSID={session_id}"}

    except requests.exceptions.RequestException:
        pass


def api_diskspace(url_diskspace, headers_diskspace):
    try:
        response_diskspace = requests.get(
                url_diskspace,
                headers=headers_diskspace,
                verify=False
            )
        response_diskspace.raise_for_status()
        return response_diskspace.json()
    except requests.exceptions.RequestException:
        pass
