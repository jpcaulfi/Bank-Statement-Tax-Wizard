import sys

import mysql.connector

reset_con = mysql.connector.connect(
    host=sys.argv[2],
    user=sys.argv[4],
    password=sys.argv[5]
)
reset_db_cursor = reset_con.cursor()
reset_db_cursor.execute(f"DROP SCHEMA IF EXISTS {sys.argv[3]}")
reset_con.commit()
reset_db_cursor = reset_con.cursor()
reset_db_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {sys.argv[3]}")
reset_con.commit()
print("\n\nDatabase reset\n\n")
