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

    for x in range(0, 5):
        print(" ")
    print(f"Generating results for schema {sys.argv[2]}")
    for x in range(0, 5):
        print(" ")

    print("\n\n\nWriting summaries...\n\n\n")

    wb = xlsxwriter.Workbook('./results/results.xlsx')
    db_connection = get_database_connection()
    db_cursor = db_connection.cursor()

    summary_sheet = wb.add_worksheet('Summary')
    summary_sheet.write(1, 0, "Summary of Bank Transactions")
    summary_sheet.write(3, 0, sys.argv[5])
    summary_sheet.write(5, 0, "Fiscal New Year:")
    fiscal_new_year_string = month_to_word(fiscal_new_year_array[0]) + " " + day_to_string(fiscal_new_year_array[1])
    summary_sheet.write(5, 2, fiscal_new_year_string)
    summary_sheet.write(7, 0, "Summary of Bank Statements:")

    row = 9
    db_cursor.execute("SELECT YEAR(date) FROM transactions GROUP BY YEAR(date) ORDER BY YEAR(date) ASC")
    select_years_stored_response = db_cursor.fetchall()
    for years_stored in select_years_stored_response:

        year = int(years_stored[0])
        summary_sheet.write(row, 0, "Tax Year " + str(year))
        summary_sheet.write(row, 2, fiscal_new_year_string + ", " + str(year) + " to " + fiscal_new_year_string + ", " + str(year + 1))
        period_start = str(year) + "-" + fiscal_new_year_array[0] + "-" + fiscal_new_year_array[1]
        period_end = str(year + 1) + "-" + fiscal_new_year_array[0] + "-" + fiscal_new_year_array[1]
        row += 2

        nonbusiness_row = row

        select_this_period_business_sql = "SELECT category, SUM(amount) FROM transactions" \
                                          f" WHERE date >= '{period_start}' AND date < '{period_end}'" \
                                          "AND type = 'business' GROUP BY category"
        db_cursor.execute(select_this_period_business_sql)
        this_period_business_response = db_cursor.fetchall()
        summary_sheet.write(row, 1, "Business Transactions:")
        row += 1
        business_gross = 0.00
        business_income = 0.00
        for business_category_record in this_period_business_response:
            summary_sheet.write(row, 1, business_category_record[0])
            summary_sheet.write(row, 2, business_category_record[1])
            business_income += business_category_record[1]
            if business_category_record[1] >= 0:
                business_gross += business_category_record[1]
            row += 1
        row += 1
        summary_sheet.write(row, 1, "Business Gross:")
        summary_sheet.write(row, 2, business_gross)
        summary_sheet.write(row, 1, "Business Income:")
        summary_sheet.write(row, 2, business_income)

        select_this_period_nonbusiness_sql = "SELECT category, SUM(amount) FROM transactions" \
                                              f" WHERE date >= '{period_start}' AND date < '{period_end}'" \
                                              "AND type = 'non-business' GROUP BY category"
        db_cursor.execute(select_this_period_nonbusiness_sql)
        this_period_nonbusiness_response = db_cursor.fetchall()
        summary_sheet.write(row, 4, "Non-Business Transactions:")
        nonbusiness_row += 1
        nonbusiness_gross = 0.00
        nonbusiness_income = 0.00
        for nonbusiness_category_record in this_period_nonbusiness_response:
            summary_sheet.write(nonbusiness_row, 4, nonbusiness_category_record[0])
            summary_sheet.write(nonbusiness_row, 5, nonbusiness_category_record[1])
            nonbusiness_income += nonbusiness_category_record[1]
            if nonbusiness_category_record[1] >= 0:
                nonbusiness_gross += nonbusiness_category_record[1]
            nonbusiness_row += 1
        nonbusiness_row += 1
        summary_sheet.write(nonbusiness_row, 4, "Non-Business Gross:")
        summary_sheet.write(nonbusiness_row, 5, nonbusiness_gross)
        summary_sheet.write(nonbusiness_row, 4, "Non-Business Income:")
        summary_sheet.write(nonbusiness_row, 5, nonbusiness_income)
        row += 4

    print("\n\n\nWriting dump of all transactions...\n\n\n")

    select_all_transactions_sql = "SELECT * FROM transactions"
    db_cursor.execute(select_all_transactions_sql)
    all_transactions_response = db_cursor.fetchall()
    dump_transactions_sheet = wb.add_worksheet('All Transactions')
    dump_transactions_sheet.write(0, 0, "Account ID")
    dump_transactions_sheet.write(0, 1, "Date")
    dump_transactions_sheet.write(0, 2, "Description")
    dump_transactions_sheet.write(0, 3, "Category")
    dump_transactions_sheet.write(0, 4, "Amount")
    row = 1
    for transaction_record in all_transactions_response:
        dump_transactions_sheet.write(row, 0, transaction_record[1])
        dump_transactions_sheet.write(row, 1, str(transaction_record[2]))
        dump_transactions_sheet.write(row, 2, transaction_record[4])
        dump_transactions_sheet.write(row, 3, transaction_record[5])
        dump_transactions_sheet.write(row, 4, transaction_record[3])
        row += 1

    print("\n\n\nWriting list of all accounts...\n\n\n")

    select_all_accounts_sql = "SELECT * FROM accounts"
    db_cursor.execute(select_all_accounts_sql)
    all_accounts_response = db_cursor.fetchall()
    dump_accounts_sheet = wb.add_worksheet('All Accounts')
    dump_accounts_sheet.write(0, 0, "Account ID")
    dump_accounts_sheet.write(0, 1, "Bank")
    dump_accounts_sheet.write(0, 2, "Account Num")
    dump_accounts_sheet.write(0, 3, "Type")
    row = 1
    for account_record in all_accounts_response:
        dump_accounts_sheet.write(row, 0, account_record[0])
        dump_accounts_sheet.write(row, 1, account_record[1])
        dump_accounts_sheet.write(row, 2, account_record[2])
        dump_accounts_sheet.write(row, 3, account_record[3])
        row += 1

    wb.close()


for x in range(0, 8):
    print(" ")

proceed = input("You are about to generate the results of the bank statement sorting.\n\n"
                "An Excel file will be created\n\n Proceed? (y/n)")

if proceed == "y":
    for x in range(0, 8):
        print(" ")
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
