import datetime
import logging

from dateutil.tz import tzutc

from update_dns import InstanceDataParser


def test_parse_machine_description():
    parser = InstanceDataParser("codekata.proagile.link")
    machine_descriptions = parser.machine_from_instance_description(
        {
            "Reservations": [
                {"Instances": [
                    {
                        'InstanceId': 'i-020c4b1dfded43572',
                        "Tags": [{"Key": "Name", "Value": "rider-1234.codekata.proagile.link"}],
                        "PublicIpAddress": "10.2.3.4"
                    }
                ]}
            ]
        }
    )
    assert list(machine_descriptions) == [('i-020c4b1dfded43572', "rider-1234.codekata.proagile.link", "10.2.3.4")]


def test_parse_instance_id():
    instance_description = {
        "Reservations": [
            {"Instances": [
                {'AmiLaunchIndex': 0, 'ImageId': 'ami-03e08697c325f02ab', 'InstanceId': 'i-020c4b1dfded43572',
                 "PublicIpAddress": "10.2.3.4", 'InstanceType': 't3.large', 'KeyName': 'BC-eu-central-1',
                 'LaunchTime': datetime.datetime(2023, 6, 20, 7, 29, 1, tzinfo=tzutc()),
                 'Monitoring': {'State': 'disabled'},
                 'Placement': {'AvailabilityZone': 'eu-central-1c', 'GroupName': '', 'Tenancy': 'default'},
                 'PrivateDnsName': 'ip-172-31-43-177.eu-central-1.compute.internal',
                 'PrivateIpAddress': '172.31.43.177',
                 'ProductCodes': [], 'PublicDnsName': '', 'State': {'Code': 80, 'Name': 'stopped'},
                 'StateTransitionReason': 'User initiated (2023-06-21 06:33:00 GMT)', 'SubnetId': 'subnet-b5efdfff',
                 'VpcId': 'vpc-62211b0b', 'Architecture': 'x86_64',
                 'BlockDeviceMappings': [{'DeviceName': '/dev/sda1', 'Ebs': {
                     'AttachTime': datetime.datetime(2023, 5, 29, 11, 24, 7, tzinfo=tzutc()),
                     'DeleteOnTermination': True,
                     'Status': 'attached', 'VolumeId': 'vol-03eb629842b53d6fe'}}],
                 'ClientToken': 'a8cf036e-3b01-4b9b-a2d0-0e6c83bf2157', 'EbsOptimized': False, 'EnaSupport': True,
                 'Hypervisor': 'xen', 'NetworkInterfaces': [{'Attachment': {
                    'AttachTime': datetime.datetime(2023, 5, 29, 11, 24, 6, tzinfo=tzutc()),
                    'AttachmentId': 'eni-attach-0fd028009ffd863a9', 'DeleteOnTermination': True, 'DeviceIndex': 0,
                    'Status': 'attached', 'NetworkCardIndex': 0}, 'Description': '', 'Groups': [
                    {'GroupName': 'ensemble-machine', 'GroupId': 'sg-04605e09015e51109'}], 'Ipv6Addresses': [],
                    'MacAddress': '0a:b0:85:a6:25:36',
                    'NetworkInterfaceId': 'eni-0d53b5aecc79cf254',
                    'OwnerId': '257441429373',
                    'PrivateDnsName': 'ip-172-31-43-177.eu-central-1.compute.internal',
                    'PrivateIpAddress': '172.31.43.177', 'PrivateIpAddresses': [
                        {'Primary': True, 'PrivateDnsName': 'ip-172-31-43-177.eu-central-1.compute.internal',
                         'PrivateIpAddress': '172.31.43.177'}], 'SourceDestCheck': True, 'Status': 'in-use',
                    'SubnetId': 'subnet-b5efdfff', 'VpcId': 'vpc-62211b0b',
                    'InterfaceType': 'interface'}], 'RootDeviceName': '/dev/sda1',
                 'RootDeviceType': 'ebs',
                 'SecurityGroups': [{'GroupName': 'ensemble-machine', 'GroupId': 'sg-04605e09015e51109'}],
                 'SourceDestCheck': True, 'StateReason': {'Code': 'Client.UserInitiatedShutdown',
                                                          'Message': 'Client.UserInitiatedShutdown: User initiated shutdown'},
                 'Tags': [{'Key': 'Name', 'Value': 'clion-74a6cfa0-3.codekata.bacheconsulting.link'},
                          {'Key': 'SammanCoach', 'Value': 'Samman'}], 'VirtualizationType': 'hvm',
                 'CpuOptions': {'CoreCount': 1, 'ThreadsPerCore': 2},
                 'CapacityReservationSpecification': {'CapacityReservationPreference': 'open'},
                 'HibernationOptions': {'Configured': False},
                 'MetadataOptions': {'State': 'applied', 'HttpTokens': 'optional', 'HttpPutResponseHopLimit': 1,
                                     'HttpEndpoint': 'enabled'}, 'EnclaveOptions': {'Enabled': False}
                 }
            ]
            }
        ]
    }
    parser = InstanceDataParser("codekata.bacheconsulting.link")
    machine_descriptions = parser.machine_from_instance_description(instance_description)
    assert list(machine_descriptions) == [('i-020c4b1dfded43572',
                                           'clion-74a6cfa0-3.codekata.bacheconsulting.link',
                                           '10.2.3.4')]
