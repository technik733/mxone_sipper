import paramiko, time, re, getpass, sys

def logintest():

    ###set defaults as appropriate for your organization###
    default_mxone_username = "admin"
    default_mxone_target = "10.0.0.1"

    #grab credentials
    mxone_target = input("MXOne IP or hostname: ")
    if mxone_target == "":
        mxone_target = default_mxone_target

    mxone_username = input("MXOne username: ")
    if mxone_username == "":
        mxone_username = default_mxone_username
    mxone_password = getpass.getpass("MXOne password: ")

    #test credentials before proceeding
    print ("Checking credentials...")
    mxone_ssh = paramiko.SSHClient()
    #paramiko.hostkeys.clear()
    mxone_ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy())
    try:
        mxone_ssh.connect(mxone_target, username=mxone_username, password=mxone_password)
        print ("MXOne credentials accepted.")
    except:
        print ("MXOne login failed. Exiting.")
        quit()

    return mxone_target, mxone_username, mxone_password, mxone_ssh

def load(filename):
    print ("Reading CSV file...")
    #read the csv into a dictionary of with tuples for the values
    list_file = open(filename)
    ext2tup_dict = {}
    for line in list_file:
        #skip header lines
        if not line.startswith("\d"):
            continue
        line = line.rstrip()
        column_list = line.split(",")
        ext, first, last, csp, lim_number, license_type, divert_yn = column_list[0], column_list[1], column_list[2], column_list[3], column_list[4], column_list[5], column_list[6]
        ###default a blank csp field to what works for your organization###
        if csp == "":
            csp = "10"
        #flag empty names to skip later so the name command doesn't break
        skip_first = "n"
        skip_last = "n"
        if (first == '""') or (first == None):
            skip_first = "y"
        if (last == '""') or (last == None):
            skip_last = "y"
        ext2tup_dict[ext] = [first, last, csp, lim_number, license_type, divert_yn, skip_first, skip_last]
    print ("...Done")
    for key in ext2tup_dict:
        print (key, ext2tup_dict[key])
    return ext2tup_dict

#assumes ext2tup_dict is already defined
def extmove():
    #create/truncate logfile
    logfile = open("sipper_log.txt", "w+")
    buff = ""
    print ("Moving extensions...")

    #open the connection to mxone
    mxone_ssh = paramiko.SSHClient()
    mxone_ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    mxone_ssh.connect(mxone_target, username=mxone_username, password=mxone_password)
    #open a shell
    chan = mxone_ssh.invoke_shell()

    #wait for a response
    time.sleep(.1)
    resp = chan.recv(9999).decode("utf-8")
    buff += resp

    #wait for a prompt
    while not buff.endswith("> "):
        time.sleep(.1)
        resp = chan.recv(9999).decode("utf-8")
        buff += resp

    # counter for backups
    counter = 0
    totalcounter = 0

    #create/truncate the exceptions_log file
    exceptlog = open("sipper_exceptions_log.txt", "w+")
    exceptlog.write("\n")
    exceptlog.close()

    #move the extensions
    for ext in ext2tup_dict:
        skip_ext = "n"
        minibuff = ""
        # backup after backup_at runs
        if counter == backup_at:
            print ("Running backup...")
            chan.send("data_backup" + "\n")
            #wait for a response (weird - resp is the string instead of buff)
            resp = chan.recv(9999).decode("utf-8")
            while not resp.endswith("> "):
                resp += chan.recv(9999).decode("utf-8")
                buff += resp
            counter = 0
            print (resp)

        #set up the variables for the commands
        #handle names with spaces
        first = ext2tup_dict[ext][0]
        if " " in first:
            first = "\"" + first + "\""
        last = ext2tup_dict[ext][1]
        if " " in last:
            last = "\"" + last + "\""
        csp = ext2tup_dict[ext][2]
        lim_number = ext2tup_dict[ext][3]
        license_type = ext2tup_dict[ext][4]
        divert_yn = ext2tup_dict[ext][5]
        skip_first = ext2tup_dict[ext][6]
        skip_last = ext2tup_dict[ext][7]

        #strings to sudip and susip the extension, saving files if possible
        ###use for 6.3+###
        command1 = 'resource_status --extensions -d %s --high-detail' % (ext)
        command2 = ''

        ###use for pre-6.3###
        #command1 = '/opt/eri_sn/bin/mdsh -c "sudip:dir=%s;"' % (ext)
        #command2 = '/opt/eri_sn/bin/mdsh -c "susip:dir=%s;"' % (ext)

        #check call lists also
        command3 = 'call_list -p -d %s' % (ext)

        #strings to end the extensions
        command4 = '/opt/eri_sn/bin/mdsh -c "extee:dir=%s;"' % (ext)
        command5 = '/opt/eri_sn/bin/mdsh -c "ksexe:dir=%s;"' % (ext)

        #strings to build the VoIP phones
        command6 = "extension -i --dir %s --csp %s --edn no --lim %s --customer 0 --language-code en --secretary 0 --free-on-second-line 0 --security-exception yes" % (ext, csp, lim_number)
        command7 = "ip_extension -i --dir %s --protocol %s" % (ext, license_type)

        #name the extension
        #skip blank names
        if (skip_first == "n") and (skip_last == "n"):
            command8 = "name -i --dir %s --number-type Dir --name1 %s --name2 %s --presentation-priority 1" % (ext, first, last)
        if (skip_first == "y") and (skip_last == "y"):
            command8 = "\n"
        if (skip_first == "n") and (skip_last == "y"):
            command8 = "name -i --dir %s --number-type Dir --name1 %s --presentation-priority 1" % (ext, first)
        if (skip_first == "y") and (skip_last == "n"):
            command8 = "name -i --dir %s --number-type Dir --name2 %s --presentation-priority 1" % (ext, last)

        ###set these for your organization###
        #default voicemail diversion setting
        command9 = "diversion -i --dir %s --div-destination-number 93000 --div-noreply 1 --div-busy 1 --div-immediate 0" % (ext)
        #no answer
        command10 = "extension_procedure --dir %s --proc '*21#'" % (ext)
        #busy
        command11 = "extension_procedure --dir %s --proc '*22#'" % (ext)
        #direct - this one is skipped normally
        #command12 = "extension_procedure --dir %s --proc '*2#'" % (ext)

        #define all commands that are checks
        check_commands = [command1, command2, command3]

        #only divert if it's flagged for diversion
        if divert_yn == "y":
            commands = [command4, command5, command6, command7, command8, command9, command10, command11]
        else:
            commands = [command4, command5, command6, command7, command8]

        #run check_commands
        for command in check_commands:
            chan.send(command + "\n")
            #wait for a response
            resp = chan.recv(9999).decode("utf-8")
            buff += resp
            #minibuff is for just this extension
            minibuff += resp
            #wait for a prompt
            while not buff.endswith("> "):
                time.sleep(.1)
                resp = chan.recv(9999).decode("utf-8")
                buff += resp
                minibuff += resp

        ###these checks should be tuned to what your organization wants###
        #catch busy extensions & skip
        if (re.search("SPEECH", minibuff) or re.search("CALORG", minibuff)) or re.search("CALTER", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Extension Busy [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch parallel ring groups & skip
        if re.search("PARALLEL RINGING DATA", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Parallel Ring [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch pickup groups & don't skip
        if re.search("GROUP DATA", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Pickup Group\n")
            exceptlog.close()

        #catch call lists & skip
        if re.search("Call List Information", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Call List [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch PEN keys & don't skip
        if re.search("PEN    -", minibuff) or re.search("PEN                \d+", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - PEN Key\n")
            exceptlog.close()

        #catch TNS keys & don't skip
        if re.search( "TNS    \d+", minibuff) or re.search("TNS                \d+", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - TNS Key\n")
            exceptlog.close()

        #catch SCA keys & skip
        if re.search("SCA    \d\d\d\d\d", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - SCA Key [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch MNS Key Exists & skip
        if re.search("MNS    \d\d\d\d\d", minibuff) or re.search("MNS   \d\d\d\d\d", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - MNS Key Exists [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch MDN Key Exists & skip
        if re.search("MDN   \d\d\d\d\d", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - MDN Key Exists [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch Extension is an MDN key & skip
        if re.search("EXTENSION MULTIPLE DIRECTORY NUMBER DATA", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Extension is an MDN Key [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch ADN Key Exists & skip
        if re.search("ADN          \d\d\d\d\d", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - ADN Key Exists [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch Extension is an ADN Key & skip
        if re.search("ADN    CALALT  ODN", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - Extension is an ADN Key [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch EDN Key Exists & skip
        if re.search("EDN    \d\d\d\d\d", minibuff):
            exceptlog = open("sipper_exceptions_log.txt", "a")
            exceptlog.write(ext + " - EDN Key Exists [SKIPPED]\n")
            exceptlog.close()
            skip_ext = "y"

        #catch Extension is an EDN Key
        #this doesn't seem to exist, need to build a system to detect it

        #skip the extension if it has a terminal illness
        if skip_ext == "y":
            buff += ("\nSkipped " + ext + "\n")
            print (minibuff)
            print ("Skipped " + ext)
            continue

        #if not, send commands
        for command in commands:
            chan.send(command + "\n")
            #wait for a response
            resp = chan.recv(9999).decode("utf-8")
            buff += resp
            #minibuff is for just this extension
            minibuff += resp
            #wait for a prompt
            while not buff.endswith("> "):
                time.sleep(.1)
                #catching command busy
                if re.search(minibuff, "COMMAND BUSY"):
                    exceptlog = open("sipper_exceptions_log.txt", "a")
                    exceptlog.write(ext + " - COMMAND BUSY [" + command + "]\n")
                    exceptlog.close()
                    print (ext + " - COMMAND BUSY [" + command + "]")
                resp = chan.recv(9999).decode("utf-8")
                buff += resp
                minibuff += resp
                #answer yes to any confirmation
                if buff.endswith("Are you sure? (Y/N): "):
                    chan.send("y\n")

        print (minibuff)
        #reset minibuff
        minibuff = ""
        print ("Extension migration complete for " + ext +".")
        # count for backups and number of phones
        counter += 1
        totalcounter += 1
        print (str(counter) + " extensions since backup.")
        print (str(totalcounter) + " extensions total.")

    #run a final backup
    print ("Running final backup...")
    chan.send("data_backup" + "\n")
    #wait for response (weird - resp is string, not buff)
    resp = chan.recv(9999).decode("utf-8")
    while not resp.endswith("> "):
        resp += chan.recv(9999).decode("utf-8")
        buff += resp
    logfile.write(buff)
    logfile.close()

#actual program execution
filename = sys.argv[1]

#credential gram and login test
mxone_target, mxone_username, mxone_password, mxone_ssh = logintest()

#load file into a dictionary of tuples keyed by extension
ext2tup_dict = load(filename)

#set backup interval
while True:
    backup_at = input("Run backup every X extensions (1-100):")
    try:
        backup_at = int(backup_at)
    except:
        print ("Must be an integer, try again.")
        continue
    if ((backup_at < 1) or (backup_at > 100)):
        print ("Must be between 1 and 100, try again.")
        continue
    else:
        break

#confirm before executing
confirmation = input("Are you sure you want to begin now? (y/n):")
if confirmation is not "y":
    print ("Exiting.")
    quit()
else:
    pass

#move all extensions
extmove()

print ("Batch migration operation complete. See sipper_log.txt, and sipper_exceptions_log.txt for details.")
