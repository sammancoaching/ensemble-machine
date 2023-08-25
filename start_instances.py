#!/usr/bin/env python3

"""
Use this script to start a particular instance by name
"""

import logging

import click

from wrap_ec2_client import InstancesManager


@click.command()
@click.option(
    "--aws-profile",
    default="default",
    help="the aws profile"
)
@click.option(
    "--name",
    default="default",
    help="the name of the machine to start"
)
def main(aws_profile, name):
    logging.basicConfig(level=logging.INFO)

    from summon import read_aws_defaults, read_regions_config
    aws_defaults = read_aws_defaults(profile_name=aws_profile)
    regions = read_regions_config(profile_name=aws_profile).keys()
    manager = InstancesManager(aws_defaults, regions, profile_name=aws_profile)
    manager.start_machine(name)

if __name__ == '__main__':
    main()