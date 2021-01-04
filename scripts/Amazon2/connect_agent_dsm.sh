#!/bin/bash
PUBLICDNS=$1

sudo /opt/ds_agent/dsa_control -r
sleep 4

DSACONNECTSTRING="dsm://${PUBLICDNS}:4120/"
sudo /opt/ds_agent/dsa_control -a $DSACONNECTSTRING
sleep 4