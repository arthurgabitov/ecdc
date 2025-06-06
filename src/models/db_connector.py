import pyodbc

def get_user_wo_numbers(waan_sa: str):
    conn = pyodbc.connect('DSN=CNC_HW_Details_id;Trusted_Connection=yes;')
    cursor = conn.cursor()
    # Получаем только те WO, где WAANSA совпадает и WASRST в (36, 48, 50)
    cursor.execute('''
        SELECT DISTINCT WADOCO
        FROM PartsList_Robotics
        WHERE WAANSA = ? AND WASRST IN (36, 48, 50)
        ORDER BY WADOCO DESC
    ''', (waan_sa,))
    result = [row.WADOCO for row in cursor.fetchall()]
    conn.close()
    return result

def get_wo_e_number_and_model(wo_number: str):
    """
    Получить Е-номер (WMLOTN) и модель робота (WADL01) для данного WO из базы данных.
    Возвращает словарь: {"e_number": ..., "model": ...}
    """
    conn = pyodbc.connect('DSN=CNC_HW_Details_id;Trusted_Connection=yes;')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT WMLOTN, WADL01
        FROM PartsList_Robotics
        WHERE WADOCO = ?
    ''', (wo_number,))
    e_number = None
    model = None
    for row in cursor.fetchall():
        # Ищем подходящий формат Е-номера
        if row.WMLOTN:
            val = str(row.WMLOTN)
            if val.startswith(('E', 'E-', 'F', 'F-')):
                e_number = val
        if row.WADL01 and not model:
            model = str(row.WADL01)
    conn.close()
    return {"e_number": e_number, "model": model}

if __name__ == "__main__":
    conn = pyodbc.connect('DSN=CNC_HW_Details_id;Trusted_Connection=yes;')
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 5 * FROM PartsList_Robotics')
    columns = [column[0] for column in cursor.description]
    print(columns)
    for row in cursor.fetchall():
        print(row)
    conn.close()
