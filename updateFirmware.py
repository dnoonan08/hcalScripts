from optparse import OptionParser

import subprocess
import pexpect
from time import time, sleep
from re import search, escape
import sys
import os

#sys.path.insert(0, '/nfshome0/dnoonan')
#from ngccmServerInfo import *

def progress(i = 0, n = 0, k = 50): # i: iterator, k: total length of progress bar, n: total number of events
	stdstore = sys.stdout
	sys.stdout = sys.__stdout__
	if i == n:
		print " \t[" + "="*k + "]" + "\t{0:.2f}%".format(100)
		print "\033[J\033[F"
		sys.stdout = stdstore
	else:
		if i%4 == 0:
		    print " \t[" + "="*(i*k/n) + "-" + " "*(k-1-i*k/n) + "]" + "\t{0:.2f}%".format(100.*i/n)
		if (i+1)%4 == 0:
			print " \t[" + "="*(i*k/n) + "/" + " "*(k-1-i*k/n) + "]" + "\t{0:.2f}%".format(100.*i/n)
		if (i+2)%4 == 0:
			print " \t[" + "="*(i*k/n) + "|" + " "*(k-1-i*k/n) + "]" + "\t{0:.2f}%".format(100.*i/n)
		if (i+3)%4 == 0:
			print " \t[" + "="*(i*k/n) + "\\" + " "*(k-1-i*k/n) + "]" + "\t{0:.2f}%".format(100.*i/n)
		print "\033[J",
		sys.stdout = stdstore
		print 
		sys.stdout = sys.__stdout__
		print "\033[F"*2,
		sys.stdout = stdstore

def sendProgramCommands(cmds, port = 4342, host = 'hcal904daq02', sleepTime = 0,crate='1'):
	if type(cmds)==type(list()): 
		cmds = cmds
	else:
		cmds = [cmds]
	# cmd_file = open("ngfec_cmds",'write')

	ngfec_cmd = 'ngFEC.exe -z -c -p %i -H %s'%(port, host)
	p = pexpect.spawn(ngfec_cmd)


	passed = False
	# for cmd in cmds:
	# 	cmd_file.write(cmd+'\n')
	# cmd_file.close()

	if port==63000:
		c = 'tput %s-lg  go_offline'%crate
		p.sendline(c)
		sleep(.5)
		c = 'tput %s-[1-7,9-14]-B_[JTAG_Select_FPGA,JTAGSEL,JTAG_Select_Board,Bottom_TRST_N,Top_TRST_N,Bottom_RESET_N,Top_RESET_N,Igloo_VDD_Enable] go_online'%crate
		p.sendline(c)
		c = 'tput %s-bkp_jtag_sel go_online'%crate
		p.sendline(c)
		sleep(.5)
		

	for i, c in enumerate(cmds):
		print c
		p.sendline(c)
		out = p.expect(["Exit code = .*","jtag busy ... try again later","connection failed, try again in .*",pexpect.TIMEOUT],timeout=180)			
		val = p.after
		print(val)

	if out==0 and 'Exit code = 0' in val:
		passed = True

	if port==63000:
		c = 'tput %s-lg  go_online'%crate
		p.sendline(c)
		sleep(.5)
		# c = 'put HF%s-bkp_reset 0'%crate
		# p.sendline(c)
		# c = 'put HF%s-bkp_reset 1'%crate
		# p.sendline(c)
		# sleep(.5)
		# c = 'put HF%s-bkp_reset 0'%crate
		# p.sendline(c)
		# sleep(.5)
		c = 'tput %s-lg  push'%crate
		p.sendline(c)
		sleep(.5)

	p.sendline('quit')

#	progress()
#	print
	p.expect(pexpect.EOF)

	p.close()
	return passed

def sendngFECcommands(cmds, port = 4342, host = 'hcal904daq02'):
    if type(cmds)==type(list()): 
        cmds = cmds
    else:
        cmds = [cmds]
    cmd_file = open("ngfec_cmds",'write')

    ngfec_cmd = 'ngFEC.exe -z -c -p %i -H %s'%(port, host)
    p = pexpect.spawn(ngfec_cmd)

    for cmd in cmds:
        cmd_file.write(cmd+'\n')
    cmd_file.write('wait\nquit\n')
    cmd_file.close()

    p.sendline("< ngfec_cmds")

    output = []
    for i, c in enumerate(cmds):
        # Deterimine how long to wait until the first result is expected:
        if i == 0:
            timeout = max([30, int(0.0075*len(cmds))])
#					print i, c, timeout
        else:
            timeout = 30		# pexpect default
            #					print i, c, timeout
            #				print i, c, timeout
				
        t0 = time()
        p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(escape(c)), timeout=timeout)
        t1 = time()
        output.append({
                "cmd": c,
                "result": p.match.group(1).strip().replace("'", ""),
                "times": [t0, t1],
                })
    p.sendline("quit")
    
    p.expect(pexpect.EOF)
    p.close()
    return output


def reprogram(crate, slot, majorVersion, minorVersion, top=True, bot=True, programFile = '',port=4342,host='hcal904daq02',device_info = False, verify = False,topOnly=False,botOnly=False,verbose=False):

	runTop = top
	runBot = bot
	checkcmds = ['get %s-%i-iTop_FPGA_MAJOR_VERSION'%(crate, slot),
		     'get %s-%i-iTop_FPGA_MINOR_VERSION'%(crate, slot),
		     'get %s-%i-iBot_FPGA_MAJOR_VERSION'%(crate, slot),
		     'get %s-%i-iBot_FPGA_MINOR_VERSION'%(crate, slot)]

	if port ==63000:
		checkcmds = ['get %s-%i-iTop_FPGA_MAJOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iTop_FPGA_MINOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iBot_FPGA_MAJOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iBot_FPGA_MINOR_VERSION_rr'%(crate, slot)]
		
	output = sendngFECcommands(cmds=checkcmds,port=port,host=host)
	iTopFW = '%s.%s' % (output[0]['result'].replace('0x',''),output[1]['result'].replace('0x',''))
	iBotFW = '%s.%s' % (output[2]['result'].replace('0x',''),output[3]['result'].replace('0x',''))
	firmwareVersion = '%s.%s'%(str(majorVersion),str(minorVersion))

	if len(str(minorVersion))==2:
		if str(minorVersion)[0]=='0':
			firmwareVersion = '%s.%s'%(str(majorVersion),str(minorVersion)[1])

	if iTopFW.lower()==firmwareVersion.lower():
		runTop=False
	if iBotFW.lower()==firmwareVersion.lower():
		runBot = False


	JTAG_Command_Type = 'PROGRAM'
	if device_info:
		JTAG_Command_Type = 'DEVICE_INFO'
	if verify:
		JTAG_Command_Type = 'VERIFY'
	if verify or device_info:
		runTop = True
		runBot = True

	if topOnly:
		runTop=True
		runBot=False
	if botOnly:
		runTop=False
		runBot=True

	if not runTop and not runBot:
		print 'Firmware on %s-%i is correct'%(crate, slot)
		return

	errorcmds = ['get %s-mezz_rx_prbs_error_cnt'%crate,
		     'get %s-mezz_rx_rsdec_error_cnt'%crate,
		     'get %s-fec_rx_raw_error_cnt'%crate,
		     'get %s-fec_rx_prbs_error_cnt'%crate,
		     'get %s-fec_bkp_pwr_flip_cnt'%crate,
		     ]
	if port ==63000:
		errorcmds = ['get %s-mezz_rx_prbs_error_cnt_rr'%crate,
			     'get %s-mezz_rx_rsdec_error_cnt_rr'%crate,
			     'get %s-fec_rx_raw_error_cnt_rr'%crate,
			     'get %s-fec_rx_prbs_error_cnt_rr'%crate,
			     'get %s-fec_bkp_pwr_flip_cnt_rr'%crate,
			     ]

	outputPre = sendngFECcommands(cmds=errorcmds,port=port,host=host)

	if 'PWRBAD.ERROR' in iTopFW:
		runTop=False
		print 'Power Bad Error!!!!'
	if 'PWRBAD.ERROR' in iBotFW:
		runBot=False
		print 'Power Bad Error!!!!'


	passed_top = True
	passed_bot = True
	



	if runTop:
		cmds = ['jtag %s %s-%i-top %s'%(programFile,crate, slot, JTAG_Command_Type)]
		passed_top = sendProgramCommands(cmds=cmds,sleepTime=240,port=port,host=host,crate=crate)
	if runBot:
		cmds = ['jtag %s %s-%i-bot %s'%(programFile,crate, slot, JTAG_Command_Type)]
		passed_bot = sendProgramCommands(cmds=cmds,sleepTime=240,port=port,host=host,crate=crate)




	if not (passed_top and passed_bot) or verbose:
		outputPost = sendngFECcommands(cmds=errorcmds,port=port,host=host)

		print 'BEFORE PROGRAMMING                   | AFTER PROGRAMMING'
		print 'mezz prbs errors   : %s%s| mezz prbs errors  : %s'%(outputPre[0]['result'],(16-len(outputPre[0]['result']))*' ',outputPost[0]['result'])
		print 'mezz rsdec errors  : %s%s| mezz rsdec errors : %s'%(outputPre[1]['result'],(16-len(outputPre[1]['result']))*' ',outputPost[1]['result'])
		print 'fec raw errors     : %s%s| fec raw errors    : %s'%(outputPre[2]['result'],(16-len(outputPre[2]['result']))*' ',outputPost[2]['result'])
		print 'fec prbs errors    : %s%s| fec prbs errors   : %s'%(outputPre[3]['result'],(16-len(outputPre[3]['result']))*' ',outputPost[3]['result'])
		print 'bkp power flips    : %s%s| bkp power flips   : %s'%(outputPre[4]['result'],(16-len(outputPre[4]['result']))*' ',outputPost[4]['result'])


	checkcmds = ['get %s-%i-iTop_FPGA_MAJOR_VERSION'%(crate, slot),
		     'get %s-%i-iTop_FPGA_MINOR_VERSION'%(crate, slot),
		     'get %s-%i-iBot_FPGA_MAJOR_VERSION'%(crate, slot),
		     'get %s-%i-iBot_FPGA_MINOR_VERSION'%(crate, slot)]

	if port ==63000:
		checkcmds = ['get %s-%i-iTop_FPGA_MAJOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iTop_FPGA_MINOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iBot_FPGA_MAJOR_VERSION_rr'%(crate, slot),
			     'get %s-%i-iBot_FPGA_MINOR_VERSION_rr'%(crate, slot)]
	
	output = sendngFECcommands(cmds=checkcmds,port=port,host=host)
	iTopFW = '%s.%s' % (output[0]['result'].replace('0x',''),output[1]['result'].replace('0x',''))
	iBotFW = '%s.%s' % (output[2]['result'].replace('0x',''),output[3]['result'].replace('0x',''))
#	firmwareVersion = '%s.%s'%(str(majorVersion),str(minorVersion))
	iTopFWPrint = ''
	iBotFWPrint = ''
	if not iTopFW.lower()==firmwareVersion.lower(): iTopFWPrint = iTopFW+' <===== Wrong iTop Version'
	if not iBotFW.lower()==firmwareVersion.lower(): iBotFWPrint = iBotFW+' <===== Wrong iBot Version'
	if not iTopFWPrint=='':
		print iTopFWPrint
	if not iBotFWPrint=='':
		print iBotFWPrint
	return


parser = OptionParser()
parser.add_option("-c", "--fecrate", dest="c",
                  default="-1",
                  help="FE crate (default is -1)",
                  metavar="STR"
                  )
parser.add_option("-s", "--feslot", dest="s",
                  default="-1",
                  help="FE slot, can be integer or list of integers comma separated without spaces (default is -1)",
                  metavar="STR"
                  )
parser.add_option("-p", "--port", dest="p",
                  default="4342",
                  help="ngccm server port number, default is 4342",
                  metavar="STR"
                  )
parser.add_option("--device_info","--DEVICE_INFO", action="store_true", dest="DEVICE_INFO", default=False ,
		  help="Run device info instead of programming")
parser.add_option("--verify","--VERIFY", action="store_true", dest="VERIFY", default=False ,
		  help="Run verify instead of programming")
parser.add_option("-H","--host", dest="h",
                  default="hcal904daq02",
                  help="ngccm server host machine, default is hcal904daq02",
                  metavar="STR"
                  )
parser.add_option("-f", "--fw", "--firmware", dest="fw",
		  default="5.0A",
		  help="version of the firmware to use",
		  metavar="STR"
		  )
parser.add_option("-l", "--location", dest="l",
		  default="",
		  help="location of special programming file",
		  metavar="STR"
		  )
parser.add_option("-v", "--verbose", dest="verbose",
		  action="store_true",
		  default=False,
		  help="Verbose mode, Print out the error counts for before and after each card is programmed",
		  )
parser.add_option("--top", dest="topOnly",action="store_true",default=False,
		  help="run on only the top igloo",
		  )
parser.add_option("--bot", dest="botOnly",action="store_true",default=False,
		  help="run on only the bot igloo",
		  )

(options, args) = parser.parse_args()
if options.c == "-1":
	print 'specify a crate number'
	sys.exit()

if not(options.c[0]=='[' and options.c[-1]==']'):
    options.c = '["'+options.c.replace(',','","')+'"]'
print options.c
fe_crates = options.c

if ',' in options.s and not(options.s[0]=='[' and options.s[-1]==']'):
    options.s = '['+options.s+']'
fe_slot = eval(options.s)

# port = int(options.p)
# host = options.h

fe_crates = eval(options.c)


fwVersion = options.fw
majorVersion = fwVersion.split('.')[0]
minorVersion = fwVersion.split('.')[1]
programFile=options.l

if programFile=='':
	fileName = 'main_HF_RM_%s_%s_FIX.stp'%(str(majorVersion),str(minorVersion))
	if os.path.exists('/nfshome0/jmariano/HF_RM_FW/%s'%fileName):
		programFile = '/nfshome0/jmariano/HF_RM_FW/%s'%fileName
	elif os.path.exists('/nfshome0/dnoonan/HF_RM_FW/%s'%fileName):
		programFile = '/nfshome0/dnoonan/HF_RM_FW/%s'%fileName
	else:
		print "Unable to find file"
		sys.exit()


print
print 'Using firmware version %s in programming file %s'%(fwVersion,programFile)
print

for fe_crate in fe_crates:
	port = 63000
	host = 'hcalvme04'

	if fe_slot == -1:
		cmd = 'get {0}-[1,2,3,4,5,6,7,9,10,11,12,13,14]-bkp_temp_f'.format(fe_crate)
		if port == 63000:
			cmd = 'get {0}-[1,2,3,4,5,6,7,9,10,11,12,13,14]-bkp_temp_f_rr'.format(fe_crate)
		output = sendngFECcommands(cmds = cmd, port=port, host=host)[0]
		slotList = [1,2,3,4,5,6,7,9,10,11,12,13,14]
		filledSlots = []
		temps = output['result'].split()
		for i in range(len(temps)):
			if float(temps[i])>0:
				filledSlots.append(slotList[i])
			elif float(temps[i])>-270:
				print 'Problem with card in slot %i',i
	else:
		if type(fe_slot)==type(list()): 
			filledSlots = fe_slot
		else:
			filledSlots = [int(fe_slot)]
    
    
	print 'Running over slots', filledSlots

#for crate in crateSlots:
#	slots = crateSlots[crate]
	for slot in filledSlots:
		reprogram(str(fe_crate), slot, majorVersion, minorVersion,programFile=programFile,port=port,host=host,device_info=options.DEVICE_INFO,verify=options.VERIFY,topOnly=options.topOnly,botOnly=options.botOnly,verbose=options.verbose)

		
