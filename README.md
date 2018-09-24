# mxone_sipper
Python script for automating the migration of simple extensions / phone numbers from analog and digital to SIP on the Mitel MXOne PBX. This script works on both MXOne 6.3 SP0 HF2 and (with one alteration) 6.1 SP0 HF2.

Requirements:
This script has been tested with Python 3.4+ and with Paramiko 2.2.0 and 2.4.2. You do also need to have SSH access to the MXOne on the machine that's running this script.

An older version of Paramiko may work, but there is a bug in 2.2.1 that breaks an previous version of this script, and I will not be testing this.

It's important to find the triple-commented lines and adjust the appropriate variables and strings to your particular implimentation of the MXOne. (default username, IP address, diversion dial codes, etc). A sample CSV file is included in this repository.

Further documentation is pending.
