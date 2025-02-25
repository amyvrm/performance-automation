#!/bin/bash

dsru_url=$1
LABS_JFROG_TOKEN=$2


FILENAME=$(basename $dsru_url)

mkdir –m777 -p /tmp/update-packages

curl -H"Authorization: Bearer $LABS_JFROG_TOKEN" $dsru_url --output /tmp/update-packages/$FILENAME