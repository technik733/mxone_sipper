# mxone_sipper
Python script for automating the migration of simple extensions / phone numbers from analog and digital to SIP on the Mitel MXOne PBX.

Tested with:
Python 3.4+
Paramiko 2.4.2+ 

An older version of Paramiko may work, but there is a bug in 2.2.1 that breaks an earlier version of this script.

It's important to find the triple-commented lines and adjust the appropriate variables and strings to your particular implimentation of the MXOne. (default username, IP address, diversion dial codes, etc). A sample CSV file is included in this repository.

Further documentation is pending.
