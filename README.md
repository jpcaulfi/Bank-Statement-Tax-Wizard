# Bank Statement Book-Keeper

A Python program designed to extract transactions from downloaded bank statements and organize the 
company's accounting books.

This is a Python implementation of the functionality behind Intuit's QuickBooks.

### How to Use

This program is built to run on Ubuntu.

You must have Python (version > 3.0) installed and MySQL server.

1. Create a schema in MYSQL for this compilation.
2. Provide the database connection string and schema name in the file `bookkeeper.sh`.
3. Download all bank statements as PDFs and place them in the `import` folder.
4. Run `bookkeeper.sh` from the command line using `sudo bash bookkeeper.sh`.

##### Resetting the Database

You can reset your database manually with SQL commands, or you can ues the pre-built Python scripts
`reset_db.py` and `reset_transactions.py`.

`reset_db.py` will simply erase the schema and create it anew, thus it will be empty.

`reset_transactions.py` will save all of your data, but will simply change every transaction category back to `Uncategorized`.

You can trigger either of these within `bookkeeper.sh` by un-commenting the `python3` commands.

### How it Works

Just like the real Intuit QuickBooks functionality that this program is based off, the Bank Account Book Keeper will 
simply try to group transactions that match in name or description and help you sort every single transaction into a category.

You'll have the ability to go through transactions one by one or group all matches into the same category. 

Once the script has run its course (all transactions have been assigned to a category), the program will 
calculate the results and export them to an Excel file for easy reading.

The results will consist of the sum of each category broken down by year and also by fiscal year.

### Fiscal New Year Explained

The fiscal year is what the user can dictate as the end of their financial year in their company's accounting books.
For example, if my business's fiscal year for 2016 is March 2016 - March 2017, I can specify March 1st as my fiscal
new year and view results according to my company's specific business flow.
