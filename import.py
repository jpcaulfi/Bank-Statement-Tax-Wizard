import mysql.connector
import re
import sys
import time


def get_database_connection():
    db_name = sys.argv[1]
    schema_name = sys.argv[2]
    db_user = sys.argv[3]
    db_pwd = sys.argv[4]
    print(f"      Connecting to database at {db_name}...")
    try:
        con = mysql.connector.connect(
            host=db_name,
            user=db_user,
            password=db_pwd,
            database=schema_name
        )
        print("         Connection to database successful")
        print(f"         Using schema {schema_name}")
        print(" ")
        return con
    except mysql.connector.errors.ProgrammingError:
        print("         Connection to database failed")
        print("         Check your values for connection string and schema name in bookkeeper.sh")
        print(" ")


def log_account_record(bank_name, account_num):
    db_cursor = db_connection.cursor()
    lookup_account_sql = f"SELECT * FROM accounts WHERE bank = '{bank_name}' AND account = '{account_num}'"
    db_cursor.execute(lookup_account_sql)
    lookup_account_response = db_cursor.fetchall()
    db_cursor.close()
    if len(lookup_account_response) > 0:
        for lookup_account_record in lookup_account_response:
            account_id = lookup_account_record[0]
            break
    else:
        db_cursor = db_connection.cursor()
        insert_account_sql = "INSERT INTO accounts (bank, account, type) VALUES (%s, %s, %s)"
        insert_account_val = [bank_name, account_num, "NotSpecified"]
        db_cursor.execute(insert_account_sql, insert_account_val)
        account_id = db_cursor.lastrowid
    time.sleep(1)
    return account_id


def month_to_int(month_string):
    if month_string == "January":
        return 1
    elif month_string == "February":
        return 2
    elif month_string == "March":
        return 3
    elif month_string == "April":
        return 4
    elif month_string == "May":
        return 5
    elif month_string == "June":
        return 6
    elif month_string == "July":
        return 7
    elif month_string == "August":
        return 8
    elif month_string == "September":
        return 9
    elif month_string == "October":
        return 10
    elif month_string == "November":
        return 11
    elif month_string == "December":
        return 12


def scrub_date(date, start_date_string, end_date_string):
    start_date_string_array = start_date_string.split(" ")
    end_date_string_array = end_date_string.split(" ")
    start_month = month_to_int(start_date_string_array[0])
    start_year = start_date_string_array[2].strip()
    end_month = month_to_int(end_date_string_array[0])
    end_year = end_date_string_array[2].strip()
    date_split = date.split("/")
    record_month = int(date_split[0])
    record_year = 0
    if record_month == start_month:
        record_year = start_year
    elif record_month == end_month:
        record_year = end_year
    formatted_date = str(record_year) + "-" + date_split[0] + "-" + date_split[1]
    return formatted_date


def scrub_description(description):
    description = description.replace("CHECKCARD", "")
    description = description.replace("PURCHASE", "")
    description = re.sub('[^a-zA-Z ]', "", description)
    description = re.sub('[X]{3,}', "", description)
    description = re.sub(" +", " ", description)
    description = description.strip()
    return description


def import_transactions():

    insert_transactions_sql = "INSERT INTO transactions " \
                              "(accountid, date, amount, description, category) " \
                              "VALUES(%s, %s, %s, %s, %s)"
    transactions = []

    with open('./temp/import.txt') as transactions_file:
        for line in transactions_file:

            if "-bank-name: " in line:
                bank_name = line.replace("-bank-name: ", "").strip()

            elif "-account-num: " in line:
                account_num = line.replace("-account-num: ", "").strip()[-4:]
                account_id = log_account_record(bank_name, account_num)

            elif "-start: " in line:
                start_date = line.replace("-start: ", "")

            elif "-end: " in line:
                end_date = line.replace("-end: ", "")

            elif "-deposits:" in line:
                transaction_type = "deposits"
                coefficient = 1
                print(f"   Importing {transaction_type} for {bank_name} account ending in {account_num}")
                print(" ")

            elif "-withdrawals:" in line:
                transaction_type = "withdrawals"
                coefficient = -1
                print(f"   Importing {transaction_type} for {bank_name} account ending in {account_num}")
                print(" ")

            elif "-stop:" in line:
                db_cursor = db_connection.cursor()
                db_cursor.executemany(insert_transactions_sql, transactions)
                db_connection.commit()

            else:
                transaction_array = line.split(" ")
                date = scrub_date(transaction_array[0], start_date, end_date)
                amount = coefficient * float(transaction_array[-1].replace("\n", "").replace("$", "").replace("-", "").replace(",", ""))
                description = ""
                for element in transaction_array[1:-1]:
                    description = description + element + " "
                description = scrub_description(description)
                transactions.append([account_id, str(date), str(amount), str(description), "Uncategorized"])

    print("Import successful")
    print("------------------------------------------------------------")


time.sleep(1)
db_connection = get_database_connection()
time.sleep(1)

db_cursor = db_connection.cursor()
create_transactions_table = "(id INT AUTO_INCREMENT PRIMARY KEY, accountid INT, " \
                     "date DATE, amount FLOAT, " \
                     "description VARCHAR(255), category VARCHAR(255), type VARCHAR(255))"
db_cursor.execute("CREATE TABLE IF NOT EXISTS transactions " + create_transactions_table)
db_connection.commit()

db_cursor = db_connection.cursor()
create_accounts_table = "(id INT AUTO_INCREMENT PRIMARY KEY, bank VARCHAR(255), account INT, type VARCHAR(255))"
db_cursor.execute("CREATE TABLE IF NOT EXISTS accounts " + create_accounts_table)
db_connection.commit()

import_transactions()
time.sleep(1)
