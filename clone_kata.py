#!/usr/bin/env python3

import click
import os
from fabric import Connection
from dataclasses import dataclass
import csv

from instances import all_instances
from summon import read_regions_config, read_aws_defaults


@dataclass
class KataMachine:
    region_name: str
    host_ip: str
    url: str


def read_classroom_file(file, running_instances):
    result = []
    reader = csv.DictReader(file)
    for row in reader:
        url = row["url"]
        region_name = row["region"]
        matching_instances = [machine for machine in running_instances if machine.url.strip() == url.strip()]
        if matching_instances:
            instance = matching_instances[0]
            machine = KataMachine(url=url, region_name=region_name, host_ip=instance.ip_address)
            result.append(machine)
        
    return result


def clone_kata_commandline(kata):
    return f"""
                sudo -u typist -- sh -c '\
                   cd /home/typist
                   mkdir -p katas;\
                   cd katas;\
                   git clone {kata}
                '\
              """


@click.command()
@click.option(
    "--kata",
    help="the kata to clone",
    default="https://github.com/emilybache/starter.git",
    prompt=f"what kata repo?"
)
@click.option(
    "--region-name",
    help=f"the aws region name (default eu-north-1): {', '.join(read_regions_config().keys())}",
    default="eu-north-1"
)
@click.option(
    "--aws-profile",
    default=None,
    help="the aws profile, if you don't use the default"
)
@click.option(
    "--host_ip",
    help="the ip address",
)
@click.option(
    "--coach",
    help="add the kata to all running instances owned by this person",
)
@click.option(
    "--classroom",
    help="add the kata to all running instances in this classroom file",
)
def clone_kata(kata, region_name, aws_profile, host_ip, coach, classroom):
    commandline = clone_kata_commandline(kata)
    aws_defaults = read_aws_defaults(profile_name=aws_profile)
    url_stem = aws_defaults["url_stem"]
    machines = determine_machines_to_update(aws_profile, classroom, coach, host_ip, region_name, url_stem)
    logging.getLogger().info(f"will clone kata to machines: {[m.url for m in machines]}")
    run_commandline_on_machines(commandline, machines, aws_profile)


def run_commandline_on_machines(commandline, machines, aws_profile):
    for m in machines:
        try:
            print(f"will run remote commands on {m}")
            c = connect_to_machine(m, aws_profile)
            c.run(commandline)
        except Exception as e:
            print("unexpected problem running remote commands on machine ", m, e)


def connect_to_machine(machine, aws_profile):
    key_name = read_regions_config(profile_name=aws_profile)[machine.region_name]["key_name"]
    key_file = os.path.expanduser(f"~/.ssh/{key_name}.pem")
    c = Connection(host=machine.host_ip.strip(), user='ubuntu', connect_kwargs={
        "key_filename": key_file,
    }, )
    return c


def determine_machines_to_update(aws_profile, classroom, coach, host_ip, region_name, url_stem):
    running_instances = [machine for machine in all_instances(region_name, aws_profile) if
                         machine.state.strip() == "running"]
    if not running_instances:
        logging.getLogger().error(f"No running instances found in region {region_name}")
        return []
    if host_ip:
        instance = [machine for machine in running_instances if host_ip in machine.ip_address]
        if not instance:
            print(f"ERROR: host ip {host_ip} is not running")
            machines = []
        else:
            machines = [KataMachine(host_ip=host_ip, region_name=region_name, url=instance[0].url)]
    elif coach:
        running_instances = [machine for machine in running_instances if machine.coach.strip() == coach]
        machines = [KataMachine(host_ip=machine.ip_address, region_name=region_name, url=machine.url) for machine in
                    running_instances]
    elif classroom:
        with open(classroom, 'r', newline="", encoding="utf-8") as f:
            machines = read_classroom_file(f, running_instances)
    else:
        machines = [KataMachine(host_ip=machine.ip_address, region_name=region_name, url=machine.url) for machine in
                    running_instances if url_stem in machine.url]
    return machines


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    clone_kata()
