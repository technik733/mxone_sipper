# mxone_sipper
Python script for automating the migration of simple extensions / phone numbers from analog and digital to SIP on the Mitel MXOne PBX. This script works on both MXOne 6.3 SP0 HF2 and (with one alteration) 6.1 SP0 HF2.

Requirements:
This script has been tested with Python 3.4+ and with Paramiko 2.2.0 and 2.4.2. You do also need to have SSH access to the MXOne on the machine that's running this script.

It's important to find the triple-commented lines (###enclosed by three pound signs###) and adjust the appropriate variables and strings to your particular implimentation of the MXOne. (default username, IP address, voicemail diversion number, dial codes, etc). 

One way to get a good idea of what you would want to change things to, you can view /var/log/messages to see the exact commands that Provisioning Manager sends when you end and build a phone.

Paramiko can be installed by running "pip install paramiko" from your workstation if you have python3 installed. (Substitute pip3 if you have two versions of Python installed.)

A sample CSV file is included in this repository, and further documentation is pending.
