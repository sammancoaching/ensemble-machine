from update_dns import DnsUpdater


def test_parse_machine_description():
    updater = DnsUpdater({"url_stem": "codekata.proagile.link", "hosted_dns_zone_name": "proagile.link"},
                         ["eu-north-1"])
    machine_descriptions = updater.machine_from_response(
        {
            "Reservations": [
                {"Instances": [
                    {
                        "Tags": [{"Key": "Name", "Value": "rider-1234.codekata.proagile.link"}],
                        "PublicIpAddress": "10.2.3.4"
                    }
                ]}
            ]
        }
    )
    assert list(machine_descriptions) == [("rider-1234.codekata.proagile.link", "10.2.3.4")]
