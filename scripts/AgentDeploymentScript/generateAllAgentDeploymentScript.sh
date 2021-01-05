#!/bin/bash
REPLACE=$1
SEARCH="DSM_MACHINE_IP"
CURRDIR=`dirname $0`
cat $CURRDIR/LinuxAgentDeploymentScript | sed -e "s/$SEARCH/$REPLACE/" >> $CURRDIR/LinuxAgentDeploymentScript.sh
cat $CURRDIR/SolarisAgentDeploymentScript | sed -e "s/$SEARCH/$REPLACE/" >> $CURRDIR/SolarisAgentDeploymentScript.sh
cat $CURRDIR/WindowsAgentDeploymentScript | sed -e "s/$SEARCH/$REPLACE/" >> $CURRDIR/WindowsAgentDeploymentScript.ps1
cat $CURRDIR/AIXAgentDeploymentScript | sed -e "s/$SEARCH/$REPLACE/" >> $CURRDIR/AIXAgentDeploymentScript.sh