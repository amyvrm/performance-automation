#!/bin/bash

#Set timeout value in seconds to make pplay exit if it waits for too long.
timeout_value=90

#Method used to filter connaction, when no usable connaction is present by defualt.
function filter_connection {
	pplay.py --pcap "$1" --list 2>&1 | sudo sed 's/\x1b\[[0-9;]*m//g' | sudo tee pcap_connection.txt
	sudo sed -i -e 1,4d pcap_connection.txt
	usable_connection_unfiltered=`cat pcap_connection.txt`
	
	no_candidate=false
	no_candidate_substring="no candidate"
	usable_connection=$(head -n 1 pcap_connection.txt)
	if [[ "$usable_connection_unfiltered" == *"$no_candidate_substring"* ]]; then
		no_candidate=true
		usable_connection=$(head -n 1 pcap_connection.txt)
	fi
}

#Replays single pcap file by mounting it to container.
function single_pcap_file_play {

	fullfilepath="$1"
	pcap="$2"
	#fullfilepath=$(printf %q "$1")
	#pcap_container=$(printf %q "$2")
	
	
	if [ "$no_candidate" = false ]; then
		echo "executing without usable connection"
		sudo docker run -id --privileged --name pplay_container -v "${fullfilepath}:${pcap}" pplay_server /bin/bash -c "pplay.py --server 8080 --pcap \"${pcap}\""
	else
		echo "Using connection $usable_connection"
		echo "executing with usable connection"
		echo "$fullfilepath"
		echo "$pcap"
		#echo "$pcap_container"
		#--connection $usable_connection
		sudo docker run -id --privileged --name pplay_container -v "${fullfilepath}:${pcap}" pplay_server /bin/bash -c "pplay.py --server 8080 --pcap \"${pcap}\" --connection $usable_connection"
	fi
	
	sleep 1
	
	client_ip=$(sudo docker inspect pplay_container | grep -w "IPAddress" | awk '{ print $2 }' | head -n 1 | cut -d "," -f1)
	
	client_ip="${client_ip//\"}"
	
	echo $client_ip
	
	sleep 1
	
	if [ "$no_candidate" = false ]; then
		timeout $timeout_value pplay.py --client $client_ip:8080 --pcap "${fullfilepath}" --exitoneot
	else
		echo "Using connection $usable_connection"
		timeout $timeout_value pplay.py --client $client_ip:8080 --pcap "${fullfilepath}" --connection $usable_connection --exitoneot
	fi
	
	sleep 2
}

#Replays folder containing pcaps by mounting pcap folder to container.
function pcap_folder_play {
	
	fullfolderpath=$1
	folder=$2
	filename=$3
	fullfilepath=$4
	
	if [ "$no_candidate" = false ]; then
		sudo docker run -id --privileged --name pplay_container -v $fullfolderpath:/tmp/$folder pplay_server /bin/bash -c "pplay.py --server 8080 --pcap $folder/$filename"
	else
		echo "Using connection $usable_connection"
		sudo docker run -id --privileged --name pplay_container -v $fullfolderpath:/tmp/$folder pplay_server /bin/bash -c "pplay.py --server 8080 --pcap $folder/$filename --connection $usable_connection"
	fi

	sleep 1

	client_ip=$(docker inspect pplay_container | grep -w "IPAddress" | awk '{ print $2 }' | head -n 1 | cut -d "," -f1)

	client_ip="${client_ip//\"}"

	echo $client_ip

	sleep 1
	
	if [ "$no_candidate" = false ]; then
		timeout $timeout_value pplay.py --nostdin --client $client_ip:8080 --pcap $fullfilepath --exitoneot
	else
		echo "Using connection $usable_connection"
		timeout $timeout_value pplay.py --nostdin --client $client_ip:8080 --pcap $fullfilepath --connection $usable_connection --exitoneot
	fi
}


#Main script to replay pcaps using above methods.
if [ "$#" -ne 2 ]; then
    echo 'Please supply only one argument. Either -p for pcap file ansolute path or -f for folder containing pcaps absolute path.'
    exit 1
fi

while getopts p:f: flag
do
    case "${flag}" in
	p) pcap=${OPTARG};;
    f) folder=${OPTARG};;
    esac
done

if [ -z "$folder" ]; then
    echo "Replaying single pcap. $pcap"
	
	fullfilepath=$(realpath "$pcap")
	echo $fullfilepath
	
	filter_connection "$fullfilepath"
	
	single_pcap_file_play "$fullfilepath" "$pcap"
	
	
else
	for pcap_file in "$folder"/*
	do
		echo "Replaying all pcaps from folder $folder"
		
		echo "$pcap_file"
		
		filename=$(basename $pcap_file)
		
		fullfolderpath=$(realpath $folder)
		
		fullfilepath=$(realpath $pcap_file)
		
		filter_connection $fullfilepath
		
		## use either pcap_folder_play or single_pcap_file_play. Both works.
		
		#pcap_folder_play $fullfolderpath $folder $filename $fullfilepath
		
		single_pcap_file_play $fullfilepath $pcap_file
		
		sudo docker stop pplay_container

		sudo docker rm pplay_container
		
	done
fi

#If execution fails this will destroy container anyhow.
sudo docker stop pplay_container || echo "Exiting.."

sudo docker rm pplay_container || echo "Exiting.."
