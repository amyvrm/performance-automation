#!/bin/bash

function build_docker_image {
	echo 'Building docker Image'
	sudo docker build -t pplay_server -f Dockerfile .
}

function unsupported {
	echo 'Unsupported operating system.'
	exit 1
}

function install_rpm {
	echo 'Installing dependencies for rpm.'
	sudo yum install python37 python37-pip zip unzip docker -y
	#sudo unzip pplay*
	sudo pip3 install pplay
	sudo systemctl enable docker
	sudo systemctl start docker
	sudo groupadd docker
	sudo usermod -aG docker ec2-user
	#newgrp docker
	echo 'Installation of dependencies complete.'
}

function install_deb {
	echo 'Installing dependencies for debian.'
	sudo apt-get update -y
	sudo apt update -y
	sudo apt-get install python3.6 python3-pip zip unzip -y
	sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
	sudo apt update -y
	sudo apt-cache policy docker-ce
	sudo apt install docker-ce -y
	#sudo unzip pplay*
	sudo pip3 install pplay
	sudo systemctl enable docker
	sleep 1
	sudo systemctl start docker
	sleep 1
	#sudo groupadd docker || true
	#sleep 1
	#sudo usermod -aG docker $USER
	#sleep 1
	#newgrp docker
	#sleep 1
	echo 'Installation of dependencies complete.'
}


ARCH=$(uname -m)
if [[ ! $ARCH = *86 ]] && [ ! $ARCH = "x86_64" ] && [ ! $ARCH = "s390x" ]; then
	unsupported
fi

if [ -f /etc/debian_version ]; then
	if [ -f /etc/lsb-release ]; then
		. /etc/lsb-release
		DISTRO=$DISTRIB_ID
		VERSION=${DISTRIB_RELEASE%%.*}
	else
		DISTRO="Debian"
		VERSION=$(cat /etc/debian_version | cut -d'.' -f1)
	fi

	case "$DISTRO" in

		"Ubuntu")
			if [ $VERSION -ge 10 ]; then
				install_deb
			else
				unsupported
			fi
			;;

		"LinuxMint")
			if [ $VERSION -ge 9 ]; then
				install_deb
			else
				unsupported
			fi
			;;

		"Debian")
			if [ $VERSION -ge 6 ]; then
				install_deb
			elif [[ $VERSION == *sid* ]]; then
				install_deb
			else
				unsupported
			fi
			;;

		*)
			unsupported
			;;

	esac

elif [ -f /etc/system-release-cpe ]; then
	DISTRO=$(cat /etc/system-release-cpe | cut -d':' -f3)

	# New Amazon Linux 2 distro
	if [[ -f /etc/image-id ]]; then
		AMZ_AMI_VERSION=$(cat /etc/image-id | grep 'image_name' | cut -d"=" -f2 | tr -d "\"")
	fi

	if [[ "${DISTRO}" == "o" ]] && [[ ${AMZ_AMI_VERSION} = *"amzn2"* ]]; then
		DISTRO=$(cat /etc/system-release-cpe | cut -d':' -f4)
	fi

	VERSION=$(cat /etc/system-release-cpe | cut -d':' -f5 | cut -d'.' -f1 | sed 's/[^0-9]*//g')

	case "$DISTRO" in

		"oracle" | "centos" | "redhat")
			if [ $VERSION -ge 6 ]; then
				install_rpm
			else
				unsupported
			fi
			;;

		"amazon")
			install_rpm
			;;

		"fedoraproject")
			if [ $VERSION -ge 13 ]; then
				install_rpm
			else
				unsupported
			fi
			;;

		*)
			unsupported
			;;

	esac

else
	unsupported
fi

build_docker_image
