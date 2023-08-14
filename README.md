# Ensemble Machine
Support scripts for Samman Coaches to provision practice machines on AWS EC2. This is useful for technical coaches who want participants to be able to very quickly get up and running writing code and unit tests in an exercise without having to install anything at all on their local machine.

## Create a new practice machine that uses JetBrains Projector
Use this script:

    python summon.py --help

This script can create machines that use [JetBrains Projector](https://lp.jetbrains.com/projector/) so you can code in an IDE in a web browser without installing anything locally. 

## List all the instances you have created
Use this script:

    $ python instances.py --help

This should list all the machines you have started, and the urls your participants can use to access them.

## Clone a code kata repo to a machine
Use this script:

    python clone_kata.py --help

This is a convenience for copying the same kata starting position to all your machines. You will still need to go in by hand on each machine and navigate the IDE to open the relevant folder.

## Shut down all machines
Use the script:

    ./shutdown.py

If you want to only shut down a few machines rather than all, use the AWS console to change the state to "stopped". 

# Initial Setup
Before these scripts will work you will need:
* an account on AWS
* AWS user with credentials for programmatic access to ec2 and route53
* a aws_machine_spec.json file specifying default settings for machines in all regions.
* a aws_zones.json file specifying pem file, images and security groups for each AWS region you want to use.
* a DNS name your machines can use in their urls.

The sections below go through all these items in turn.

### AWS user with credentials for programmatic access
These scripts use a [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html) client to update your AWS configuration. The user should have access to both ec2 and route53. You set up new users in the "IAM" part of AWS. I created a UserGroup for my user with permissions:

* AmazonEC2FullAccess
* AmazonRoute53FullAccess

### AWS machine spec configuration file
This file should be named "aws_machine_spec.json" and look something like this:

    {
          "default": {
            "region": "eu-north-1",
            "instance_type": "t3.large",
            "volume_type": "gp2",
            "volume_size": 16,
            "coach_tag": "SammanCoach",
            "url_stem": "codekata.proagile.link",
            "hosted_dns_zone_id": "Z09412383RT0WUSMP2I5",
            "hosted_dns_zone_name": "proagile.link."
          }
    }

The top-level key "default" refers to your aws profile name (as defined in your .aws/credentials file). 
* region - the default region to create instances in if none is specified on the command line
* coach_tag - a tag which will be populated on the instance with the name of the user who created it
* url_stem - the custom url to assign to instances. This should be a url that your organization has control of and can assign using AWS Route53.
* hosted_dns_zone_name - the name of the dns zone in AWS Route53 you will assign to your machines.

### AWS zones configuration file

The aws_zones.json file should look like this:

    {
        "default": {
            "eu-central-1": {
                "image_id": "ami-05f7491af5eef733c",
                "security_group_ids": ["sg-0d66d1b4ba3786ff3"],
                "key_name": "pem-eu-central-1"
            }
        }
    }

The top-level key "default" refers to your aws profile name (as defined in your .aws/credentials file). The next level key is the AWS region name. Below that you need a valid image id, security group and key name.

To find out the relevant image id, go into your AWS management console for the region in question. Ask it to make a new instance and find the option to create an Ubuntu LTS instance. It should show the image id and you can copy it.

You will want to create a new key pair for your summoned machines. Create one, name it appropriately, download and store it in your .ssh folder.

You will want to create a new security group for your summoned machines. Create a new one. Add Inbound rules so you can have the following access:
* Custom TCP on port 8080 for ipv4
* Custom TCP on port 8080 for ipv6
* HTTP for ipv4
* HTTP for ipv6
* HTTPS for ipv4
* HTTPS for ipv6
* SSH for ipv4

The outbound rules that come by default seem to be ok - should allow all traffic on all ports for ipv4.

### Configure a DNS name for your machines to use
Buy a suitable domain name, and update its name servers to point at the ones on AWS. Create a 'hosted zone' to administrate it. There are instructions [here](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/migrate-dns-domain-inactive.html). You are going to use the script 'update_dns.py' to add records to this hosted zone for all the machines you'll create with 'summon.py'. Note the hosted zone id and add it to your aws_machine_spec.json config file.

# Tips and troubleshooting

## Fixing the keymap
When you have several people accessing a projector machine from different host operating systems, it has a tendency to re-set the keymap somewhat randomly. This can get rather annoying if copy and paste suddenly stop working for people on Windows when a Mac user happens to click somewhere on their browser window but otherwise weren't intending to change anything.

You can fix the keymap by using a custom VM property. Set this:

    -DORG_JETBRAINS_PROJECTOR_SERVER_AUTO_KEYMAP=false

in this file: clion64.vmoptions or equivalent - search for 'Edit Custom VM options' in the menus.

Then restart the instance. There is more documentation about this feature [in JetBrains documentation](https://jetbrains.github.io/projector-client/mkdocs/latest/ij_user_guide/server_customization/#enable-auto-keymap-setting).

## How to know which version of the IDE to use?

Log into a machine then do this:

    ubuntu@ip-172-31-15-238:~$ sudo su typist
    typist@ip-172-31-15-238:/home/ubuntu$ cd
    typist@ip-172-31-15-238:~$ .local/bin/projector install

    New version 1.3.0 of projector-installer is available (ver. 1.1.4 is installed)!
    Changelog: https://github.com/JetBrains/projector-installer/blob/master/CHANGELOG.md#130
    To update use command: projector self-update

    Installing IDE in quick mode; for full customization you can rerun this command with "--expert" argument or edit this co
    nfig later via "projector config edit" command.
               1. Idea_Community
               2. Idea_Ultimate
               3. PyCharm_Community
               4. PyCharm_Professional
               5. CLion
               6. GoLand
               7. DataGrip
               8. PhpStorm
               9. WebStorm
              10. RubyMine
              11. Rider
              12. DataSpell
              13. MPS
    Choose IDE type or 0 to exit: [0-13]: 4
    Do you want to select from Projector-tested IDE only? [y/N]y
               1. PyCharm Professional 2019.3.4
               2. PyCharm Professional 2020.2
               3. PyCharm Professional 2020.3.3
               4. PyCharm Professional Edition 2019.3.4
               5. PyCharm Professional Edition 2020.2
               6. PyCharm Professional Edition 2020.3.3
               7. PyCharm Professional Edition 2020.3.5
    Choose IDE number to install or 0 to exit: [0-7]: Aborted!
    typist@ip-172-31-15-238:~$


## How to troubleshoot Projector instances
Log into the instance with ssh. Check whether the system service running PyCharm (or whatever) exists and what the latest log messages are:

	sudo systemctl status pycharm

- View stack traces:

    journalctl -u clion

- change user to 'typist' 

    sudo su - typist

- look for a .projector folder in that user's home folder. It should have a configs folder - look for Pycharm - find the config.ini file ... check it looks ok.

## How to install a JetBrains plugin
eg the Verify plugin for Rider

1. download the right version of the plugin for the version of rider that you are using. For example verify-2021.3.0.zip
2. use ./instances.py to find out the ip addresses of all your machines
3. use scp to copy the file onto each machine, switch the ip address etc in this kind of commandline:

   scp -i pem-eu-central-1.pem  verify-2021.3.0.zip ubuntu@3.71.35.224:/home/ubuntu

4. On each machine, shift-shift to search everywhere and select 'plugins'
5. On the plugins window click the cog and choose 'install plugin from disk', then navigate to /home/ubuntu and select the plugin zip
6. ask it to restart rider
7. reboot your machines on aws

## Memory leak - out of disk space (Rider)
Log into machine and delete transient files:

    sudo su typist
    rm -rf .cache/JetBrains/Rider2021.2/resharper-host/local/Transient/

## Projector potential improvements and workarounds

   * Really sluggish sometimes. Workarounds:
      * Try Chrome or Edge browser
      * Close tab and open in a new tab (reloading doesn't seem to help much)
   * Markdown shows blank pages. This is a known bug. Workaround:
      * Use .txt files
   * Color schemes not modifiable. This is also a known bug, and it's not prioritized by JetBrains. Workaround:
      * Make the scheme and export it locally, import it to projector machine

# Notes for other IDEs and tools

## Golang
For goland  you need to additionally:

    - create a gopath eg /home/typist/gopath, and configure that in the IDE
    - run 'sudo apt-get install --reinstall ca-certificates' (maybe?)

## C Test Framework cgreen
This is what I did to augment the clion config:

    - sh login.sh <machine dns or ip>
    - git clone https://github.com/cgreen-devs/cgreen.git
    - sudo apt install cmake
    - cd cgreen && make
    - sudo make install
    - sudo ldconfig

In CMakeLists.txt files, find_package(cgreen) should then not crash

## Erlang in IntelliJ
Add the 'extra package' "erlang" to the IDE config
additionally:

    - install the erlang IntelliJ plugin
    - restart the machine