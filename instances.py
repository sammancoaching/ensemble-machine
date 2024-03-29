#!/usr/bin/env python3
import datetime
import json
from dataclasses import dataclass
from pathlib import Path

import boto3
import click

from summon import read_regions_config, read_aws_defaults

@dataclass
class RunningInstance:
    ip_address: str
    state: str
    coach: str
    url: str
    creation_date: str
    region_name: str


@click.command()
@click.option(
    "--region-name",
    help=f"the aws region name (default eu-north-1): {', '.join(read_regions_config().keys())}",
    default="eu-north-1"
)
@click.option(
    "--aws-profile",
    default="default",
    help="the aws profile, if you dont use the default"
)
@click.option(
    "--coach",
    help="only show instances owned by this person",
)
def main(region_name, aws_profile, coach=None):
    instances = all_instances(region_name, aws_profile)
    if coach:
        instances = [instance for instance in instances if instance.coach.strip() == coach]
    print('\n'.join(print_instances(instances)))


def all_instances(region_name, aws_profile):
    url_stem = read_aws_defaults(profile_name=aws_profile)["url_stem"]
    instances = []
    if region_name == "all":
        all_regions = read_regions_config(profile_name=aws_profile).keys()
        for region_name in all_regions:
            response = get_sammancoach_machines(region_name, aws_profile)
            instances.extend(instances_from_response(response, url_stem))
    else:
        response = get_sammancoach_machines(region_name, aws_profile)
        instances.extend(instances_from_response(response, url_stem))

    return instances


def print_instances(instances):
    rows = []
    for instance in instances:
        rows.append(print_instance(instance))
    return rows


def get_sammancoach_machines(region_name, aws_profile):
    session = boto3.Session(profile_name=aws_profile, region_name=region_name)
    client = session.client('ec2')
    custom_filter = [{
        'Name': 'tag:SammanCoach',
        'Values': ['*']}]
    response = client.describe_instances(Filters=custom_filter)
    return response


def instances_from_response(obj, url_stem):
    machines = []
    for reservation in obj['Reservations']:
        for instance in reservation['Instances']:
            tags = instance['Tags']
            public_ip = instance.get("PublicIpAddress", "not available")
            attach_time = try_find_attach_time(instance)
            attach_time_short = attach_time.partition('T')[0] if attach_time else '-'
            machine_data = {
                "State": instance["State"]["Name"],
                "IP": public_ip,
                "AttachTime": attach_time_short,
                "Placement": instance['Placement']['AvailabilityZone'],
            }
            for machine in tags:
                key = machine['Key']
                value = machine['Value']
                machine_data[key] = value
            machines.append(machine_data)
    instances = []

    for machine in machines:
        if url_stem in machine['Name']:
            instance = RunningInstance(ip_address=f"{machine['IP']:16}",
                                       state=f"{machine['State']:12}",
                                       coach=f"{machine['SammanCoach']:12}",
                                       url=f"https://{machine['Name']:42}",
                                       creation_date=f"{machine['AttachTime']}",
                                       region_name=machine['Placement'],
                                       )
            instances.append(instance)
    return instances


def print_instance(instance: RunningInstance):
    return f"{instance.ip_address} {instance.state} {instance.coach} {instance.url} {instance.creation_date} {instance.region_name}"


def try_find_attach_time(instance):
    try:
        time_value = instance["BlockDeviceMappings"][0]["Ebs"]["AttachTime"]
        if isinstance(time_value, datetime.datetime):
            return time_value.isoformat()
        else:
            return time_value
    except:
        return None


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    main()
