#!/usr/bin/env python3
import configparser
import csv
import json
import os
import pathlib
import secrets
import time

import boto3
import click
from dataclasses import dataclass

import update_dns


def read_ide_config(config=None):
    config = config or pathlib.Path().resolve() / "ide_config.json"
    assert config.exists(), "missing ide_config.json file, expected to be in current working directory"
    with open(config) as f:
        configs = json.load(f)
        for key in configs.keys():
            configs[key]["config_name"] = key
        return configs


def read_regions_config(config=None):
    config = config or pathlib.Path().resolve() / "aws_zones.json"
    assert config.exists(), "missing aws_zones.json file, expected to be in current working directory"
    with open(config) as f:
        return json.load(f)


def generate_script(dns_name, config_name,
                    name, extra_packages,
                    snap_packages, environment, note=None):
    required_packages = [
        "less",
        "python3-pip",
        "libxext6",
        "libxrender1",
        "libxtst6",
        "libfreetype6",
        "libxi6",
        "libxss1",
        "nginx",
        "certbot",
        "python3-certbot-nginx",
    ]
    packages = required_packages + extra_packages
    packages_argument = " ".join(packages)
    snap_packages_to_install = " ".join(snap_packages)
    install_snap_classic_packages = f"sudo snap install {snap_packages_to_install} --classic" if snap_packages else ""
    environment_file = "\n".join(f"{key}={value}" for key, value in environment.items())
    return f"""\
#! /bin/sh
set -ex

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb https://download.mono-project.com/repo/ubuntu stable-focal main" | \
  sudo tee /etc/apt/sources.list.d/mono-official-stable.list

sudo apt update -y
sudo apt install -y {packages_argument}

{install_snap_classic_packages}

sudo adduser --gecos "" --disabled-password typist

sudo -u typist git config --global user.name "Typist"
sudo -u typist git config --global user.email "typist@example.com"

sudo -u typist pip3 install projector-installer==1.6.0 --user

sudo -u typist /home/typist/.local/bin/projector \\
 --accept-license autoinstall \\
 --config-name "{config_name}" \\
 --ide-name "{name}" \\
 --port "8080"

cat << ENV | sudo tee -a /etc/environment
{environment_file}
ENV

cat << SCRIPT | sudo tee /lib/systemd/system/{config_name}.service
[Unit]
Description=Jetbrains Projector - {config_name}

[Service]
User=typist
Type=simple
ExecStart=/home/typist/.projector/configs/%N/run.sh
Restart=always

[Install]
WantedBy=multi-user.target
SCRIPT

sudo systemctl daemon-reload
sudo systemctl enable "{config_name}"
sudo systemctl start "{config_name}"

#configure nginx
cat << CONFIG | sudo tee /etc/nginx/sites-available/default
server {{
  listen       80;
  server_name  {dns_name};
  location / {{
    proxy_pass http://localhost:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host \$host;
    proxy_cache_bypass \$http_upgrade;
  }}
}}
CONFIG

# configure nginx with let's encrypt certificate
sudo certbot --nginx \
  --non-interactive \
  --redirect \
  --agree-tos \
  --register-unsafely-without-email \
  --domain {dns_name}

"""


@dataclass
class ProjectorInstance:
    config_name: str
    dns_name: str
    coach: str
    region_name: str
    room: int = 0
    instance_id: str = None


def create_instances(classroom_size, config_name, session_id, coach, region_name):
    if classroom_size <= 1:
        dns_name = f"{config_name}-{session_id}.codekata.proagile.link"
        return [ProjectorInstance(config_name, dns_name, coach, region_name)]
    else:
        instances = []
        for i in range(classroom_size):
            room = i + 1
            dns_name = f"{config_name}-{session_id}-{room}.codekata.proagile.link"
            instance = ProjectorInstance(config_name, dns_name, coach, region_name, room)
            instances.append(instance)
        return instances


def write_classroom_file(f, instances):
    writer = csv.DictWriter(f, ["room", "region", "id", "url", "team", "comments"])
    writer.writeheader()
    for instance in instances:
        writer.writerow({
            "room": instance.room,
            "region": instance.region_name,
            "id": instance.instance_id,
            "url": f"https://{instance.dns_name}",
            "team": "",
            "comments": ""
        })


@click.command()
@click.option(
    "--config-name",
    help="normally the shortname for the IDE like pycharm or idea",
    prompt=f"what config [{', '.join(read_ide_config())}]?"
)
@click.option(
    "--region-name",
    help=f"the aws region name (default eu-north-1): {', '.join(read_regions_config().keys())}",
    default="eu-north-1"
)
@click.option(
    "--aws-profile",
    default=None,
    help="the aws profile, if you dont use the default"
)
@click.option(
    "--classroom-size",
    default=0,
    help="if larger then 0 then it will create a classroom file, which is a csv file that can be used for other "
         "commands and as a signup sheet "
)
def summon(config_name, region_name, aws_profile, classroom_size):
    coach = os.getlogin()
    session_id = secrets.token_hex(4)
    instances = create_instances(classroom_size, config_name, session_id, coach, region_name)

    session = boto3.Session(profile_name=aws_profile, region_name=region_name)
    ec2 = session.client("ec2")
    for projector_instance in instances:
        summon_projector_instance(ec2, projector_instance)

    if len(instances) > 1:
        filename = f"{session_id}-classroom.csv"
        print(f"creating classroom file: {filename}")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            write_classroom_file(f, instances)

    print("Updating DNS records...")
    # Hack: we're simply guessing the new machine has been created here.
    # A better/more stable/quicker solution would be to check with AWS when the machine is up,
    # and update DNS then.
    # Inspiration:
    #    for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
    #    response = ec2.monitor_instances(InstanceIds=['INSTANCE_ID'])
    #    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Waiter.InstanceRunning
    time.sleep(15)
    update_dns.Doer().doit()


def summon_projector_instance(ec2, projector_instance: ProjectorInstance):
    tags = [
        {'Key': 'Name', 'Value': projector_instance.dns_name},
        {'Key': 'SammanCoach', 'Value': projector_instance.coach},
    ]
    machine_config = read_ide_config()[projector_instance.config_name]
    note = None
    if 'note' in machine_config:
        note = machine_config['note']
        del machine_config['note']
    user_data = generate_script(
        projector_instance.dns_name,
        **machine_config,
    )
    instance = launch_instance(ec2, tags, user_data, projector_instance.region_name)
    if note:
        print("-=-=- NOTE -=-=-\n" + note)
    # set the instance_id in the ProjectorInstance now that we have it
    projector_instance.instance_id = instance["InstanceId"]


def launch_instance(ec2, tags, user_data, region_name):
    region_config = read_regions_config()[region_name]
    response = ec2.run_instances(
        MinCount=1,
        MaxCount=1,
        ImageId=region_config["image_id"],  # old "ami-0ed17ff3d78e74700"
        InstanceType="t3.large",
        KeyName=region_config["key_name"],
        SecurityGroupIds=region_config["security_group_ids"],  # old "sg-0eec46ebc5e138c72"
        UserData=user_data,
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': tags}],
        BlockDeviceMappings=[{
            'DeviceName': "/dev/sda1",
            'Ebs':
            {
                'DeleteOnTermination': True,
                'VolumeType': 'gp2',
                'VolumeSize': 16,
            }
        }]
    )
    return response['Instances'][0]


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    summon()
