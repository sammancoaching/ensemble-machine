#!/usr/bin/env python3

"""
When an ensemble machine starts or is restarted, the IP address changes.
The DNS record must be updated to point at the new IP, and that's what this script does.

You should run this script by hand whenever you restart ensemble machines.
"""
import logging

import boto3
import click

from wrap_ec2_client import InstancesManager


class DnsUpdater:
    def __init__(self, aws_defaults, aws_regions, profile_name=None):
        """ A DnsUpdater can change records in Route53 so that you get a human-readable url for your ensemble machines.
        Arguments:
        - aws_defaults - usually read from the file 'aws_machine_spec.json'.
        - aws_regions - usually the keys from the 'aws_zones.json' - all the ec2 regions where you have machines whose dns records should be updated.
        - profile_name - the AWS profile to use for credentials for boto3. Your profile names are usually listed in the file ~/.aws/credentials
         """
        self.log = logging.getLogger(__name__)

        self.instance_manager = InstancesManager(aws_defaults, aws_regions, profile_name)
        session = boto3.Session(profile_name=profile_name, region_name=aws_defaults["region"])
        self.route53 = session.client("route53")
        self.hosted_dns_zone_name = aws_defaults["hosted_dns_zone_name"]
        self._pa_link_zone_id = aws_defaults.get("hosted_dns_zone_id", None)

    def update_ensemble_machine_dns_records(self):
        for _, machine, ipv4 in self.instance_manager.list_machines_and_addresses():
            self.update_dns_record(machine, ipv4)

    def update_dns_record(self, machine, ipv4):
        change_data = {
            'Comment': 'DNS update for ensemble machine via script',
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': machine,
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [{
                        'Value': ipv4
                    }]
                }
            }]
        }
        self.route53.change_resource_record_sets(HostedZoneId=self.hosted_zone_id(), ChangeBatch=change_data)
        self.log.debug(f"Updated DNS info for {machine}")


    def hosted_zone_id(self):
        """ Use the route53 api to look up the hosted zone for this domain name.
        Store it in a class member variable so we only do the lookup once.
        If you prefer, you can specify the zone id in the aws_machine_spec under the key 'hosted_dns_zone_id' and avoid this lookup.
        """
        if self._pa_link_zone_id is None:
            result = self.route53.list_hosted_zones()
            for zone in result["HostedZones"]:
                if zone["Name"] == self.hosted_dns_zone_name:
                    self._pa_link_zone_id = zone["Id"]
                    self.log.debug(f"Using AWS Hosted Zone: {self._pa_link_zone_id}")
                    break
        if self._pa_link_zone_id is None:
            raise Exception(f"Couldn't find Zone ID for {self.hosted_dns_zone_name} - no work can be done")
        return self._pa_link_zone_id


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
    DnsUpdater(aws_defaults, regions, profile_name=aws_profile).update_ensemble_machine_dns_records()


if __name__ == '__main__':
    main()
