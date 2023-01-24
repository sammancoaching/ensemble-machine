from io import StringIO

from approvaltests import verify_all

from clone_kata import read_classroom_file, KataMachine
from instances import RunningInstance


def test_read_classroom_file():
	classroom_file = """\
room,region,id,url,team,comments
1,ca-central-1,i-0bd2b004ba4473c6e,https://c7f3aa50-1-idea.codekata.proagile.link,,
2,ca-central-1,i-07f1241bff8f0d1ee,https://c7f3aa50-2-idea.codekata.proagile.link,,
"""
	f = StringIO(classroom_file)
	result = read_classroom_file(f, running_instances=[
		RunningInstance("18.157.73.25", "running", "emily", "https://c7f3aa50-1-idea.codekata.proagile.link", "2022-01-31", region_name="eu-north-1"),
		RunningInstance("18.157.73.26", "running", "emily", "https://c7f3aa50-2-idea.codekata.proagile.link", "2022-01-31", region_name="eu-north-1"),
	])

	verify_all("machines", result)