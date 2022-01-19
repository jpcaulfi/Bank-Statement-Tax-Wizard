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


def display_transaction_record(record, existing_categories_list, account_nickname_dict):
    for x in range(0, 10):
        print(" ")
    print("Existing transaction categories:")
    print("---------------------------------------------------------------")
    print(" ")
    for existing_category in existing_categories_list:
        print(existing_category)
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")
    print(" ")
    print(" ")
    print("Transaction:")
    print("---------------------------------------------------------------")
    print(" ")
    print(f"    Account Nickname: {account_nickname_dict[record[1]]}")
    print(" ")
    print(f"    Date: {record[2]}")
    print(" ")
    print(f"    Description: {record[4]}")
    print(" ")
    print(f"    Amount: {record[3]}")
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")


def display_single_confirmation(record, category, type, account_nickname_dict, additional_message):
    for x in range(0, 8):
        print(" ")
    print(additional_message)
    print(" ")
    print("Transaction (Your Changes):")
    print("---------------------------------------------------------------")
    print(" ")
    print(f"    Account Nickname: {account_nickname_dict[record[1]]}")
    print(" ")
    print(f"    Date: {record[2]}")
    print(" ")
    print(f"    Description: {record[4]}")
    print(" ")
    print(f"    Amount: {record[3]}")
    print(" ")
    print(" ")
    print(f"  --Marking as transaction category: {category}")
    print(f"  --With type: {type}")
    print(" ")
    print("---------------------------------------------------------------")
    print(" ")


def sort_transactions():

    # Get all the accounts and their nicknames
    get_accounts_sql = "SELECT id, nickname FROM accounts"
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()
    db_cursor.execute(get_accounts_sql)
    account_nickname_dict = {}
    for account_record in db_cursor.fetchall():
        account_nickname_dict[account_record[0]] = account_record[1]

    update_transaction_sql = "UPDATE transactions SET category = %s, type = %s WHERE id = %s"
    select_unspecified_transactions_sql = "SELECT * FROM transactions " \
                                          "WHERE category = 'Uncategorized'"
    db_cursor.execute(select_unspecified_transactions_sql)
    select_unspecified_transactions_response = db_cursor.fetchall()

    category_type_dict = {}

    while len(select_unspecified_transactions_response) > 0:

        # Gather a list of all created categories
        existing_categories_list = []
        existing_categories_sql = "SELECT category FROM transactions GROUP BY category"
        db_cursor.execute(existing_categories_sql)
        existing_categories_response = db_cursor.fetchall()
        for existing_category in existing_categories_response:
            if existing_category[0] != "Uncategorized":
                existing_categories_list.append(existing_category[0])

        for unspecified_transaction_record in select_unspecified_transactions_response:

            # Display the current transaction and prompt the user to input a category
            display_transaction_record(unspecified_transaction_record,
                                       existing_categories_list,
                                       account_nickname_dict)
            user_provided_category = "Uncategorized"
            proceed_assign_category = "n"
            while proceed_assign_category != "y":
                user_provided_category = input("Enter a category for the above transaction: ").lower()

                # If the category doesn't exist, ask for confirmation to create a new one
                if user_provided_category not in existing_categories_list:
                    print(" ")
                    proceed_assign_category = input(f"\n\nCreate new category {user_provided_category}? (y/n)")

                    # Have the user specify the new category as business or non-business
                    if proceed_assign_category == "y":
                        user_provided_category_type = input("\n\nBusiness or non-business?"
                                                            "\n0 for non-business, 1 for business\n: ")
                        if user_provided_category_type.strip()[-1] == '0':
                            category_type_dict[user_provided_category] = "non-business"
                        else:
                            category_type_dict[user_provided_category] = "business"
                else:
                    proceed_assign_category = "y"

            # Search the database for transactions that match the description of the current transaction
            db_cursor.execute(f"SELECT * FROM transactions WHERE description = '{unspecified_transaction_record[4]}'")
            select_matching_transactions_response = db_cursor.fetchall()
            number_of_matches = len(select_matching_transactions_response)

            # Ask the user if they'd like to add all matched transactions to the entered category
            if number_of_matches > 1:
                for x in range(0, 5):
                    print(" ")
                print(f"{number_of_matches} uncategorized transactions match "
                      f"description: {unspecified_transaction_record[4]}")
                proceed_add_all = input(f"Add all to category {user_provided_category}? (y/n)")
            else:
                proceed_add_all = "y"

            # Write the records to the database as specified by user inputs
            if proceed_add_all == "y":
                for matching_transaction in select_matching_transactions_response:
                    db_cursor.execute(update_transaction_sql, [user_provided_category,
                                                               category_type_dict[user_provided_category],
                                                               matching_transaction[0]])
                db_connection.commit()
                display_single_confirmation(unspecified_transaction_record,
                                            user_provided_category,
                                            category_type_dict[user_provided_category],
                                            account_nickname_dict,
                                            f"Adding {number_of_matches} transactions to "
                                            f"category {user_provided_category}\nIncluding:")
            else:
                db_cursor.execute(update_transaction_sql, [user_provided_category,
                                                           category_type_dict[user_provided_category],
                                                           unspecified_transaction_record[0]])
                db_connection.commit()
                display_single_confirmation(unspecified_transaction_record, user_provided_category,
                                            category_type_dict[user_provided_category], " ")
            break

        db_cursor = db_connection.cursor()
        db_cursor.execute(select_unspecified_transactions_sql)
        select_unspecified_transactions_response = db_cursor.fetchall()
        print(f"{len(select_unspecified_transactions_response)} uncategorized transactions remaining")
        print(" ")
        time.sleep(1)
        print("Fetching next transaction...")
        time.sleep(1)

    print(" ")
    print(" ")
    print(" ")
    print("All transactions sorted")


# Sorting all transactions into categories (Intuit Quickbooks)
for x in range(0, 8):
    print(" ")
proceed = input("You are about to begin sorting the stored transactions. Proceed? (y/n)")

if proceed == "y":
    print(" ")
    print(" ")
    print(" ")
    print("   Pulling all stored transactions...")
    time.sleep(3)
    sort_transactions()
