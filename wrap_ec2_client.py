import logging

import boto3


class InstancesManager:
    def __init__(self, aws_defaults, aws_regions, profile_name=None):
        self.log = logging.getLogger(__name__)

        self.ec2_region_clients = []
        for region in aws_regions:
            region_session = boto3.Session(profile_name=profile_name, region_name=region)
            region_client = region_session.client("ec2")
            self.ec2_region_clients.append(region_client)

        self.url_stem = aws_defaults["url_stem"]

    def list_machines_and_addresses(self):
        parser = InstanceDataParser(self.url_stem)
        for ec2_client in self.ec2_region_clients:
            result = ec2_client.describe_instances()
            yield from parser.machine_from_instance_description(result)

    def stop_all_machines(self):
        parser = InstanceDataParser(self.url_stem)
        for ec2_client in self.ec2_region_clients:
            result = ec2_client.describe_instances()
            machines = [id for id, name, ip in parser.machine_from_instance_description(result)]
            if machines:
                ec2_client.stop_instances(InstanceIds=machines)

    def start_machine(self, name):
        parser = InstanceDataParser(self.url_stem)
        for ec2_client in self.ec2_region_clients:
            result = ec2_client.describe_instances()
            machines = [id for id, name in parser.machine_with_name(result, name)]
            if machines:
                ec2_client.start_instances(InstanceIds=machines)


class InstanceDataParser:
    def __init__(self, url_stem):
        self.log = logging.getLogger(__name__)
        self.url_stem = url_stem

    def machine_from_instance_description(self, instance_description):
        reservations = instance_description["Reservations"]
        for reservation in reservations:
            for instance in reservation["Instances"]:
                name = self._extract_name_tag(instance)
                self.log.debug(f"Discovered instance with name {name}")
                instance_id = self._extract_instance_id(instance)
                if self.url_stem in name:
                    if "PublicIpAddress" in instance:
                        ip_address = instance["PublicIpAddress"]
                        self.log.info(f"found machine {name} with public ip address {ip_address}")
                        yield instance_id, name, ip_address
                    else:
                        self.log.debug(f"found machine {name} but no public ip address - probably stopped")

    def machine_with_name(self, instance_description, search_name):
        reservations = instance_description["Reservations"]
        for reservation in reservations:
            for instance in reservation["Instances"]:
                name = self._extract_name_tag(instance)
                self.log.debug(f"Discovered instance with name {name}")
                instance_id = self._extract_instance_id(instance)
                if search_name in name:
                    yield instance_id, name


    def _extract_name_tag(self, instance):
        try:
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    name_tag = tag["Value"]
                    self.log.debug(f"found machine with name {name_tag}")
                    return name_tag
        except KeyError as ke:
            self.log.error(f"couldn't find Name Tag for machine {instance}", ke)
            return "unknown"

    def _extract_instance_id(self, instance):
        try:
            id_tag = instance["InstanceId"]
            self.log.debug(f"found machine with id {id_tag}")
            return id_tag
        except KeyError as ke:
            self.log.error(f"couldn't find id for machine {instance}", ke)
            return "unknown"
