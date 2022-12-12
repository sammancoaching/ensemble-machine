import io
import json

from approvaltests import verify, verify_all

from summon import write_classroom_file, create_instances, ProjectorInstance, generate_script, read_ide_config, \
    read_regions_config


def test_create_several_instances():
    session_id = "c7f3aa50"
    config_name = "idea"
    region_name = "ca-central-1"
    coach = "emily"

    instances = create_instances(2, config_name, session_id, coach, region_name)
    verify_all("instances", instances)


def test_create_instance():
    session_id = "c7f3aa50"
    config_name = "idea"
    region_name = "ca-central-1"
    coach = "emily"
    
    instances = create_instances(1, config_name, session_id, coach, region_name)
    verify_all("instances", instances)


def test_write_classroom():
    f = io.StringIO()
    config_name = "idea"
    dns_name = "c7f3aa50-1-idea.codekata.proagile.link"
    region_name = "ca-central-1"
    coach = "emily"
    
    instances = [
        ProjectorInstance(config_name, dns_name, coach, region_name, room=1),
        ProjectorInstance(config_name, dns_name, coach, region_name, room=2),
    ]
    write_classroom_file(f, instances)
    
    verify(f.getvalue())


def test_generate_script():
    dns_name = "c7f3aa50-1-idea.codekata.proagile.link"
    machine_config = read_ide_config()["idea"]

    script = generate_script(dns_name, **machine_config)

    verify(script)


def test_read_config(tmp_path):
    p = tmp_path / "ide_config.json"
    config = """\
{
    "clion": {
        "config_name": "clion",
        "name": "CLion 2021.2",
        "extra_packages": ["openjdk-17-jdk"],
        "snap_packages": [],
        "environment": {"DOTNET_ROOT": "/snap/dotnet-sdk/current"}
    }
}
"""
    p.write_text(config)

    configs = read_ide_config(p)

    assert list(configs.keys()) == ["clion"]
    assert list(configs["clion"].keys()) == ["config_name", "name", "extra_packages", "snap_packages", "environment"]
    assert list(configs["clion"]["extra_packages"]) == ["openjdk-17-jdk"]
    assert dict(configs["clion"]["environment"]) == {"DOTNET_ROOT": "/snap/dotnet-sdk/current"}


def test_read_aws_regions(tmp_path):
    p = tmp_path / "aws_zones.json"
    config = """\
{
    "eu-central-1": {
        "image_id": "ami-05f7491af5eef733c",
        "security_group_ids": ["sg-0d66d1b4ba3786ff3"],
        "key_name": "pem-eu-central-1"
    }
}
"""
    p.write_text(config)

    region_config = read_regions_config(config=p)

    assert list(region_config.keys()) == ["eu-central-1"]
    assert list(region_config["eu-central-1"].keys()) == ["image_id", "security_group_ids", "key_name"]
    assert list(region_config["eu-central-1"]["security_group_ids"]) == ["sg-0d66d1b4ba3786ff3"]
