from ROOT import *
gROOT.SetBatch()

import sys
from time import time, sleep
from datetime import datetime

from re import search, escape
import os
import subprocess
import pexpect

crateList = ['HFM01','HFM02','HFM03','HFM04','HFM05','HFM06','HFM07','HFM08',
	     'HFP01','HFP02','HFP03','HFP04','HFP05','HFP06','HFP07','HFP08']

if len(sys.argv)==2:
	frontEndCrate = sys.argv[-1]
	if not frontEndCrate in crateList:
		print 'Unknown crate'
		sys.exit()
else:
	print "Specify a front end crate as an argument"
	sys.exit()


frontEndCrates = [frontEndCrate]

expecteduHTRDict = { "HFM01":[(22,2),(22,1),(32,6)],
		     "HFM02":[(22,4),(22,3),(22,2)],
		     "HFM03":[(29,1),(22,6),(22,5)],
		     "HFM04":[(29,3),(29,2),(29,1)],
		     "HFM05":[(29,5),(29,4),(29,3)],
		     "HFM06":[(32,1),(29,6),(29,5)],
		     "HFM07":[(32,4),(32,3),(32,2)],
		     "HFM08":[(32,6),(32,5),(32,4)],
		     "HFP01":[(32,12),(22,7),(22,8)],
		     "HFP02":[(22,8),(22,9),(22,10)],
		     "HFP03":[(22,11),(22,12),(29,7)],
		     "HFP04":[(29,7),(29,8),(29,9)],
		     "HFP05":[(29,9),(29,10),(29,11)],
		     "HFP06":[(29,11),(29,12),(32,7)],
		     "HFP07":[(32,8),(32,9),(32,10)],
		     "HFP08":[(32,10),(32,11),(32,12)],
		     }


expecteduHTRList = expecteduHTRDict[frontEndCrate]

# frontEndCrates = ["HFM08"]
# expecteduHTRList = [(32,6),(32,5),(32,4)]

slotList = [3,4,5,6,10,11,12,13,14]


def read_histo(file_in="", sepCapID=True, qieRange = 0):
	result = {}
	tf = TFile(file_in, "READ")
	if sepCapID:
		rangeADCoffset = qieRange*64.
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = []
				info["rms"] = []
				for i_capID in range(4):
					offset = 64*(i_capID)
					th.GetXaxis().SetRangeUser(offset, offset+63)
					info["mean"].append(th.GetMean()-offset+rangeADCoffset)
					info["rms"].append(max(th.GetRMS(), 0.01))

				result[histNum] = info
		
	else:
		for i_link in range(24):
			for i_ch in range(4):
				histNum = 4*i_link + i_ch
				th = tf.Get("h{0}".format(histNum))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = th.GetMean()
				info["rms"] = th.GetRMS()

				result[histNum] = info

	tf.Close()
	return result

def send_commands(cmds=["quit"], script=False, raw=False, progbar=False, port = 4342, control_hub = "hcal904daq02"):
	# Arguments and variables
	output = []
	raw_output = ""
	if control_hub != False and port:		# Potential bug if "port=0" ... (Control_hub should be allowed to be None.)
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
		if control_hub != None:
			ngfec_cmd += " -H {0}".format(control_hub)
		
		# Send the ngfec commands:
		p = pexpect.spawn(ngfec_cmd)
		if not script:
			for i, c in enumerate(cmds):
				p.sendline(c)
				if c != "quit":
					t0 = time()
					p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(escape(c)))
					t1 = time()
					output.append({
						"cmd": c,
						"result": p.match.group(1).strip().replace("'", ""),
						"times": [t0, t1],
					})
					raw_output += p.before + p.after
		else:
			p.sendline("< {0}".format(file_script))
			for i, c in enumerate(cmds):
				# Deterimine how long to wait until the first result is expected:
				if i == 0:
					timeout = max([30, int(0.0075*len(cmds))])
				else:
					timeout = 30		# pexpect default
				# Send commands:
				t0 = time()
				p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(escape(c)), timeout=timeout)
				t1 = time()
#				print [p.match.group(0)]
				output.append({
					"cmd": c,
					"result": p.match.group(1).strip().replace("'", ""),
					"times": [t0, t1],
				})
				raw_output += p.before + p.after
			p.sendline("quit")

		p.expect(pexpect.EOF)
		raw_output += p.before
		p.close()
		if raw:
			return raw_output
		else:
			return output

def get_histo(crate, slot,sepCapID=True,iteration=0):
	histoCommand = "link hist int 1000 %i mappingHists/ped_%i_%i.root 0 quit quit quit"%(int(sepCapID),crate,slot)
	proc = subprocess.Popen("echo %s | uHTRtool.exe -c %i:%i"%(histoCommand,crate,slot),stdout=subprocess.PIPE,shell=True)
	sleep(1)

mapping = {}

for FEcrate in frontEndCrates:
	print FEcrate
	print expecteduHTRList
	cmds = []
	for slot in slotList:
		cmds += ['put {0}-{1}-QIE{1}_RangeSet 3'.format(FEcrate, slot, slot),
			 'put {0}-{1}-QIE{1}_FixRange 1'.format(FEcrate, slot, slot)]


#	print cmds
	send_commands(cmds=cmds, script=True, port=63000, control_hub="hcalvme04")
	sleep(3)
	uHTR_outputs = {}
    
	for uHTR in expecteduHTRList:
		uHTRcrate = uHTR[0]
		uHTRslot = uHTR[1]
    
        
		get_histo(uHTRcrate, uHTRslot, sepCapID=False)
		sleep(2)
		uHTR_outputs[uHTR]=read_histo("mappingHists/ped_{0}_{1}.root".format(uHTRcrate,uHTRslot),sepCapID=False)
    
	for uHTR in uHTR_outputs:
		for i in uHTR_outputs[uHTR]:
			if uHTR_outputs[uHTR][i]['mean']>100:
				link = int(i/24)*6
				thisSlot = i%24+1
				mapping["{0}-{1}".format(FEcrate,thisSlot)] = {"crate":uHTR[0],
									       "slot":uHTR[1],
									       "links":link
									       }
#		print mapping
    
	cmds = []
	for slot in slotList:
		cmds += ['put {0}-{1}-QIE[1-24]_RangeSet 24*0'.format(FEcrate, slot),
			 'put {0}-{1}-QIE[1-24]_FixRange 24*0'.format(FEcrate, slot)]
    
	send_commands(cmds=cmds, script=True, port=63000, control_hub="hcalvme04")

cardlist = mapping.keys()
cardlist = sorted(cardlist,key=lambda x: float(x.split('-')[-1]))
for m in cardlist:
    print "{0} {1}:{2} {3}-{4}".format(m, mapping[m]['crate'],mapping[m]['slot'],mapping[m]['links'],mapping[m]['links']+5)
    
