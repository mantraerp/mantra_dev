#!/bin/bash

echo "################  Git auto fixture start $(date +'%Y-%m-%d %H:%M:%S') ###############" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1


echo "Export Fixture start on $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
cd /home/mantra/mantrastage-bench/apps/mantra_dev/
bench export-fixtures
echo "Export Fixture done $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1


# Configuration variables1
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

GIT_USERNAME=$(echo "$response" | jq -r '.message.GIT_USERNAME')
GIT_PAT=$(echo "$response" | jq -r '.message.GIT_PAT')



COMMIT_MESSAGE="Auto-commit fixture $(date +'%Y-%m-%d %H:%M:%S')"


git add .
echo "Git add done $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1

git commit -m "$COMMIT_MESSAGE"
echo "Git commit done $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1

# Extract the remote repository URL
REMOTE_URL=$(git config --get remote.origin.url)
echo "Git Remote url: $REMOTE_URL" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1

# # Construct an authenticated URL using the PAT
# if [[ $REMOTE_URL == https://* ]]; then
#   AUTHENTICATED_URL=${REMOTE_URL/https:\/\//https:\/\/$GIT_PAT@}
# else
#   echo "Error: Remote URL is not HTTPS-based." >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
# #   exit 1
# fi

AUTHENTICATED_URL=$(echo "$REMOTE_URL" | sed "s|https://|https://$GIT_PAT@|")

# Push changes to the current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Git Branch: $BRANCH" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1

git push "$AUTHENTICATED_URL" "$BRANCH"

echo "Git push done $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1



########### Push backup on server

echo "Backup start $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
if [ ! -d "/home/mantra/mantrastage-bench/GitBackup" ]; then
  cd /home/mantra/mantrastage-bench/
  mkdir GitBackup
fi
echo $password | sudo -S -k chmod 777 -R /home/mantra/mantrastage-bench/GitBackup
cd /home/mantra/mantrastage-bench/GitBackup
time_stamp=$(date +%Y-%m-%d-%T)
echo $password | sudo -S -k mkdir "${time_stamp}"
echo $password | sudo -S -k chmod 777 -R /home/mantra/mantrastage-bench/GitBackup/${time_stamp}
echo $password | sudo -S -k cp -r /home/mantra/mantrastage-bench/apps/mantra_dev "/home/mantra/mantrastage-bench/GitBackup/${time_stamp}"
echo "Backup end $(date +'%Y-%m-%d %H:%M:%S')" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
