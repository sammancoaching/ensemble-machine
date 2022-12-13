#!/usr/bin/env python3

import click

from clone_kata import determine_machines_to_update, run_commandline_on_machines
from summon import region_configs


def download_plugin_commandline(plugin):
    return f"""\
sudo -u typist -- sh -c '\
   cd /home/typist
   curl '{plugin}' -o plugin_archive.zip
'\
"""


@click.command()
@click.option(
    "--plugin",
    help="the plugin to download",
    default="https://plugins.jetbrains.com/plugin/download?rel=true&updateId=169164",
    prompt=f"what download url?"
)
@click.option(
    "--region-name",
    help=f"the aws region name (default eu-north-1): {', '.join(region_configs.keys())}",
    default="eu-north-1"
)
@click.option(
    "--aws-profile",
    default=None,
    help="the aws profile, if you dont use the default"
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
def download_plugin(plugin, region_name, aws_profile, host_ip, coach, classroom):
    commandline = download_plugin_commandline(plugin)
    machines = determine_machines_to_update(aws_profile, classroom, coach, host_ip, region_name)
    run_commandline_on_machines(commandline, machines, aws_profile)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    download_plugin()
