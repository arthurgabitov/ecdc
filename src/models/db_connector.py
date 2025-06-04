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

if __name__ == "__main__":
    conn = pyodbc.connect('DSN=CNC_HW_Details_id;Trusted_Connection=yes;')
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 5 * FROM PartsList_Robotics')
    columns = [column[0] for column in cursor.description]
    print(columns)
    for row in cursor.fetchall():
        print(row)
    conn.close()
