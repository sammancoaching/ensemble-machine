#!/usr/bin/env python3

"""
Use this script to shut down all currently running instances
"""
import logging

import click

from update_dns import InstancesManager


@click.command()
@click.option(
    "--aws-profile",
    default="default",
    help="the aws profile"
)
def main(aws_profile):
    logging.basicConfig(level=logging.INFO)

    from summon import read_aws_defaults, read_regions_config
    aws_defaults = read_aws_defaults(profile_name=aws_profile)
    regions = read_regions_config(profile_name=aws_profile).keys()
    manager = InstancesManager(aws_defaults, regions, profile_name=aws_profile)
    manager.stop_all_machines()


if __name__ == '__main__':
    main()
