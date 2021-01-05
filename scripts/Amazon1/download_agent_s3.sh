#!/bin/bash
sudo aws s3 sync s3://regression-testing-jenkins/staging_mttr_artifacts /tmp --exclude "*" --include "*amzn1*"
sleep 2

unzip /tmp/Agent* -d /tmp/extracted
sleep 2

chmod a+rwx /tmp/extracted/
sudo rpm -i /tmp/extracted/Agent-Core-amzn1-*.rpm
sleep 5
