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

echo "################  Bench migrate start $(date +'%Y-%m-%d %H:%M:%S') ###############" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
cd /home/mantra/mantrastage-bench/apps/
echo $password | sudo -S -k bench migrate
echo "################  Bench migrate end $(date +'%Y-%m-%d %H:%M:%S') ###############" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
