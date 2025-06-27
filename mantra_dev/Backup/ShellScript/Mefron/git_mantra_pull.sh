#!/bin/bash

GIT_USERNAME="mantraerp"
GIT_TOKEN="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"
GIT_REPO="github.com/mantraerp/mantra.git"
BRANCH="main"
DATE=$(date '+%F_%H_%M_%S')
COMMIT_MSG="Auto_commit_$DATE"
LOG_FILE="/home/mantra/scripts/mantra_pull.log"

#Mefron pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Mefron" >> "$LOG_FILE" 2>&1
cd '/home/mefron-bench/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Mefron" >> "$LOG_FILE" 2>&1

#Smart pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Smart identity" >> "$LOG_FILE" 2>&1
cd '/home/mantrasmartidentity_india/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Smart identity" >> "$LOG_FILE" 2>&1



#Mitras pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Mitras globle" >> "$LOG_FILE" 2>&1
cd '/home/mitras_global/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Mitras globle" >> "$LOG_FILE" 2>&1


#Mewurk pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Mewurk" >> "$LOG_FILE" 2>&1
cd '/home/mewurk/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Mewurk" >> "$LOG_FILE" 2>&1


#Mocula pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Mocula" >> "$LOG_FILE" 2>&1
cd '/home/mocula/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Mocula" >> "$LOG_FILE" 2>&1


#Mupizo pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Mupizo" >> "$LOG_FILE" 2>&1
cd '/home/mupizo/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Mupizo" >> "$LOG_FILE" 2>&1



#Fzco pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in Fzco" >> "$LOG_FILE" 2>&1
cd '/home/fzco/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in Fzco" >> "$LOG_FILE" 2>&1


#fzco dubai pull
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Start mantra pull in fzco dubai" >> "$LOG_FILE" 2>&1
cd '/home/frappe-bench/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE2 - End mantra pull in fzco dubai" >> "$LOG_FILE" 2>&1