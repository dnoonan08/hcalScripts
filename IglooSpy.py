from time import time,sleep
from optparse import OptionParser
import sys
import pexpect
from re import search, escape
from datetime import datetime

def time_string():
	return datetime.now().strftime("%y%m%d_%H%M%S.%f")[:-3]		# Chop off the last three decimal places, leaving three (not rounding).

def progress(i = 0, n = 0, name = None, k = 50): # i: iterator, k: total length of progress bar, n: total number of events
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
		print "\t\t" + str(name)
		sys.stdout = sys.__stdout__
		print "\033[F"*2,
		sys.stdout = stdstore



def sendngFECcommands(cmds=['quit'], script=True, raw=False, progbar=False, port = 63000, host = "hcal904daq04"):
	# Arguments and variables
	output = []
	raw_output = ""
	# if script: 
	# 	print 'Using script mode'
	# else: 
	# 	print 'Not using script mode'

	# print cmds

	if host != False and port:		# Potential bug if "port=0" ... (host should be allowed to be None.)
		## Parse commands:
		if isinstance(cmds, str):
			cmds = [cmds]
		if not script:
			if "quit" not in cmds:
				cmds.append("quit")
		else:
			cmds = [c for c in cmds if c != "quit"]		# "quit" can't be in a ngFEC script.
			cmds_str = ""
			for c in cmds:
				cmds_str += "{0}\n".format(c)
			file_script = "ngfec_script"
			with open(file_script, "w") as out:
				out.write(cmds_str)
		
		# Prepare the ngfec arguments:
		ngfec_cmd = 'ngFEC.exe -z -c -p {0}'.format(port)
		if host != None:
			ngfec_cmd += " -H {0}".format(host)
		
		# Send the ngfec commands:
		p = pexpect.spawn(ngfec_cmd)

		if not script:
			for i, c in enumerate(cmds):
				if 'wait' in c:
					# waitTime = int(c.split()[-1])
					# sleep(waitTime/1000.)
					continue
				p.sendline(c)
				if c != "quit":
					if progbar:
						progress(i, len(cmds), cmds[i].split()[1])
					t0 = time()
					p.expect("{0}\s?#((\s|E)[^\r^\n^#]*)".format(escape(c)))
					t1 = time()
#					print [p.match.group(0)]
					output.append({
						"cmd": c,
						"result": p.match.group(1).strip().replace("'", ""),
						"times": [t0, t1],
						"raw": p.before+p.after
					})
					raw_output += p.before + p.after
		else:
			p.sendline("< {0}".format(file_script))
			for i, c in enumerate(cmds):
				# Deterimine how long to wait until the first result is expected:
				if i == 0:
					timeout = max([30, int(0.2*len(cmds))])
#					print i, c, timeout
				else:
					timeout = 30		# pexpect default
#					print i, c, timeout
#				print i, c, timeout
				
				# Send commands:
				t0 = time()
				p.expect(["{0}\s?#((\s|E)[^\r^\n^#]*)".format(escape(c)),'bingo'], timeout=timeout)
				t1 = time()
#				print [p.match.group(0)]
				output.append({
					"cmd": c,
					"result": p.match.group(1).strip().replace("'", ""),
					"times": [t0, t1],
					"raw": p.before+p.after
				})
				raw_output += p.before + p.after
			p.sendline("quit")
		if progbar:
			progress()
		p.expect(pexpect.EOF)
		raw_output += p.before
#		sleep(1)		# I need to make sure the ngccm process is killed.
		p.close()
#		print "closed"
		if raw:
			return raw_output
		else:
			return output


def readIglooSpy_per_card(port,host, crate, slot, topbottom, card, subdetector="HF",Nsamples=0, verbose=True):

	results = {}
	if not (topbottom==0 or topbottom==1):
		print 'ERROR: parameter topbottom --- 1 for top, 0 for bottom'
		return results
	TB=['Bot','Top']
	try:
		if verbose:
			print "######################################"
			print "#  Reading Input Spy ...             #"
			print "######################################"
		if subdetector=="HF":
			cmd1 = ["put {0}-{1}-i{2}_CntrReg_WrEn_InputSpy 1".format(crate, slot, TB[topbottom]),
				"wait 100",
				"put {0}-{1}-i{2}_CntrReg_WrEn_InputSpy 0".format(crate, slot,TB[topbottom]),
				"get {0}-{1}-i{2}_StatusReg_InputSpyWordNum".format(crate, slot, TB[topbottom])]

			output = sendngFECcommands(cmds=cmd1,port=port,host=host)
			nsamples = int(output[-1]["result"],16) if not Nsamples else min(int(output[-1]["result"],16),Nsamples)

			if verbose: print "Reading {0} samples".format(nsamples)
			cmd2 = ["get {0}-{1}-i{2}_inputSpy".format(crate, slot, TB[topbottom]),
				"wait 200"]*nsamples
		elif subdetector=="HE":
			cmd1 = ["put {0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 1".format(crate, slot, card),
				"wait 100",
				"put {0}-{1}-{2}-i_CntrReg_WrEn_InputSpy 0".format(crate, slot,card),
				"get {0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, card)]

			output = sendngFECcommands(cmds=cmd1,port=port,host=host)
			nsamples = int(output[-1]["result"],16) if not Nsamples else min(int(output[-1]["result"],16),Nsamples)

			if verbose: print "Reading {0} samples".format(nsamples)
			cmd2 = ["get {0}-{1}-{2}-i_inputSpy".format(crate, slot, card),
				"wait 200"]*nsamples

		
		output_all = sendngFECcommands(cmds=cmd2, port=port, host=host, script = False, progbar=verbose)

		results[crate, slot, TB[topbottom]] = [out["result"] for out in output_all if not (out["result"] == "OK" or out["result"] == "commented command")]

	except Exception as ex:
		print "Caught exception:"
		print ex
	return results



def clear_buffer(crate, slot, card, port, host, subdetector="HF",verbose=True):
	if verbose:
		print "######################################"
		print "#  Clearing the buffer...            #"
		print "######################################"

	if subdetector=="HF":
		cmds = ["put {0}-{1}-i[Top,Bot]_CntrReg_InputSpyRst 2*0".format(crate,slot),
			"wait",
			"put {0}-{1}-i[Top,Bot]_CntrReg_InputSpyRst 2*1".format(crate,slot),
			"wait",
			"put {0}-{1}-i[Top,Bot]_CntrReg_InputSpyRst 2*0".format(crate,slot),
			]
	elif subdetector=="HE":
		cmds = ["put {0}-{1}-{2}-i_CntrReg_InputSpyRst 0".format(crate,slot,card),
			"wait",
			"put {0}-{1}-{2}-i_CntrReg_InputSpyRst 1".format(crate,slot,card),
			"wait",
			"put {0}-{1}-{2}-i_CntrReg_InputSpyRst 0".format(crate,slot,card),
			]

#	print cmds
	output = sendngFECcommands(cmds=cmds, port=port, host=host)



def interleave(c0, c1):
	retval = 0;
	for i in xrange(8):
		bitmask = 0x01 << i
		retval |= ((c0 & bitmask) | ((c1 & bitmask) << 1)) << i;

	return retval

def parseIglooSpy(buff):
	# first split in pieces
	buff_l = buff.split()
	qie_info = []
    # Sometimes the reading wasn't complete, so put some safeguards
	if len(buff_l) > 1:
		counter = buff_l[0]
		for elem in buff_l[1:]:
			# check that it's long enough
			if len(elem) == 10:
				qie_info.append(elem[:6])
				qie_info.append("0x"+elem[6:])

	return qie_info

def getInfoFromSpy_per_QIE(buff, verbose=False):

	BITMASK_TDC = 0x07
	OFFSET_TDC0 = 4
	OFFSET_TDC1 = 4+8

	BITMASK_ADC = 0x07
	OFFSET_ADC0 = 1
	OFFSET_ADC1 = 1+8
	
	BITMASK_EXP = 0x01
	OFFSET_EXP0 = 0
	OFFSET_EXP1 = 0+8

	BITMASK_CAP = 0x01
	OFFSET_CAP0 = 7
	OFFSET_CAP1 = 15

	int_buff = int(buff,16)

	if verbose:
		# get binary representation
		buff_bin = bin(int_buff)
		print "{0} -> {1}".format(buff, buff_bin)

	adc1 = int_buff >> OFFSET_ADC1 & BITMASK_ADC
	adc0 = int_buff >> OFFSET_ADC0 & BITMASK_ADC
	mantissa = interleave(adc0, adc1)

	tdc1 = int_buff >> OFFSET_TDC1 & BITMASK_TDC
	tdc0 = int_buff >> OFFSET_TDC0 & BITMASK_TDC
	tdc = interleave(tdc0, tdc1)
	
	exp1 = int_buff >> OFFSET_EXP1 & BITMASK_EXP
	exp0 = int_buff >> OFFSET_EXP0 & BITMASK_EXP
	exp = interleave(exp0, exp1)
	
	c0 = int_buff >> OFFSET_CAP0 & BITMASK_CAP
	c1 = int_buff >> OFFSET_CAP1 & BITMASK_CAP
	capid = interleave(c0, c1)


	if verbose:
		print "adc_0:", adc0, "; adc_1:", adc1, "; adc:", adc
		print "exp_0:", exp0, "; exp_1:", exp1, "; exp:", exp
		print "tdc_0:", tdc0, "; tdc_1:", tdc1, "; tdc:", tdc
		print "capid_0:", c0, "; capid_1:", c1, "; capid:", capid


        #print buff, capid
	return {'capid':capid,
		'adc':64*exp+mantissa,
		'man':mantissa,
		'exp':exp,
		'tdc':tdc}


def  getInfoFromSpy_per_card(port,host,crate, slot, isTop, card, subdetector="HF", verbose=False, Nsamples=None, clearBuffer=False, printAsTable=False, rawData=False):

	topbottom=isTop
	TB=['Bot','Top']
	output=[]

	if not (topbottom==0 or topbottom==1):
		print >> sys.stderr, 'ERROR: parameter isTop --- 1 for top, 0 for bottom'
		return output

	spyconts=readIglooSpy_per_card(port=port, host=host, crate=crate, slot=slot, topbottom=topbottom, card=card, subdetector=subdetector, Nsamples=Nsamples, verbose=verbose)

	if isTop or subdetector=="HE":
		startQIE=1
	else:
		startQIE=13

	if rawData:
		for spycontst in spyconts.values()[0]:
			outdire={}
			spycont=spycontst.split()
			nqie=0
			if verbose: print ' #{0} |'.format(str(int(spycont[0],16)).rjust(2," ")),
			for sc in spycont:
				print sc,
			print
	    

	if printAsTable:		
		if verbose:
			print "word |",
			for i in range(12):
				print "QIE {0}    |".format(str(i+startQIE).rjust(2," ")),
			print
			print "     |",
			for i in range(12):
				print "C ADC TDC |",
			print
		for spycontst in spyconts.values()[0]:
			outdire={}
			spycont=spycontst.split()
			nqie=0
			if verbose: print ' #{0} |'.format(str(int(spycont[0],16)).rjust(2," ")),

			for sc in spycont[1:]:
				outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[:-4]) if len(sc)>6 else getInfoFromSpy_per_QIE('0x0')
				data = outdire['qie{0}'.format(nqie)]
				if verbose: print "{0} {1} {2} |".format(data['capid'],str(data['adc']).rjust(3," "),str(data['tdc']).rjust(3," ")),
				nqie+=1
				outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[-4:]) if len(sc)>6 else (getInfoFromSpy_per_QIE(sc) if len(sc)>2 else getInfoFromSpy_per_QIE('0x0'))
				data = outdire['qie{0}'.format(nqie)]
				if verbose: print "{0} {1} {2} |".format(data['capid'],str(data['adc']).rjust(3," "),str(data['tdc']).rjust(3," ")),
				nqie+=1
        
			if verbose: print
			output.append(outdire)
	else:
		for spycontst in spyconts.values()[0]:
			outdire={}
			spycont=spycontst.split()
			nqie=0
			if verbose: print '\nspy_word #{0}\n'.format(int(spycont[0],16)),
			for sc in spycont[1:]:
				outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[:-4]) if len(sc)>6 else getInfoFromSpy_per_QIE('0x0')
				if verbose: print 'qie{0}\t'.format(nqie+startQIE),outdire['qie{0}'.format(nqie)]
				nqie+=1
				outdire['qie{0}'.format(nqie)]=getInfoFromSpy_per_QIE(sc[-4:]) if len(sc)>6 else (getInfoFromSpy_per_QIE(sc) if len(sc)>2 else getInfoFromSpy_per_QIE('0x0'))
				if verbose: print 'qie{0}\t'.format(nqie+startQIE),outdire['qie{0}'.format(nqie)]
				nqie+=1
			output.append(outdire)

    

	if verbose:
		if subdetector=="HF":
			leftn=sendngFECcommands(cmds=["get {0}-{1}-i{2}_StatusReg_InputSpyWordNum".format(crate, slot, TB[topbottom])],port=port,host=host)[0]
		elif subdetector=="HE":
			leftn=sendngFECcommands(cmds=["get {0}-{1}-{2}-i_StatusReg_InputSpyWordNum".format(crate, slot, card)],port=port,host=host)[0]
		print '\n',leftn['cmd'],'#',leftn['result']

	if not clearBuffer:
		print 'NOTE THAT THE SPY FIFO WILL RETAIN OLD DATA UNTIL YOU FLUSH IT OR RESET IT !'

	return output


## ----------------------
## -- Check the capids --
## ----------------------

def capidOK(parsed_info):
	capids = set()
	for info in parsed_info:
		capid = info['capid']
		capids.add(capid)

        #print capids
	return len(capids) == 1, capids

def checkCapid(prev, curr):
        result = True
        error = []
        if prev != -1:
                if prev == 3:
                        if curr != 0:
				result = False
				error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}.".format(prev, curr))
                        elif prev in [0,1,2]:
				if curr - prev != 1:
					result = False
					error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}.".format(prev, curr))
                        else:
				result = False
				error.append("Previous capid value ({0}) does not make sense.".format(prev))
        return result, error

def capidRotating(parsed_info_list):
    # check what the capid is for each reading, 
    # and make sure that the rotation is ok
    prev_capid = -1
    result = True
    error = []
    for i, parsed_info in enumerate(parsed_info_list):
        # parsed_info could be empty, or contain less than 12 items
        if len(parsed_info) == 0:
            # assume that all was fine
            if prev_capid != -1:
                if prev_capid == 3:
                    prev_capid = 0
                elif prev_capid in [0,1,2]:
                    prev_capid += 1

        else:
            # Check whether the capids were all the same
            capid = capidOK(parsed_info)
            if not capid[0]:
                result = False
                error.append("Not all capids were the same.")
            else:
                capid_value = list(capid[1])[0]
                if prev_capid != -1:
                    if prev_capid == 3:
                        if capid_value != 0:
                            result = False
                            error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}. (Line {2})".format(prev_capid, capid_value, i))
                    elif prev_capid in [0,1,2]:
                        if capid_value - prev_capid != 1:
                            result = False
                            error.append("Capid did not rotate correctly. Previously it was {0}, now it is {1}. (Line {2})".format(prev_capid, capid_value, i))
                    else:
                        result = False
                        error.append("Previous capid value ({0}) does not make sense.".format(prev_capid))
                
                prev_capid = capid_value

    return result, "\n".join(error)

if __name__ == "__main__":

	parser = OptionParser()
	parser.add_option("--sleep", dest="sleep",
			  default=10, metavar="N", type="float",
			  help="Sleep for %metavar minutes in between data runs (default: %default)",
			  )
	parser.add_option("--capidonly", dest="cid_only",
			  default = 0,
			  type="int",
			  help="1 = display CapID only,  0 = normal mode"
			  )
	parser.add_option("-n", "--numts", dest="nsamples",
			  default = 200,
			  type="int",
			  help="number of TS to capture -- 200 MAX"
			  )
	parser.add_option("-c", "--crate", "--rbx", dest="crate",
			  default="",
			  help="FE crate or RBX (default is -1)",
			  type="str"
			  )
	parser.add_option("-s", "--slot", "--rm", dest="slot",
			  default=-1,
			  help="FE slot or RM (default is -1)",
			  type="int"
			  )
	parser.add_option("--card", dest="card",
			  default=-1,
			  help="Card number within HE RM (default is 1).  This is only used for HE subdetector",
			  type="int"
			  )
	parser.add_option("--bx", dest="BX_forSpy",
			  default=0,
			  help="Select BX to start the spy at",
			  type="int"
			  )
	parser.add_option("-p", "--port", dest="port",
			  type="int",
			  default=-1,
			  help="ngccm server port (default if 63000 if HF subdetector is used, 64500 if HE subdetector is used)"
			  )
	parser.add_option("-H", "--host", dest="host",
			  type="str",
			  default="",
			  help="ngccm server host"
			  )
	parser.add_option("-k","--keep","--keepbuffer","--keepBuffer", dest="clearBuffer",
			  default=True,
			  action="store_false",
			  help="option to keep the igloo spy buffer, default is to clear it after a run"
			  )
	parser.add_option("--Top","--top", dest="top",
			  default=False, action="store_true",
			  help="Spy top igloo (default is to spy top igloo)",
			  )
	parser.add_option("--Bot","--bot", dest="bot",
			  default=False, action="store_true",
			  help="Spy bottom igloo (default is to spy top igloo)",
			  )
	parser.add_option("--HF","--hf", dest="hf",
			  default=False, action="store_true",
			  help="Run on HF subdetector (default is HF)",
			  )
	parser.add_option("--HE","--he", dest="he",
			  default=False, action="store_true",
			  help="Run on HE subdetector (default is HF)",
			  )
	parser.add_option("-r","--random","--randomBX", dest="randomBX",
			  default=False, action="store_true",
			  help="start spy buffer at a random value, rather than just prior to BC0"
			  )
	parser.add_option("--notable", dest="printAsTable",
			  default=True, action="store_false",
			  help="display information in raw format rather than in a table"
			  )
	parser.add_option("--raw", dest="rawData",
			  default=False, action="store_true",
			  help="print raw data for debugging purposes"
			  )
    
	
	(options, args) = parser.parse_args()


	port = options.port
	host = options.host

	crate = options.crate
	slot = options.slot
	card = options.card

        BX_forSpy = options.BX_forSpy
        if BX_forSpy < 0:
                BX_forSpy = BX_forSpy + 3564


        #check that only one igloo is specified
	if options.top and options.bot:
		print 'Please specify only one igloo, top or bottom, not both'
		print 'Exiting'
		sys.exit()

        #default igloo is top
	isTop = 1
	if options.bot:
		isTop = 0


        #check that only one igloo is specified
	if options.hf and options.he:
		print 'Please specify only one subdetector, HF or HE, not both'
		print 'Exiting'
		sys.exit()

	subdetector = "HF"
	if options.he:
		subdetector = "HE"
		
	if port==-1:
		if subdetector=="HF": port=63000
		if subdetector=="HE": port=64000

        if host=="":
		if subdetector=="HF": host="hcalngccm01"
		if subdetector=="HE": host="hcalngccm02"

        
	print 'Spying data from {0} subdetector'.format(subdetector)
	if subdetector == "HF":
		print '  Crate {0}'.format(crate)
		print '  Slot  {0}'.format(slot)
		if isTop:
			print '  Top FPGA'
		else:
			print '  Bottom FPGA'
	if subdetector == "HE":
		print '  RBX  {0}'.format(crate)
		print '  RM   {0}'.format(slot)
		print '  Card {0}'.format(card)


		
        #turns on the spy at fixed BX flag in the igloo (starts spy at 50 BX before BC0)
	if not options.randomBX:
		if subdetector=="HF":
			cmds = ["put {0}-{1}-i[Top,Bot]_SpyAtFixedBX 2*1".format(crate, slot),
                                "put {0}-{1}-i[Top,Bot]_BX_forSpy 2*{3}".format(crate, slot, card, BX_forSpy)] 
			output = sendngFECcommands(cmds=cmds, port=port, host=host)
		elif subdetector=="HE":
			cmds = ["put {0}-{1}-{2}-i_SpyAtFixedBX 1".format(crate, slot, card),
                                "put {0}-{1}-{2}-i_BX_forSpy {3}".format(crate, slot, card, BX_forSpy)]
			output = sendngFECcommands(cmds=cmds, port=port, host=host)



	getInfoFromSpy_per_card(crate=crate, slot=slot, port=port, host=host, isTop=isTop, card=card, subdetector=subdetector, verbose=True, Nsamples=options.nsamples, clearBuffer=options.clearBuffer, printAsTable=options.printAsTable, rawData=options.rawData)

	if options.clearBuffer:
		clear_buffer(crate=crate, slot=slot, card=card, port=port, host=host, subdetector=subdetector)

	if not options.randomBX:
		if subdetector=="HF":
			cmds = ["put {0}-{1}-i[Top,Bot]_SpyAtFixedBX 2*0".format(crate, slot)]
			output = sendngFECcommands(cmds=cmds, port=port, host=host)
		elif subdetector=="HE":
			cmds = ["put {0}-{1}-{2}-i_SpyAtFixedBX 0".format(crate, slot, card)]
			output = sendngFECcommands(cmds=cmds, port=port, host=host)


    
    
