#!/bin/bash

dsru_url=$1
NX_USR=$2
NX_PWD=$3


FILENAME=$(basename $dsru_url)

mkdir –m777 -p /tmp/update-packages

curl -u $NX_USR:$NX_PWD $dsru_url --output /tmp/update-packages/$FILENAME