#!/usr/bin/env python3

"""
When an EC2 machine starts, it should make an HTTPs request to this lambda.
This lambda function will list all machines in EC2, take the public IPv4 address and update
the corresponding record in Route53.

This allows for a machine to reboot, get a new IPv4 address but still have a working DNS record.
"""
import logging

import boto3


class Doer:
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.route53 = boto3.client("route53")
        self.ec2s = [
            boto3.client('ec2', region_name='eu-north-1'),
            boto3.client('ec2', region_name='eu-central-1'),
            boto3.client('ec2', region_name='ca-central-1'),
            boto3.client('ec2', region_name='ap-south-1'),
            boto3.client('ec2', region_name='eu-west-2'),        
            ]
        self._pa_link_zone_id = None

    def doit(self):
        for machine, ipv4 in self._list_machines_and_addresses():
            self.update_dns_record(machine, ipv4)
            
    def _list_machines_and_addresses(self):
        for ec2 in self.ec2s:
            result = ec2.describe_instances()
            reservations = result["Reservations"]
            for reservation in reservations:
                for instance in reservation["Instances"]:
                    self.log.debug(f"Discovered instance {instance}")
                    name = self._extract_name_tag(instance)
                    if "codekata.proagile.link" in name:
                        if "PublicIpAddress" in instance:
                            yield name, instance["PublicIpAddress"]
            

    def _extract_name_tag(self, instance):
        try:
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    return tag["Value"]
        except KeyError as ke:
                print(f"couldn't find Name Tag for machine {instance}", ke)
                return "unknown"


    def update_dns_record(self, machine, ipv4):
        change_data = {
            'Comment': 'Automatic update from codekata lambda',
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
        self.log.info(f"Ready to update {machine} to point to {ipv4}")
        self.route53.change_resource_record_sets(HostedZoneId=self.doitx(), ChangeBatch=change_data)
        self.log.info(f"Updated {machine}")

    def doitx(self):
        if self._pa_link_zone_id is None:
            result = self.route53.list_hosted_zones()
            for zone in result["HostedZones"]:
                if zone["Name"] == "proagile.link.":
                    self._pa_link_zone_id = zone["Id"]
                    self.log.debug(f"Using AWS Hosted Zone: {self._pa_link_zone_id}")
                    break
        if self._pa_link_zone_id is None:
            raise Exception("Couldn't find Zone ID for proagile.link - no work can be done")
        return self._pa_link_zone_id


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Doer().doit()
