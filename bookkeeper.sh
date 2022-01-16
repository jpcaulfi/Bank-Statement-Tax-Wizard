#!/bin/bash

# Enter the repository with cd and run this command:
#    sudo bash bookkeeper.sh

# Enter your database information here:
COMPANY=""
DATABASE_STRING="localhost"
SCHEMA_NAME=""
DATABASE_USERNAME=""
DATABASE_PASSWORD=""

# Setup
sudo apt update
sudo apt-get update
sudo apt install python3 python3-pip poppler-utils
pip install mysql-connector-python xlsxwriter
sudo /etc/init.d/mysql start
echo -e "\n\n\n"
echo "Environment prepared"
sleep 2

# Reset DB
python3 reset_db.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD
echo -e "\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
echo "------------------------------------------------------------"
echo "Launching Bank Statement Tax Wizard"
echo "------------------------------------------------------------"
echo -e "\n\n\n\n\n\n\n\n\n"
sleep 3

# Process PDF files into transaction log
start_time=$(date +%M)
_pdf_files="$(find ./imports/ -name "*.pdf")"
if [[ $_pdf_files == "" ]];
then
  echo "No PDF files detected in folder imports."
  echo "Did you put your PDF files in the right directory?"
  sleep 5
  exit
fi
rm -rf results/
rm -rf temp/
mkdir results
mkdir temp
for f in $_pdf_files
do
  echo "Processing PDF file $f"
  BANK_NAME="$(pdfgrep -m 1 -o '[a-z]*'"\.com" "$f" | sed 's/.com//g')"
  echo "-bank-name: $BANK_NAME" >> ./temp/import.txt
  ACCOUNT_NUM="$(pdfgrep -m 1 "Account number" "$f" | grep -o '[0-9]\+$')"
  echo "-account-num: $ACCOUNT_NUM" >> ./temp/import.txt
  NUMBER_OF_STATEMENTS="$(pdfgrep "" $f | grep -i 'beginning balance on ' | wc -l)"
  LINE_NUMBERS=(`pdfgrep "" $f | grep -i -n 'beginning balance on ' | cut -d : -f 1`)
  for i in $(seq 1 $NUMBER_OF_STATEMENTS)
  do
    if [[ ${LINE_NUMBERS[($i)]} == "" ]];
    then
      declare -i END_OF_FILE=$(pdfgrep "" $f | wc -l)
      declare -i BLOCK_SIZE=$END_OF_FILE-${LINE_NUMBERS[($i-1)]}+1
    else
      declare -i BLOCK_SIZE=${LINE_NUMBERS[($i)]}-${LINE_NUMBERS[($i-1)]}
    fi
    declare -i GREP_INCREMENT=$BLOCK_SIZE-1
    echo "-start: $(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -E -i -o 'beginning balance on [A-Za-z]{1,9}+[ ]*+[0-9]{1,2}+[,]+[ ]*+[0-9]{1,4}' | sed 's/beginning balance on //gi')" >> ./temp/import.txt
    echo "-end: $(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -E -i -o 'ending balance on [A-Za-z]{1,9}+[ ]*+[0-9]{1,2}+[,]+[ ]*+[0-9]{1,4}' | sed 's/ending balance on //gi')" >> ./temp/import.txt
    declare -i TRANSACTIONS_SECTION_END="$(pdfgrep "" $f | grep -m $i -A $BLOCK_SIZE -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -n -i 'total withdrawals' | cut -d : -f 1)"
    TRANSACTIONS_LINE_NUMBERS=(`pdfgrep "" $f | grep -m $i -A $BLOCK_SIZE -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -n -i 'date[ ]*description[ ]*amount' | cut -d : -f 1`)
    declare -i DEPOSITS_SECTION_SIZE=${TRANSACTIONS_LINE_NUMBERS[1]}-${TRANSACTIONS_LINE_NUMBERS[0]}-1
    declare -i WITHDRAWALS_SECTION_SIZE=$TRANSACTIONS_SECTION_END-${TRANSACTIONS_LINE_NUMBERS[1]}-1
    echo "-deposits:" >> ./temp/import.txt
    pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m 1 -A $DEPOSITS_SECTION_SIZE -i 'date[ ]*description[ ]*amount' | grep '[0-9]*\.[0-9]*' | grep '[0-9]*\/[0-9]*' | grep -E '[0-9]{1,2}\/[0-9].*[0-9]{1,3}\.[0-9]{1,2}' >> ./temp/import.txt
    echo "-withdrawals:" >> ./temp/import.txt
    pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m 2 -A $WITHDRAWALS_SECTION_SIZE -i 'date[ ]*description[ ]*amount' | grep '[0-9]*\.[0-9]*' | grep '[0-9]*\/[0-9]*' | grep -E '[0-9]{1,2}\/[0-9].*[0-9]{1,3}\.[0-9]{1,2}' >> ./temp/import.txt
    echo "-stop:" >> ./temp/import.txt
  done
  echo " "
  echo "Processed PDF file $f successfully"
  echo " "
  echo "------------------------------------------------------------"
  echo " "
done
end_time=$(date +%M)
echo "All PDF files processed successfully"
elapsed=$(( end_time - start_time ))
echo "(Took $elapsed minutes)"
sleep 3

# Import transactions into database
echo " "
echo " "
echo "Importing all transaction data into database"
echo " "
python3 import.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD
echo "All transaction data imported into database successfully"

# Sort bank accounts
python3 sort_accounts.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD

# Sort transactions
#python3 reset_transactions.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD
python3 sort_transactions.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD

# Generate results
python3 results.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD "$COMPANY"