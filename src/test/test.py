import sqlite3
from common.constants import DB_PATH

db_path = DB_PATH

def show_database_objects():
    """显示数据库中的所有表和视图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            *
        FROM unified_price_view
    """)
    
    rows = cursor.fetchall()
    print("unified_price_view 数据:")
    for row in rows:
        print(row)
    conn.close()


if __name__ == "__main__":
    show_database_objects()