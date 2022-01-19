#####################################################
# This program based off of functionality from:
#        Intuit Quickbooks
# Not distributed for sale
# Project created for learning purposes
#####################################################

import sys
import re
import time
import mysql.connector
import xlsxwriter


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


def month_to_word(month_string):
    month_int = int(month_string)
    if month_int == 1:
        return "January"
    elif month_int == 2:
        return "February"
    elif month_int == 3:
        return "March"
    elif month_int == 4:
        return "April"
    elif month_int == 5:
        return "May"
    elif month_int == 6:
        return "June"
    elif month_int == 7:
        return "July"
    elif month_int == 8:
        return "August"
    elif month_int == 9:
        return "September"
    elif month_int == 10:
        return "October"
    elif month_int == 11:
        return "November"
    elif month_int == 12:
        return "December"


def drop_leading_zero(date):
    zero_dropped = date
    if date[0] == '0':
        zero_dropped = date[1:]
    return zero_dropped


def day_to_string(day):
    if day[-1] == '1':
        return drop_leading_zero(day) + "st"
    elif day[-1] == '2':
        return drop_leading_zero(day) + "nd"
    elif day[-1] == '3':
        return drop_leading_zero(day) + "rd"
    else:
        return drop_leading_zero(day) + "th"


def generate_results(fiscal_new_year_array):

    fiscal_new_year_string = month_to_word(fiscal_new_year_array[0]) + " " + day_to_string(fiscal_new_year_array[1])

    for x in range(0, 5):
        print(" ")
    print(f"Generating results for schema {sys.argv[2]}")
    for x in range(0, 5):
        print(" ")
    print("\n\n\nWriting summaries...\n\n\n")

    # Get all the accounts and their nicknames
    get_accounts_sql = "SELECT id, nickname FROM accounts"
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()
    db_cursor.execute(get_accounts_sql)
    account_nickname_dict = {}
    for account_record in db_cursor.fetchall():
        account_nickname_dict[account_record[0]] = account_record[1]

    # Create a workbook for each statement (income, sales)
    income_statement_wb = xlsxwriter.Workbook('./results/income_statement.xlsx')
    sales_statement_wb = xlsxwriter.Workbook('./results/sales_statement.xlsx')

    # Create the summary sheet for the income statement
    #   and populate the header with information
    income_summary_sheet = income_statement_wb.add_worksheet('Summary')
    income_summary_sheet.write(1, 0, "Summary of Bank Transactions")
    income_summary_sheet.write(3, 0, sys.argv[5])
    income_summary_sheet.write(5, 0, "Fiscal New Year:")
    income_summary_sheet.write(5, 2, fiscal_new_year_string)
    income_summary_sheet.write(7, 0, "Summary of Bank Statements:")

    # Create the summary sheet for the sales statement
    #   and populate the header with information
    sales_summary_sheet = sales_statement_wb.add_worksheet('Summary')
    sales_summary_sheet.write(1, 0, "Summary of Bank Transactions")
    sales_summary_sheet.write(3, 0, sys.argv[5])
    sales_summary_sheet.write(5, 0, "Fiscal New Year:")
    sales_summary_sheet.write(5, 2, fiscal_new_year_string)
    sales_summary_sheet.write(7, 0, "Summary of Bank Statements:")

    # Get all years present in the transactions table, and iterate over them
    #
    # Note:
    #    The years present provide a list to iterate over,
    #    however the results are still calculated over the user's
    #    fiscal-year range.
    #        i.e. Company with fiscal new year of March 31:
    #             iterating over year 2018
    #             take date range March 31 2018 - March 31 2019
    #
    db_cursor.execute("SELECT YEAR(date) FROM transactions GROUP BY YEAR(date) ORDER BY YEAR(date) ASC")
    select_years_stored_response = db_cursor.fetchall()

    # Row increments
    #   income_b_row  = Income Statement Business row
    #   income_nb_row = Income Statement Non-Business row
    #   sales_b_row   = Sales Statement Business row
    #   sales_nb_row  = Sales Statement Non-Business row
    income_b_row = 9
    sales_b_row = 9

    for years_stored in select_years_stored_response:

        year = int(years_stored[0])

        # Write the subheader for each statement's summary sheet
        income_summary_sheet.write(income_b_row, 0, "Tax Year " + str(year))
        income_summary_sheet.write(income_b_row, 2, fiscal_new_year_string + ", " + str(year) + " to " + fiscal_new_year_string + ", " + str(year + 1))
        sales_summary_sheet.write(sales_b_row, 0, "Tax Year " + str(year))
        sales_summary_sheet.write(sales_b_row, 2, fiscal_new_year_string + ", " + str(year) + " to " + fiscal_new_year_string + ", " + str(year + 1))

        period_start = str(year) + "-" + fiscal_new_year_array[0] + "-" + fiscal_new_year_array[1]
        period_end = str(year + 1) + "-" + fiscal_new_year_array[0] + "-" + fiscal_new_year_array[1]
        income_b_row += 2
        sales_b_row += 2
        income_nb_row = income_b_row
        sales_nb_row = sales_b_row

        # Get the sum of each transaction category from the database
        # For business transactions
        select_this_period_business_sql = "SELECT category, SUM(amount) FROM transactions" \
                                          f" WHERE date >= '{period_start}' AND date < '{period_end}'" \
                                          "AND type = 'business' GROUP BY category"
        db_cursor.execute(select_this_period_business_sql)
        this_period_business_response = db_cursor.fetchall()

        # Write business transactions section subheader in each
        income_summary_sheet.write(income_b_row, 1, "Business Transactions:")
        sales_summary_sheet.write(sales_b_row, 1, "Business Transactions:")
        income_b_row += 1
        sales_b_row += 1

        # Write each category for business transactions into the income statement
        # If the sum is positive, also write it into the sales statement
        business_gross = 0.00
        business_income = 0.00
        for business_category_record in this_period_business_response:
            income_summary_sheet.write(income_b_row, 1, business_category_record[0].title())
            income_summary_sheet.write(income_b_row, 2, business_category_record[1])
            business_income += business_category_record[1]
            if business_category_record[1] >= 0:
                business_gross += business_category_record[1]
                sales_summary_sheet.write(sales_b_row, 1, business_category_record[0].title())
                sales_summary_sheet.write(sales_b_row, 2, business_category_record[1])
                sales_b_row += 1
            income_b_row += 1
        income_b_row += 1
        sales_b_row += 1

        # Write the totals
        income_summary_sheet.write(income_b_row, 1, "Business Gross:")
        income_summary_sheet.write(income_b_row, 2, business_gross)
        sales_summary_sheet.write(sales_b_row, 1, "Business Gross:")
        sales_summary_sheet.write(sales_b_row, 2, business_gross)
        income_summary_sheet.write(income_b_row, 1, "Business Income:")
        income_summary_sheet.write(income_b_row, 2, business_income)

        # Get the sum of each transaction category from the database
        # For non-business transactions
        select_this_period_nonbusiness_sql = "SELECT category, SUM(amount) FROM transactions" \
                                              f" WHERE date >= '{period_start}' AND date < '{period_end}'" \
                                              "AND type = 'non-business' GROUP BY category"
        db_cursor.execute(select_this_period_nonbusiness_sql)
        this_period_nonbusiness_response = db_cursor.fetchall()

        # Write business transactions section subheader in each
        income_summary_sheet.write(income_nb_row, 4, "Non-Business Transactions:")
        sales_summary_sheet.write(sales_nb_row, 4, "Non-Business Transactions:")
        income_nb_row += 1
        sales_nb_row += 1

        # Write each category for non-business transactions into the income statement
        # If the sum is positive, also write it into the sales statement
        nonbusiness_gross = 0.00
        nonbusiness_income = 0.00
        for nonbusiness_category_record in this_period_nonbusiness_response:
            income_summary_sheet.write(income_nb_row, 4, nonbusiness_category_record[0].title())
            income_summary_sheet.write(income_nb_row, 5, nonbusiness_category_record[1])
            nonbusiness_income += nonbusiness_category_record[1]
            if nonbusiness_category_record[1] >= 0:
                nonbusiness_gross += nonbusiness_category_record[1]
                sales_summary_sheet.write(sales_nb_row, 4, nonbusiness_category_record[0].title())
                sales_summary_sheet.write(sales_nb_row, 5, nonbusiness_category_record[1])
                sales_nb_row += 1
            income_nb_row += 1
        income_nb_row += 1
        sales_nb_row += 1

        # Write the totals
        income_summary_sheet.write(income_nb_row, 4, "Non-Business Gross:")
        income_summary_sheet.write(income_nb_row, 5, nonbusiness_gross)
        sales_summary_sheet.write(sales_nb_row, 4, "Non-Business Gross:")
        sales_summary_sheet.write(sales_nb_row, 5, nonbusiness_gross)
        income_summary_sheet.write(income_nb_row, 4, "Non-Business Income:")
        income_summary_sheet.write(income_nb_row, 5, nonbusiness_income)

        if income_nb_row > income_b_row:
            income_b_row = income_nb_row
        if sales_nb_row > sales_b_row:
            sales_b_row = sales_nb_row
        income_b_row += 4
        sales_b_row += 4

    # Write a dump of all transactions into a new sheet in both workbooks
    print("\n\n\nWriting dump of all transactions...\n\n\n")
    select_all_transactions_sql = "SELECT * FROM transactions"
    db_cursor.execute(select_all_transactions_sql)
    all_transactions_response = db_cursor.fetchall()
    income_dump_t_sheet = income_statement_wb.add_worksheet('All Transactions')
    income_dump_t_sheet.write(0, 0, "Account")
    income_dump_t_sheet.write(0, 1, "Date")
    income_dump_t_sheet.write(0, 2, "Description")
    income_dump_t_sheet.write(0, 3, "Category")
    income_dump_t_sheet.write(0, 4, "Amount")
    sales_dump_t_sheet = sales_statement_wb.add_worksheet('All Transactions')
    sales_dump_t_sheet.write(0, 0, "Account")
    sales_dump_t_sheet.write(0, 1, "Date")
    sales_dump_t_sheet.write(0, 2, "Description")
    sales_dump_t_sheet.write(0, 3, "Category")
    sales_dump_t_sheet.write(0, 4, "Amount")
    dump_t_row = 1
    for transaction_record in all_transactions_response:
        income_dump_t_sheet.write(dump_t_row, 0, account_nickname_dict[transaction_record[1]])
        income_dump_t_sheet.write(dump_t_row, 1, str(transaction_record[2]))
        income_dump_t_sheet.write(dump_t_row, 2, transaction_record[4])
        income_dump_t_sheet.write(dump_t_row, 3, transaction_record[5].title())
        income_dump_t_sheet.write(dump_t_row, 4, transaction_record[3])
        sales_dump_t_sheet.write(dump_t_row, 0, account_nickname_dict[transaction_record[1]])
        sales_dump_t_sheet.write(dump_t_row, 1, str(transaction_record[2]))
        sales_dump_t_sheet.write(dump_t_row, 2, transaction_record[4])
        sales_dump_t_sheet.write(dump_t_row, 3, transaction_record[5].title())
        sales_dump_t_sheet.write(dump_t_row, 4, transaction_record[3])
        dump_t_row += 1

    # Write a dump of all accounts into a new sheet in both workbooks
    print("\n\n\nWriting list of all accounts...\n\n\n")
    select_all_accounts_sql = "SELECT * FROM accounts"
    db_cursor.execute(select_all_accounts_sql)
    all_accounts_response = db_cursor.fetchall()
    income_dump_a_sheet = income_statement_wb.add_worksheet('All Accounts')
    income_dump_a_sheet.write(0, 0, "Account ID")
    income_dump_a_sheet.write(0, 1, "Bank")
    income_dump_a_sheet.write(0, 2, "Account Num")
    income_dump_a_sheet.write(0, 3, "Nickname")
    sales_dump_a_sheet = sales_statement_wb.add_worksheet('All Accounts')
    sales_dump_a_sheet.write(0, 0, "Account ID")
    sales_dump_a_sheet.write(0, 1, "Bank")
    sales_dump_a_sheet.write(0, 2, "Account Num")
    sales_dump_a_sheet.write(0, 3, "Nickname")
    dump_a_row = 1
    for account_record in all_accounts_response:
        income_dump_a_sheet.write(dump_a_row, 0, account_record[0])
        income_dump_a_sheet.write(dump_a_row, 1, account_record[1])
        income_dump_a_sheet.write(dump_a_row, 2, account_record[2])
        income_dump_a_sheet.write(dump_a_row, 3, account_record[3].title())
        sales_dump_a_sheet.write(dump_a_row, 0, account_record[0])
        sales_dump_a_sheet.write(dump_a_row, 1, account_record[1])
        sales_dump_a_sheet.write(dump_a_row, 2, account_record[2])
        sales_dump_a_sheet.write(dump_a_row, 3, account_record[3].title())
        dump_a_row += 1

    income_statement_wb.close()
    sales_statement_wb.close()


# Generating Excel workbooks with results
# One for income (income tax), one for just sales (sales tax)
for x in range(0, 8):
    print(" ")

proceed = input("You are about to generate the results of the bank statement sorting.\n\n"
                "An Excel file will be created\n\n Proceed? (y/n)")

if proceed == "y":
    for x in range(0, 8):
        print(" ")

    # Get user's input for fiscal new year in correct format (enforce)
    entry_does_not_match = True
    fiscal_new_year = ""
    while entry_does_not_match:
        print("Enter fiscal new year in the following format: MM-DD")
        print(" ")
        print("If your fiscal new year is simply the calendar new year, enter 01-01")
        print(" ")
        print("Do not deviate from the format")
        print(" ")
        fiscal_new_year = input("Enter fiscal new-year: ")
        if re.match('[0-9]{2}-[0-9]{2}', fiscal_new_year):
            entry_does_not_match = False
        else:
            print(" ")
            print(" ")
            print("Incorrect format")
            for x in range(0, 5):
                print(" ")
            time.sleep(1)
    fiscal_new_year_array = fiscal_new_year.split("-")
    time.sleep(1)
    generate_results(fiscal_new_year_array)
    for x in range(0, 8):
        print(" ")
    print("Report generated successfully.\n\nCheck the results folder in this repository.\n\n")
