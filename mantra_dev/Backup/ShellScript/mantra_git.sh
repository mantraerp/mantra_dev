#!/bin/bash

# Configuration variables
API_URL="http://192.168.1.38:8001/api/method/mantra_dev.backend_code.gitapi.mantra_git_pull_with_url"

# Make a REST API request
response=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{\"company_name\": \"mantra\"}")


# Check if the response was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch password from the API." >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
    exit 1
fi

# Parse the password from the response (assumes JSON response)
password=$(echo "$response" | jq -r '.message.password')
git_url=$(echo "$response" | jq -r '.message.git_url')
company=$(echo "$response" | jq -r '.message.company')

if [ ! -d "/home/mantra/mantrastage-bench/GitBackup" ]; then
  cd /home/mantra/mantrastage-bench/
  mkdir GitBackup
fi

echo $password | sudo -S -k chmod 777 -R /home/mantra/mantrastage-bench/GitBackup
cd /home/mantra/mantrastage-bench/GitBackup
time_stamp=$(date +%Y-%m-%d-%T)
echo "Git pull start $time_stamp" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1

echo $password | sudo -S -k mkdir "${time_stamp}"
echo $password | sudo -S -k chmod 777 -R /home/mantra/mantrastage-bench/GitBackup/${time_stamp}
echo $password | sudo -S -k cp -r /home/mantra/mantrastage-bench/apps/mantra_dev "/home/mantra/mantrastage-bench/GitBackup/${time_stamp}"
cd /home/mantra/mantrastage-bench/apps/mantra_dev
git pull --rebase --autostash $git_url >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1