#! python
import csv

import boto3
import click
import summon as summon_module
from instances import get_sammancoach_machines


@click.group()
def cli():
    pass


@cli.command()
@click.argument("classroom")
def terminate(classroom):
    yes = click.prompt("are you sure? [y/N] ")
    if yes == "y":
        boto3.client("ec2").terminate_instances(InstanceIds=(ids_in_classroom(classroom)))


@cli.command()
@click.argument("classroom")
def stop(classroom):
    boto3.client("ec2").stop_instances(InstanceIds=(ids_in_classroom(classroom)))


@cli.command()
@click.argument("classroom")
def start(classroom):
    boto3.client("ec2").start_instances(InstanceIds=(ids_in_classroom(classroom)))


@cli.command()
@click.argument("classroom")
def ids(classroom):
    print(ids_in_classroom(classroom))


def ids_in_classroom(classroom):
    with open(classroom, "r", newline="") as f:
        reader = csv.DictReader(f)
        ids = [row["id"] for row in reader]
    return ids


if __name__ == '__main__':
    cli()
