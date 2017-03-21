#from read_histo import *
from front_back_Map import *

from numpy import mean as numMean

from optparse import OptionParser

import subprocess

from ROOT import *
gROOT.SetBatch()

import sendCommands

from time import sleep
import os

if not os.path.exists("results_pedestalTuning"):
	os.mkdir("results_pedestalTuning")

nominalPedestal = 4

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
					th.GetXaxis().SetRangeUser(offset, offset+45)
#					print histNum, i_capID, offset, th.GetMean()
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
		


def get_histo(crate, slot,sepCapID=True,iteration=""):
	histoCommand = "link hist int 1000 %i results_pedestalTuning/ped_%i_%i_%s.root 0 quit quit quit"%(int(sepCapID),int(crate), int(slot),iteration)
	proc = subprocess.Popen("echo %s | uHTRtool.exe -c %i:%i"%(histoCommand,crate,slot),stdout=subprocess.PIPE,shell=True)
	sleep(2)

def plotCombined(crate, slot,name="",plotnum=99):
	get_histo(crate, slot,False,plotnum)
	tf = TFile("results_pedestalTuning/ped_{0}.root".format(plotnum), "READ")	
	h = tf.Get("h0")
	h.GetXaxis().SetRangeUser(0,20)
	for i in range(1,96):
		h.Add(tf.Get("h{0}".format(i)))

	c = TCanvas()
	c.SetLogy()
	h.Draw()
	c.SaveAs("results_pedestalTuning/ped_%s.png"%name)


def setToDefaults(uHTRCrate, uHTRSlot):
	cmds = []
	for card in range(4):
		pedestalDAC = [0x26]*24
		capIDPedestal = [[0,0,0,0]]*24
		qieCrate = mapping[uHTRCrate][uHTRSlot][card]['crate']
		qieSlot  = mapping[uHTRCrate][uHTRSlot][card]['slot']

		port = 63000
		host = 'hcalvme04'

		pedVals = ''
		capIDpedVals = ''
		for x in range(24):
			pedVals += '%i '%pedestalDAC[x]
			for y in range(4):
				capIDpedVals += '%i '%capIDPedestal[x][y]
		cmds += ['put {0}-{1}-QIE[1-24]_PedestalDAC {2}'.format(qieCrate, qieSlot, pedVals),
			 'put {0}-{1}-QIE[1-24]_CapID[0-3]pedestal {2}'.format(qieCrate, qieSlot, capIDpedVals)
			 ]
	sendCommands.send_commands(cmds, script = False, progbar = False,port=port, control_hub=host)










def tunePedestals(FEcrate):
	outputCMDfile = open("results_pedestalTuning/cmdsPedestalTuning_{0}.txt".format(FEcrate),"write")

	uHTRlist = expecteduHTRDict[FEcrate]

	for uHTR in uHTRlist:
		uHTRCrate = uHTR[0]
                uHTRSlot = uHTR[1]
                
                setToDefaults(uHTRCrate, uHTRSlot)
                beforeHist = TH1F("beforeTuning","beforeTuning",100,0,10)
                afterHist = TH1F("afterTuning","afterTuning",100,0,10)
                
                #plotCombined(uHTRCrate, uHTRSlot,"before",99)
                
                get_histo(uHTRCrate, uHTRSlot,True,"before")
                vals = read_histo("results_pedestalTuning/ped_%i_%i_before.root"%(int(uHTRCrate),int(uHTRSlot)),True,0)
#                print uHTR, vals
                for v in vals:
                	for i in range(4):
                		beforeHist.Fill(vals[v]['mean'][i])
                
                pedDACcmds = []
                port = 63000
                host = 'hcalvme04'
                for card in range(4):
                	pedestalDAC = [0x26]*24
                	capIDPedestal = [[0,0,0,0]]*24
                	qieCrate = mapping[uHTRCrate][uHTRSlot][card]['crate']
                	qieSlot  = mapping[uHTRCrate][uHTRSlot][card]['slot']

			if not qieCrate==FEcrate:
				continue
                	print "{0}:{1}".format(qieCrate,qieSlot)
                
                	
                	for i in range(24):
                		ih = card*24+i
                		pedVal = numMean(vals[ih]['mean'])
                		adjustPed = int(round((4-pedVal)/.666))
                
                		pedestalDAC[i] += adjustPed
                		vals[ih]['mean'] = [ x+0.666*adjustPed for x in vals[ih]['mean'] ]
                
                		capIDpedSetting = []
                		for j in range(4):
                			pedVal = vals[ih]['mean'][j]
                			adjustPed = int(round((4-pedVal)/.666))
                
                			if adjustPed > 7:
                				adjustPed = 7
                			if adjustPed < -7:
                				adjustPed = -7
                
                			if adjustPed > 0:
                				adjustPed += 8
                			else:
                				adjustPed = abs(adjustPed)
                
                			capIDpedSetting.append(adjustPed)
                			vals[ih]['mean'][j] = vals[ih]['mean'][j]+0.666*adjustPed
                
                		capIDPedestal[i] = capIDpedSetting
                
                	pedVals = ''
                	capIDpedVals = ''
                	for x in range(24):
                		pedVals += '%i '%pedestalDAC[x]
                		for y in range(4):
                			capIDpedVals += '%i '%capIDPedestal[x][y]
                	pedDACcmds += ['put {0}-{1}-QIE[1-24]_PedestalDAC {2}'.format(qieCrate, qieSlot, pedVals),
                		       'put {0}-{1}-QIE[1-24]_CapID[0-3]pedestal {2}'.format(qieCrate, qieSlot, capIDpedVals)
                		       ]
                
                
                for cmd in pedDACcmds:
                	print cmd
                	outputCMDfile.write("%s\n"%cmd)
                sendCommands.send_commands(pedDACcmds, script = False, progbar = False,port=port, control_hub=host)
                sleep(1)
                
                #plotCombined(uHTRCrate, uHTRSlot,"after",100)
                
                get_histo(uHTRCrate, uHTRSlot,True,"after")
                vals = read_histo("results_pedestalTuning/ped_%i_%i_after.root"%(int(uHTRCrate),int(uHTRSlot)),True,0)
		print uHTR, vals

                for v in vals:
                	for i in range(4):
                		afterHist.Fill(vals[v]['mean'][i])
                
        c = TCanvas()
        beforeHist.SetLineColor(kBlue)
        afterHist.SetLineColor(kRed)
        afterHist.Draw()
        beforeHist.Draw("same")
        c.SaveAs("results_pedestalTuning/pedDist_{0}.png".format(FEcrate))
        
        outputCMDfile.close()



if __name__ == "__main__":

	parser = OptionParser()
	parser.add_option("-c", "--crate", dest="crates",
			  default="",
			  help="FE crate (default is -1)",
			  type="str"
			  )

	(options, args) = parser.parse_args()

	if not(options.crates[0]=='[' and options.crates[-1]==']'):
		options.crates = '["'+options.crates.replace(',','","')+'"]'
	print options.crates
	fe_crates = eval(options.crates)


	for crate in fe_crates:
		print crate
		tunePedestals(crate)

