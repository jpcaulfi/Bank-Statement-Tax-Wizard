import mysql.connector
import sys


# Sets all transactions to "Uncategorized"
reset_record_sql = "UPDATE transactions SET category = %s, type = NULL WHERE id = %s"

con = mysql.connector.connect(
    host=sys.argv[1],
    user=sys.argv[3],
    password=sys.argv[4],
    database=sys.argv[2]
)
db_cursor = con.cursor()
db_cursor.execute("SELECT * FROM transactions WHERE category != 'Uncategorized'")
for record in db_cursor.fetchall():
    db_cursor.execute(reset_record_sql, ["Uncategorized", record[0]])
con.commit()
