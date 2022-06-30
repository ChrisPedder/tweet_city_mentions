#!/usr/bin/env bash

# Expects one command line arg, twitter handle of user we're scraping for
if [[$# -ne 1]]
then
  echo "Oops, wrong number of args passed to script, expected 1"
  exit 1
else
  HANDLE=$1
fi

echo $HANDLE
STORAGEPATH="twitter-@${HANDLE}"
echo "Scraping tweets for user name ${HANDLE}"

snscrape --jsonl --progress twitter-user "${HANDLE}">"${STORAGEPATH}"

echo "Scraped tweets written to ${STORAGEPATH}"
