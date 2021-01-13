# REQUIREMENTS

This file covers aspects of hardware and software requirements for tools/checkers (located in `Tools` folder) we developed.

## Hardware environment

Processor: 2 gigahertz (GHz) or faster processor

Memory: 2G RAM or higher

Disk: No requirement

Network connection: Required

In our paper, all experiments were done on the same machine, which contains a 16-core Intel Xeon E5-2667 v4 CPU (3.20GHz), 25MB L3 Cache, 64GB RAM, and 6×512GB SSD (RAID 5). It has a 1000Mbps network connection, with twisted pair port. Note that all the machine-learning inference is done by cloud APIs remotely, instead of on the machine locally.

## Software environment

Linux/Unix operating system

### Python>=3.8

jedi >= 0.17.0

astor >= 0.8.1

anytree >= 2.8.0

PyGithub >= 1.51

urllib3 >= 1.25.9

google-cloud-language==1.3.0

google-cloud-vision==1.0.0

google-cloud-speech==2.0.0

google-cloud-texttospeech==2.2.0

### Ruby>=2.4

octokit>=4.18.0
