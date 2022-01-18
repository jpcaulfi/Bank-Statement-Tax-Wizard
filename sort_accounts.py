#####################################################
# This program based off of functionality from:
#        Intuit Quickbooks
# Not distributed for sale
# Project created for learning purposes
#####################################################

import time
import sys
import mysql.connector


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
        return con
    except mysql.connector.errors.ProgrammingError:
        print("         Connection to database failed")
        print("         Check your values for connection string and schema name in bookkeeper.sh")


def display_account_record(record, existing_nicknames_response):
    for x in range(0, 10):
        print(" ")
    print("Existing bank account nicknames:")
    print("---------------------------------------------------------------")
    print(" ")
    for existing_nickname in existing_nicknames_response:
        if existing_nickname[0] != "NotSpecified":
            print(existing_nickname[0])
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")
    print(" ")
    print(" ")
    print("Account:")
    print("---------------------------------------------------------------")
    print(" ")
    print(f"    Bank: {record[1]}")
    print(" ")
    print(f"    Account Number: {record[2]}")
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")


def display_confirmation(record, nickname):
    for x in range(0, 10):
        print(" ")
    print("Account (Your Changes):")
    print("---------------------------------------------------------------")
    print(" ")
    print(f"    Bank: {record[1]}")
    print(" ")
    print(f"    Account Number: {record[2]}")
    print(" ")
    print(" ")
    print(f"  --Marking as nickname: {nickname}")
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")
    time.sleep(1)
    print("Fetching next account...")
    time.sleep(1)


def sort_accounts():

    update_account_sql = "UPDATE accounts SET nickname = %s WHERE id = %s"
    select_unspecified_accounts_sql = "SELECT * FROM accounts WHERE nickname = 'NotSpecified'"

    # Select all accounts with account nickname "NotSpecified"
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()
    db_cursor.execute(select_unspecified_accounts_sql)
    select_unspecified_accounts_response = db_cursor.fetchall()

    while len(select_unspecified_accounts_response) > 0:

        existing_nicknames_sql = "SELECT nickname FROM accounts GROUP BY nickname"
        db_cursor.execute(existing_nicknames_sql)
        existing_nicknames_response = db_cursor.fetchall()

        # Take the user's input and set the account nickname to their input
        for unspecified_account_record in select_unspecified_accounts_response:
            display_account_record(unspecified_account_record, existing_nicknames_response)
            user_provided_nickname = input("Enter an account nickname for the above account: ").lower()
            db_cursor.execute(update_account_sql, [user_provided_nickname, unspecified_account_record[0]])
            db_connection.commit()
            display_confirmation(unspecified_account_record, user_provided_nickname)
            break

        db_cursor = db_connection.cursor()
        db_cursor.execute(select_unspecified_accounts_sql)
        select_unspecified_accounts_response = db_cursor.fetchall()

    print(" ")
    print(" ")
    print(" ")
    print("All accounts sorted")


# Sorting all bank accounts as checking, savings, etc
for x in range(0, 8):
    print(" ")
proceed = input("You are about to begin sorting the stored bank accounts. Proceed? (y/n)")

if proceed == "y":
    print(" ")
    print(" ")
    print(" ")
    print("   Pulling all stored accounts...")
    time.sleep(1)
    sort_accounts()
