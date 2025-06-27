import pyodbc
import re

DSN = 'CNC_HW_Details_id'
DATABASE = 'CNC_HW_DETAILS'
TABLE = 'PartsList_Robotics'
SCHEMA = 'dbo'

# Универсальная функция подключения

def get_connection():
    return pyodbc.connect(f'DSN={DSN};DATABASE={DATABASE};Trusted_Connection=yes;')

def get_user_wo_numbers(waan_sa: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT DISTINCT WADOCO
        FROM {SCHEMA}.{TABLE}
        WHERE WAANSA = ? AND WASRST IN (36, 48, 50)
        ORDER BY WADOCO DESC
    ''', (waan_sa,))
    result = [row.WADOCO for row in cursor.fetchall()]
    conn.close()
    return result

def get_wo_e_number_and_model(wo_number: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT WMLOTN, WADL01
        FROM {SCHEMA}.{TABLE}
        WHERE WADOCO = ?
    ''', (wo_number,))
    e_number = None
    model = None
    for row in cursor.fetchall():
        if row.WMLOTN:
            val = str(row.WMLOTN)
            if val.startswith(('E', 'E-', 'F', 'F-')):
                e_number = val
        if row.WADL01 and not model:
            model = str(row.WADL01)
            if 'IND.ROBOT' in model:
                model = model.replace('IND.ROBOT', '').strip()
                model = re.sub(r'^[-\s]+', '', model)
    conn.close()
    return {"e_number": e_number, "model": model}

if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT TOP 5 * FROM {SCHEMA}.{TABLE}')
        columns = [column[0] for column in cursor.description]
        print(columns)
        for row in cursor.fetchall():
            print(row)
        conn.close()
    except Exception as e:
        print(f"Ошибка подключения или запроса: {e}")
