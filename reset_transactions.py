import mysql.connector
import sys

reset_record_sql = "UPDATE transactions SET category = %s WHERE id = %s"

con = mysql.connector.connect(
    host=sys.argv[2],
    user=sys.argv[4],
    password=sys.argv[5],
    database=sys.argv[3]
)
db_cursor = con.cursor()
db_cursor.execute("SELECT * FROM transactions WHERE category != 'Uncategorized'")
for record in db_cursor.fetchall():
    db_cursor.execute(reset_record_sql, ["Uncategorized", record[0]])
con.commit()
