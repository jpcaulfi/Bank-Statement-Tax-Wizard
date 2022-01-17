#!/bin/bash

# Enter this repository with cd and run this command:
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

# Launch message
echo -e "\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
echo "------------------------------------------------------------"
echo "Launching Bank Statement Tax Wizard"
echo "------------------------------------------------------------"
echo -e "\n\n\n\n\n\n\n\n\n"
sleep 3

# Process PDF files into transaction log
## Make a list of all PDF files in the imports folder
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

## Iterate over each PDF file
TRANSACTION_REGEX='[0-9]{1,2}\/[0-9].*[0-9]{1,3}\.[0-9]{1,2}'
for f in $_pdf_files
do
  echo "Processing PDF file $f"

  ## Extract the bank name and the account number (last 4 digits) from the PDF file
  BANK_NAME="$(pdfgrep -m 1 -o '[a-z]*'"\.com" "$f" | sed 's/.com//g')"
  echo "-bank-name: $BANK_NAME" >> ./temp/import.txt
  ACCOUNT_NUM="$(pdfgrep -m 1 "Account number" "$f" | grep -o '[0-9]\+$')"
  echo "-account-num: $ACCOUNT_NUM" >> ./temp/import.txt

  ## Determine the number of statements present and the line numbers they begin at
  NUMBER_OF_STATEMENTS="$(pdfgrep "" $f | grep -i 'beginning balance on ' | wc -l)"
  LINE_NUMBERS=(`pdfgrep "" $f | grep -i -n 'beginning balance on ' | cut -d : -f 1`)
  declare -i END_OF_FILE=$(pdfgrep "" $f | wc -l)-1

  ## Iterate over each statement
  for i in $(seq 1 $NUMBER_OF_STATEMENTS)
  do

    ### Identify the size (in lines) of the current statement
    if [[ ${LINE_NUMBERS[($i)]} == "" ]];
    then
      declare -i SECTION_END=$END_OF_FILE
    else
      declare -i SECTION_END=${LINE_NUMBERS[($i)]}
    fi
    declare -i BLOCK_SIZE=$SECTION_END-${LINE_NUMBERS[($i-1)]}
    declare -i GREP_INCREMENT=$BLOCK_SIZE-1

    ### Extract the statement's start and end dates
    echo "-start: $(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -E -i -o 'beginning balance on [A-Za-z]{1,9}+[ ]*+[0-9]{1,2}+[,]+[ ]*+[0-9]{1,4}' | sed 's/beginning balance on //gi')" >> ./temp/import.txt
    echo "-end: $(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -E -i -o 'ending balance on [A-Za-z]{1,9}+[ ]*+[0-9]{1,2}+[,]+[ ]*+[0-9]{1,4}' | sed 's/ending balance on //gi')" >> ./temp/import.txt

    ### Determine the number of transaction sections present and the line numbers they begin at
    NUMBER_OF_TRANSACTION_SECTIONS="$(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -n -i 'date[ ]*description[ ]*amount' | wc -l)"
    TRANSACTION_LINE_NUMBERS=(`pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -n -i 'date[ ]*description[ ]*amount' | cut -d : -f 1`)

    if [[ $NUMBER_OF_TRANSACTION_SECTIONS -gt 0 ]]
    then

      # Iterate over each transaction section
      for j in $(seq 1 $NUMBER_OF_TRANSACTION_SECTIONS)
      do

        ### Identify the size (in lines) of each transaction section
        if [[ ${TRANSACTION_LINE_NUMBERS[($i)]} == "" ]];
        then
          declare -i TRANSACTION_SECTION_END=$SECTION_END
        else
          declare -i TRANSACTION_SECTION_END=${TRANSACTION_LINE_NUMBERS[($i)]}
        fi
        declare -i TRANSACTION_BLOCK_SIZE=$TRANSACTION_SECTION_END-${TRANSACTION_LINE_NUMBERS[($i-1)]}
        declare -i TRANSACTION_GREP_INCREMENT=$TRANSACTION_BLOCK_SIZE-1
        declare -i k=$j*3

        ### Extract all deposits
        GREP_DEPOSITS="$(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m $j -B 2 -i 'date[ ]*description[ ]*amount' | tail -$k | grep -i 'deposits')"
        if [[ $GREP_DEPOSITS != "" ]];
        then
          echo "-deposits:" >> ./temp/import.txt
          DEPOSIT_END_REGEX='[]*[Tt]otal [Dd]eposits.*'
          pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m $j -A $TRANSACTION_GREP_INCREMENT -i 'date[ ]*description[ ]*amount' | tail -$TRANSACTION_BLOCK_SIZE | while read -r line
          do
            if [[ $line =~ $DEPOSIT_END_REGEX ]]
            then
              break
            elif [[ $line =~ $TRANSACTION_REGEX ]]
            then
              echo "$line" >> ./temp/import.txt
            else
              continue
            fi
          done
        fi

        ### Extract all withdrawals
        GREP_WITHDRAWALS="$(pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m $j -B 2 -i 'date[ ]*description[ ]*amount' | tail -$k | grep -i 'withdrawals')"
        if [[ $GREP_WITHDRAWALS != "" ]];
        then
          echo "-withdrawals:" >> ./temp/import.txt
          WITHDRAWAL_END_REGEX='[]*[Tt]otal [Ww]ithdrawals.*'
          pdfgrep "" $f | grep -m $i -A $GREP_INCREMENT -i 'beginning balance on ' | tail -$BLOCK_SIZE | grep -m $j -A $TRANSACTION_GREP_INCREMENT -i 'date[ ]*description[ ]*amount' | tail -$TRANSACTION_BLOCK_SIZE | while read -r line
          do
            if [[ $line =~ $WITHDRAWAL_END_REGEX ]]
            then
              break
            elif [[ $line =~ $TRANSACTION_REGEX ]]
            then
              echo "$line" >> ./temp/import.txt
            else
              continue
            fi
          done
        fi

      done
    fi
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
#python3 sort_accounts.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD

# Sort transactions
#python3 reset_transactions.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD
#python3 sort_transactions.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD

# Generate results
#python3 results.py $DATABASE_STRING $SCHEMA_NAME $DATABASE_USERNAME $DATABASE_PASSWORD "$COMPANY"