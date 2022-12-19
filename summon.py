#!/usr/bin/env python3
import logging
import csv
import json
import os
import pathlib
import secrets
import time

import boto3
import click
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)

from update_dns import DnsUpdater


def read_ide_config(config=None):
    """ ide_config.json contains details of how to install software and configure projector for each kind of IDE you want to be able to summon. """
    config = config or pathlib.Path().resolve() / "ide_config.json"
    if not config.exists():
        logging.warning("missing ide_config.json file, expected to be in current working directory")
        return {}
    with open(config) as f:
        configs = json.load(f)
        for key in configs.keys():
            configs[key]["config_name"] = key
        return configs


def read_regions_config(config=None, profile_name="default"):
    """ aws_zones.json contains dictionaries for each aws zone you want to be able to summon instances in. """
    config = config or pathlib.Path().resolve() / "aws_zones.json"
    assert config.exists(), "missing aws_zones.json file, expected to be in current working directory"
    with open(config) as f:
        regions_config = json.load(f)
        return regions_config[profile_name]


def read_aws_defaults(config=None, profile_name="default"):
    """ aws_defaults are values that are set the same for all regions """
    config = config or pathlib.Path().resolve() / "aws_machine_spec.json"
    assert config.exists(), "missing aws_machine_spec.json file, expected to be in current working directory"
    with open(config) as f:
        aws_defaults = json.load(f)
        return aws_defaults[profile_name]


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


def create_instances(classroom_size, config_name, session_id, coach, region_name, url_stem):
    if classroom_size <= 1:
        dns_name = f"{config_name}-{session_id}.{url_stem}"
        return [ProjectorInstance(config_name, dns_name, coach, region_name)]
    else:
        instances = []
        for i in range(classroom_size):
            room = i + 1
            dns_name = f"{config_name}-{session_id}-{room}.{url_stem}"
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
    help=f"the aws region name: {', '.join(read_regions_config().keys())}",
    default=None
)
@click.option(
    "--aws-profile",
    default=None,
    help="the aws profile, if you don't use the default"
)
@click.option(
    "--classroom-size",
    default=0,
    help="How many machines to create "
)
@click.option(
    "--coach",
    default="Samman",
    help="The name of the Samman Coach who owns these instances"
)
def summon(config_name, region_name, aws_profile, classroom_size, coach):
    coach = coach or os.getlogin()
    session_id = secrets.token_hex(4)
    aws_defaults = read_aws_defaults(profile_name=aws_profile)

    region_name = region_name or aws_defaults["region"]
    instances = create_instances(classroom_size, config_name, session_id, coach, region_name, aws_defaults["url_stem"])

    session = boto3.Session(profile_name=aws_profile, region_name=region_name)
    ec2 = session.client("ec2")
    for projector_instance in instances:
        summon_projector_instance(ec2, projector_instance, profile_name=aws_profile, aws_defaults=aws_defaults)

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
    aws_regions = read_regions_config(profile_name=aws_profile).keys()
    DnsUpdater(aws_defaults, aws_regions).update_ensemble_machine_dns_records()


def summon_projector_instance(ec2, projector_instance: ProjectorInstance, profile_name, aws_defaults):
    machine_config = read_ide_config()[projector_instance.config_name]
    user_data = generate_script(
        projector_instance.dns_name,
        **machine_config,
    )
    tags = [
        {'Key': 'Name', 'Value': projector_instance.dns_name},
        {'Key': aws_defaults["coach_tag"], 'Value': projector_instance.coach},
    ]
    instance = launch_instance(ec2, tags, user_data, projector_instance.region_name, profile_name, aws_defaults)

    # set the instance_id in the ProjectorInstance now that we have it
    projector_instance.instance_id = instance["InstanceId"]


def launch_instance(ec2, tags, user_data, region_name, profile_name, aws_defaults):
    region_config = read_regions_config(profile_name=profile_name)[region_name]
    response = ec2.run_instances(
        MinCount=1,
        MaxCount=1,
        ImageId=region_config["image_id"],
        InstanceType= aws_defaults["instance_type"],
        KeyName=region_config["key_name"],
        SecurityGroupIds=region_config["security_group_ids"],
        UserData=user_data,
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': tags}],
        BlockDeviceMappings=[{
            'DeviceName': "/dev/sda1",
            'Ebs':
            {
                'DeleteOnTermination': True,
                'VolumeType': aws_defaults["volume_type"],
                'VolumeSize': aws_defaults["volume_size"],
            }
        }]
    )
    return response['Instances'][0]


if __name__ == "__main__":
    summon()
