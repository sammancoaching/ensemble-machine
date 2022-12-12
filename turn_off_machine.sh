#!/usr/bin/env sh

usage="$(basename "$0") [-h|MACHINE_IP/HOSTNAME] -- shut down a machine

where:
    -h  show this help text
    MACHINE_IP - the ip address or hostname of the kata machine, eg 13.51.93.104"


shutdown() {
  MACHINE=$1
  PEMFILE=projector.pem
  echo "Shutting down $MACHINE..."
  ssh -i ~/.ssh/$PEMFILE ubuntu@$MACHINE "\
    sudo shutdown -h now\
  "
}

if [ "$1" == "-h" ]; then
  echo "$usage"
  exit 0
fi

shutdown $1
