# Ensemble Machine

Support scripts for Samman Coaches to provision practice machines on AWS EC2. Before these will work you will need:
    
    - an account on AWS
    - AWS credentials
    - pem file(s) for each AWS region you want to use
    - a aws_zones.json file specifying pem file, images and security groups.

The aws_zones.json file should look like this:

    {
        "eu-central-1": {
            "image_id": "ami-05f7491af5eef733c",
            "security_group_ids": ["sg-0d66d1b4ba3786ff3"],
            "key_name": "pem-eu-central-1"
        }
    }

Replace those regions, ids and key file name with the ones you have for your AWS account.

## How to create a new practice machine that uses JetBrains Projector

    python summon.py

... then follow the instructions.

## How to login to a summoned machine

    sh login.sh 12.23.34.45

... or DNS name:

    sh login.sh b5f76de4-clion.codekata.proagile.link

## How to delete an instance

Use the AWS console

## How to clone a repo to a machine

    sh clone_kata.sh https://github.com/emilybache/starter.git b5f76de4-clion.codekata.proagile.link

## How to see what state the Projector instances have

Example run:

    $ python instances.py
    d5f4dba2-clion.codekata.proagile.link             stopped     ebjaolo
    e32c9ea5-clion.codekata.proagile.link             stopped     ebjaolo
    0899b6a8-clion.codekata.proagile.link             stopped     ebjaolo
    46b0cd53-clion.codekata.proagile.link             stopped     emily

# How to shut down a machine?

    sh turn_off_machine.sh b5f76de4-clion.codekata.proagile.link

# How to know which version of the IDE to use?

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


### How to troubleshoot Projector instances
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

## Notes for other ide tools etc

## Golang
For goland  you need to additionally:
    - create a gopath eg /home/typist/gopath, and configure that in the IDE
    - run 'sudo apt-get install --reinstall ca-certificates' (maybe?)

### C Test Framework cgreen
This is what I did to augment the clion config:
    - sh login.sh <machine dns or ip>
    - git clone https://github.com/cgreen-devs/cgreen.git
    - sudo apt install cmake
    - cd cgreen && make
    - sudo make install
    - sudo ldconfig

In CMakeLists.txt files, find_package(cgreen) should then not crash

### Erlang in IntelliJ
Add the 'extra package' "erlang" to the IDE config
additionally:
    - install the erlang IntelliJ plugin
    - restart the machine