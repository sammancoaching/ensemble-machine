import datetime
import json
from pathlib import Path

from approvaltests import verify, verify_all

from instances import get_sammancoach_machines, RunningInstance, print_instance, \
    instances_from_response

SAMPLE_RESPONSE = Path('tests/response.json')


def test_instance_list_report():
    # To update the sample response (boto3/ec2 API changes)
    # run this test as a script in repo root:
    #     PYTHONPATH=. python tests/test_instances.py
    # That will overwrite the sample response file with a fresh response
    sample_response = SAMPLE_RESPONSE.read_text(encoding='utf8')
    output = instance_report_from_response(sample_response)
    verify_all('instances', output)


def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def instance_report_from_response(json_response):
    obj = json.loads(json_response)
    return instances_from_response(obj, "codekata.proagile.link")


def save_new_response_json():
    response_obj = get_sammancoach_machines("eu-north-1", None)
    response_json = json.dumps(response_obj, default=datetime_handler)
    SAMPLE_RESPONSE.write_text(response_json, encoding='utf8')


def test_print_instance():
    instance = RunningInstance("18.157.73.25", "running", "emily", "99daacf1-rider.codekata.proagile.link", "2022-01-31", region_name="eu-north-1")
    verify(print_instance(instance))

if __name__ == '__main__':
    save_new_response_json()
