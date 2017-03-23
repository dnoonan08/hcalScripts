##############################################
# at_reg.py -
#    A script to test the registers of a QIE card.
#
# Author: O. Kamer Koseyan - Novemer 11 - 12, 2015
##############################################

import sys
import os
import sqlite3
from random import randint
# from hcal_teststand import *
# from hcal_teststand.utilities import logger
# from hcal_teststand.hcal_teststand import teststand

from ROOT import *
gROOT.SetBatch(True)
#gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")
from optparse import OptionParser
import subprocess
import pexpect
from time import time, sleep
from datetime import date, datetime
from re import search, escape

from ngccmServerInfo import *


import sendCommands
UID_SN_DB = sqlite3.connect("/nfshome0/dnoonan/serialNumberToUIDmap.db")
cursor = UID_SN_DB.cursor()

v = False
names = []			# List of names ordered as in registers list.
# fe_crate = 13
# fe_slot = 2
n = 5 #at.n
errdic = {}


def setQIEDefaults(crate, slot):

    port = serverLocations[int(crate)]['port']
    host = serverLocations[int(crate)]['host']
    
    cmds  = ['put HF{0}-{1}-B_Igloo_VDD_Enable 1'.format(crate,slot),
             'put HF{0}-{1}-B_Top_RESET_N 1'.format(crate,slot),
             'put HF{0}-{1}-B_Top_TRST_N 1'.format(crate,slot),
             'put HF{0}-{1}-B_Bottom_RESET_N 1'.format(crate,slot),
             'put HF{0}-{1}-B_Bottom_TRST_N 1'.format(crate,slot),
             # 'put HF{0}-{1}-iTop_CntrReg_InternalQIER 0'.format(crate,slot),
             # 'put HF{0}-{1}-iBot_CntrReg_InternalQIER 0'.format(crate,slot),
             ]
    
    cmds += ["put HF{0}-{1}-iTop_AddrToSERDES 0".format(crate,slot),
             "put HF{0}-{1}-iTop_CntrReg_CImode 0".format(crate,slot),
             # "put HF{0}-{1}-iTop_CntrReg_InternalQIER 0".format(crate,slot),
             # "put HF{0}-{1}-iTop_CntrReg_OrbHistoClear 0".format(crate,slot),
             # "put HF{0}-{1}-iTop_CntrReg_OrbHistoRun 0".format(crate,slot),
             "put HF{0}-{1}-iTop_CntrReg_WrEn_InputSpy 0".format(crate,slot),
             "put HF{0}-{1}-iTop_CtrlToSERDES_i2c_go 0".format(crate,slot),
             "put HF{0}-{1}-iTop_CtrlToSERDES_i2c_write 0".format(crate,slot),
             "put HF{0}-{1}-iTop_DataToSERDES 0".format(crate,slot),
             "put HF{0}-{1}-iTop_LinkTestMode 0".format(crate,slot),
             "put HF{0}-{1}-iBot_AddrToSERDES 0".format(crate,slot),
             "put HF{0}-{1}-iBot_CntrReg_CImode 0".format(crate,slot),
             # "put HF{0}-{1}-iBot_CntrReg_InternalQIER 0".format(crate,slot),
             # "put HF{0}-{1}-iBot_CntrReg_OrbHistoClear 0".format(crate,slot),
             # "put HF{0}-{1}-iBot_CntrReg_OrbHistoRun 0".format(crate,slot),
             "put HF{0}-{1}-iBot_CntrReg_WrEn_InputSpy 0".format(crate,slot),
             "put HF{0}-{1}-iBot_CtrlToSERDES_i2c_go 0".format(crate,slot),
             "put HF{0}-{1}-iBot_CtrlToSERDES_i2c_write 0".format(crate,slot),
             "put HF{0}-{1}-iBot_DataToSERDES 0".format(crate,slot),
             "put HF{0}-{1}-iBot_LinkTestMode 0".format(crate,slot),
             ]
    

    cmds += ["put HF{0}-{1}-QIE[1-24]_Lvds 24*1".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_Trim 24*2".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_DiscOn 24*1".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_TGain 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_TimingThresholdDAC 24*0xff".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_TimingIref 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_PedestalDAC 24*0x26".format(crate, slot),    
             "put HF{0}-{1}-QIE[1-24]_CapID0pedestal 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_CapID1pedestal 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_CapID2pedestal 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_CapID3pedestal 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_FixRange 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_RangeSet 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_ChargeInjectDAC 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_RinSel 24*7".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_Idcset 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_CalMode 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_CkOutEn 24*1".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_TDCMode 24*0".format(crate, slot),
             "put HF{0}-{1}-QIE[1-24]_PhaseDelay 24*0".format(crate, slot),
             "put HF{0}-{1}-Qie[1-24]_ck_ph 24*0".format(crate, slot),
             ]

    output = sendCommands.send_commands(cmds, script = False, progbar = False,port=port, control_hub=host)

    goodReset = True
    for entry in output:
        if not 'OK' in entry['result']:
            print entry
            goodReset = False

    return goodReset

def rand(size = 1):
	output = ''

	if size % 32:
		output += hex(randint(0, 2**(size % 32-1))) + ' '
	for i in range(int(size/32)):
		output += hex(randint(0, 2**32-1)) + ' '

	return output[:-1]

def register(name = None, size = 1, n = 5, multQIEs = False):
	cmds = []
	for i in range(n):
		r = ''
		if multQIEs:
			for i in range(24):
				r += '{0} '.format(rand(size))
		else:
			r = rand(size)
		cmds += ['put {0} {1}'.format(name, r),'get {0}'.format(name)]
		# cmds += ['put {0} {1}'.format(name, r), 'wait','get {0}'.format(name), 'wait']
	return cmds

def create_plots(info = [-1,-1,'0x00000000 0x00000000'],names = None, dic = None, k = 1):

    
        uID = info[-1]
        sernumber = cursor.execute("select serial from UIDtoSerialNumber where uid=?",(uID,)).fetchone()
                
        if type(sernumber)==type(tuple()):
            serialnumber = '500'+str(sernumber[0])
        else:
            serialnumber = '500999'

	outputDir = 'registerTestResults/%s__%s'%(serialnumber,info[2].replace(' ','_'))
	if not os.path.exists(outputDir):
		os.mkdir(outputDir)
	outputDir = 'registerTestResults/%s__%s/%s'%(serialnumber,info[2].replace(' ','_'),str(date.today()))
	if not os.path.exists(outputDir):
		os.mkdir(outputDir)

	outFile = TFile("{0}/HF{1}-{2}_{3}_{4}.root".format(outputDir,str(info[0]),info[1],info[2].replace(' ','_'),serialnumber),'recreate')
	gROOT.SetStyle("Plain")
	gStyle.SetOptStat(0)
        canvas = TCanvas()#"regTest","regTest",1200,600)
	canvas.Divide(1, k)
        canvas.SetBottomMargin(0.3)
	tothist = []
	rwhist = []
	xhist = []
	stacks = []
	for i in range(k):
		namespart = names[i*len(names)/k: (i+1)*len(names)/k]	# On (i+1)*len(names)/n, first i*len(names) is done, then the division by n. By that way, i = k - 1 => (i+1)*len(names)/k = len(names). So we don't lose any bins because of integer division.
		tothist.append(TH1F("Total_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		rwhist.append(TH1F("R/W_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		xhist.append(TH1F("Exec_{0}".format(i+1), "", len(namespart), -0.5, len(namespart)-0.5))
		stacks.append(THStack("Error_{0}".format(i+1), ""))
		tothist[i].SetFillColor(kGreen)
		rwhist[i].SetFillColor(kRed)
		xhist[i].SetFillColor(kOrange)
		for j, name in enumerate(namespart):
			tothist[i].GetXaxis().SetBinLabel(j+1, name)
			rwhist[i].GetXaxis().SetBinLabel(j+1, name)
			xhist[i].GetXaxis().SetBinLabel(j+1, name)
			tothist[i].Fill(j, dic[name][1][0])
			rwhist[i].Fill(j, dic[name][1][1])
			xhist[i].Fill(j, dic[name][1][2])
                tothist[i].GetXaxis().LabelsOption("vd")
		rwhist[i].GetXaxis().LabelsOption("vd")
		xhist[i].GetXaxis().LabelsOption("vd")
		canvas.cd(i + 1)
#		gPad.SetBottomMargin(-10)
#		gPad.SetLogy(1)
		tothist[i].GetXaxis().SetLabelOffset(0.02)
		tothist[i].Write()
		rwhist[i].Write()
		xhist[i].Write()
		stacks[i].Add(rwhist[i])
		stacks[i].Add(xhist[i])
		stacks[i].Write()
		tothist[i].SetMaximum(1.15*n)
		tothist[i].SetMinimum(0)
		stacks[i].SetMaximum(1.15*n)
		stacks[i].SetMinimum(0)
		tothist[i].Draw()
		stacks[i].Draw("SAME")
                        



	canvas.SaveAs("{0}/HF{1}-{2}_{3}.pdf".format(outputDir,info[0],info[1],info[2].replace(' ','_')))
	canvas.SaveAs("{0}/HF{1}-{2}_{3}.png".format(outputDir,info[0],info[1],info[2].replace(' ','_')))


        
        # canvas.SetBottomMargin(0)
        canvas = TCanvas()
        for j, name in enumerate(namespart):
            if dic[name][2]==24*[0]:
                continue
            
            canvas.Clear()
            QI = []
            text = TLatex()
            text.SetTextAlign(12)
            text.SetTextSize(0.07)
            text.DrawText(0.3,0.9,name)

            text.SetTextSize(0.04)
            for i_qie in range(12):
                QI.append(TBox( .02+(i_qie*.08) , .6 , .09+(i_qie*.08), .7))
                QI[-1].SetLineColor(kBlack)
                if dic[name][2][i_qie]>0:
                    QI[-1].SetFillColor(kRed)
                else:
                    QI[-1].SetFillColor(kGreen)
                QI[-1].Draw('l')
            for i_qie in range(12,24):
                QI.append(TBox( .02+((i_qie-12)*.08) , .4 , .09+((i_qie-12)*.08), .5))
                QI[-1].SetLineColor(kBlack)
                if dic[name][2][i_qie]>0:
                    QI[-1].SetFillColor(kRed)
                else:
                    QI[-1].SetFillColor(kGreen)
                QI[-1].Draw('l')

            for i_qie in range(9):
                text.DrawText( .05+(i_qie*.08) , .65, "%i"%(i_qie+1))
            for i_qie in range(9,12):
                text.DrawText( .04+(i_qie*.08) , .65, "%i"%(i_qie+1))
            for i_qie in range(12,24):
                text.DrawText( .04+((i_qie-12)*.08) , .45, "%i"%(i_qie+1))

            canvas.SaveAs("{0}/HF{1}-{2}_{3}_{4}.pdf".format(outputDir,info[0],info[1],info[2].replace(' ','_'),name.replace('[1-24]','')))
            canvas.SaveAs("{0}/HF{1}-{2}_{3}_{4}.png".format(outputDir,info[0],info[1],info[2].replace(' ','_'),name.replace('[1-24]','')))
                
	outFile.Write()
	outFile.Close()
	return 0

def registerTest(fe_crate, fe_slot):


        port = serverLocations[int(fe_crate)]['port']
        host = serverLocations[int(fe_crate)]['host']

	output = sendCommands.send_commands(cmds = 'get HF{0}-{1}-UniqueID'.format(fe_crate, fe_slot), script = False, progbar = False, port=port, control_hub=host)
	uID = "%s %s"%(output[0]['result'].split()[1],output[0]['result'].split()[2])


	print 'HF {0}, Slot {1}, UniqueId {2}'.format(fe_crate, fe_slot, uID)

	names = []
	registers = []			# List of commands to be sent to ngFEC tool
        errdic = {}
	registers.extend(
 		register("HF{0}-{1}-QIE[1-24]_Lvds".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_Trim".format(fe_crate, fe_slot), 2, n, True) +			# 2 bits
		register("HF{0}-{1}-QIE[1-24]_DiscOn".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_TGain".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_TimingThresholdDAC".format(fe_crate, fe_slot), 8, n, True) +	# 8 bits
		register("HF{0}-{1}-QIE[1-24]_TimingIref".format(fe_crate, fe_slot), 3, n, True) +		# 3 bits
		register("HF{0}-{1}-QIE[1-24]_PedestalDAC".format(fe_crate, fe_slot), 6, n, True) +		# 6 bits
		register("HF{0}-{1}-QIE[1-24]_CapID0pedestal".format(fe_crate, fe_slot), 4, n, True) +		# 4 bits
		register("HF{0}-{1}-QIE[1-24]_CapID1pedestal".format(fe_crate, fe_slot), 4, n, True) +		# 4 bits
		register("HF{0}-{1}-QIE[1-24]_CapID2pedestal".format(fe_crate, fe_slot), 4, n, True) +		# 4 bits
		register("HF{0}-{1}-QIE[1-24]_CapID3pedestal".format(fe_crate, fe_slot), 4, n, True) +		# 4 bits
		register("HF{0}-{1}-QIE[1-24]_FixRange".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_RangeSet".format(fe_crate, fe_slot), 2, n, True) +			# 2 bits
		register("HF{0}-{1}-QIE[1-24]_ChargeInjectDAC".format(fe_crate, fe_slot), 3, n, True) +		# 3 bits
		register("HF{0}-{1}-QIE[1-24]_RinSel".format(fe_crate, fe_slot), 4, n, True) +			# 4 bits
		register("HF{0}-{1}-QIE[1-24]_Idcset".format(fe_crate, fe_slot), 5, n, True) +			# 5 bits
		register("HF{0}-{1}-QIE[1-24]_CalMode".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_CkOutEn".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-QIE[1-24]_TDCMode".format(fe_crate, fe_slot), 1, n, True) +			# 1 bit
		register("HF{0}-{1}-Qie[1-24]_ck_ph".format(fe_crate, fe_slot), 4, n, True)			# 4 bits
		)

	registers.extend(
		### Top:
		register("HF{0}-{1}-iTop_CntrReg_CImode".format(fe_crate, fe_slot), 1, n) +			# 1 bit
		# register("HF{0}-{1}-iTop_CntrReg_OrbHistoClear".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		# register("HF{0}-{1}-iTop_CntrReg_OrbHistoRun".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iTop_CntrReg_WrEn_InputSpy".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iTop_AddrToSERDES".format(fe_crate, fe_slot), 16, n) +			# 16 bits
		register("HF{0}-{1}-iTop_CtrlToSERDES_i2c_go".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iTop_CtrlToSERDES_i2c_write".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iTop_DataToSERDES".format(fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HF{0}-{1}-iTop_LinkTestMode".format(fe_crate, fe_slot), 8, n) +			# 8 bits
		### Bottom:
		register("HF{0}-{1}-iBot_CntrReg_CImode".format(fe_crate, fe_slot), 1, n) +			# 1 bit
		# register("HF{0}-{1}-iBot_CntrReg_OrbHistoClear".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		# register("HF{0}-{1}-iBot_CntrReg_OrbHistoRun".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iBot_CntrReg_WrEn_InputSpy".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iBot_AddrToSERDES".format(fe_crate, fe_slot), 16, n) +			# 16 bits
		register("HF{0}-{1}-iBot_CtrlToSERDES_i2c_go".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iBot_CtrlToSERDES_i2c_write".format(fe_crate, fe_slot), 1, n) +		# 1 bit
		register("HF{0}-{1}-iBot_DataToSERDES".format(fe_crate, fe_slot), 32, n) +			# 32 bits
		register("HF{0}-{1}-iBot_LinkTestMode".format(fe_crate, fe_slot), 8, n) 			# 8 bits
		)

	for reg in registers[1::2*n]:
		names.extend([reg[4:]])

        output = sendCommands.send_commands(cmds = registers, script = False, progbar = True,control_hub=host,port=port)
        # output = ngFECcommands(cmds = registers)

	errlist = []
	totaltests = 0
	rwerr = 0
	xerr = 0
#        print output
        lastCmd = ''
	for i, (put, get) in enumerate(zip(output[::2], output[1::2])):
#		if ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', ''):
                if not get['cmd'][4:]== lastCmd:
                        badChannels = 24*[0]
                lastCmd = get['cmd'][4:]
		totaltests += 1
                
		if 'ERROR' in put['result'] or 'ERROR' in get['result']:
			xerr += 1
		elif ' '.join(put['cmd'].split()[2:]).replace('0x', '') != get['result'].replace('0x', ''):
			rwerr += 1
			errlist.append([' '.join(put['cmd'].split()[2:]).replace('0x', ''), get['result'].replace('0x', '')])
                        putList = ' '.join(put['cmd'].split()[2:]).replace('0x', '').split()
                        getList = get['result'].replace('0x', '').split()

                        for j in range(len(putList)):
                            if not putList[j]==getList[j]:
                                badChannels[j] = 1

		if 'ERROR' in put['result']:
			errlist.append([put['cmd'], put['result']])
		if 'ERROR' in get['result']:
			errlist.append([get['cmd'], get['result']])
		if not (i+1) % n:
			errdic.update({get['cmd'][4:]: [errlist, [totaltests, rwerr, xerr],badChannels]})
			errlist = []
			totaltests = 0
			rwerr = 0
			xerr = 0

#---------------Last report of errors------------------
	print "\n====== SUMMARY ============================"
	passedTests = True


	if errdic.values().count([[], [n, 0, 0],24*[0]]) == len(names):
		print '[OK] There were no errors.'
	else:
		print 'R/W errors (put != get):'
		passedTests = False
		for name in names:
			for error in errdic[name][0]:
				if (error[0] != error[1] and not 'ERROR' in error[1]):
					print '\t*Register: ' + name + ' -> Data: 0x' + error[0].replace(' ', ' 0x') + ' != 0x' + error[1].replace(' ', ' 0x')

		print '\nExecution errors:'
		for name in names:
			for error in errdic[name][0]:
				if 'ERROR' in error[1]:
					print '\t*Command: ' + error[0] + ' -> Result: ' + error[1]
	print "===========================================\n"


#---------------Create histogram-----------------------
	create_plots([fe_crate, fe_slot, uID],names, errdic, 2)

# 	if v:
# 		for put, get in zip(output[::2], output[1::2]):
# 			if ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', '') and not 'ERROR' in put['result']:
# #				at.silentlog('[OK] :: {0} -> {1} == {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
# 			elif 'ERROR' in get['result']:
# 				at.silentlog('[!!] :: {0} -> {1} != {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], get['result']))
# 			elif ' '.join(put['cmd'].split()[2:]).replace('0x', '') == get['result'].replace('0x', '') and 'ERROR' in put['result']:
# 				at.silentlog('[!!] :: {0} -> {1} == {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
# 			else:
# 				at.silentlog('[!!] :: {0} -> {1} != {2} -> {3}\n'.format(put['cmd'], put['result'], get['cmd'], '0x' + get['result'].replace('0x', '').replace(' ', ' 0x')))
# 		print '\nPrinting raw comparisons into file: [OK]'
# 	else:
# 		print

	# print 'Issuing backplane reset (to clear random values written to registers)'
	# print
	# reset_commands = ['put HF{0}-{1}-bkp_reset 0'.format(fe_crate, fe_slot),
	# 	    'put HF{0}-{1}-bkp_reset 1'.format(fe_crate, fe_slot),
	# 	    'put HF{0}-{1}-bkp_reset 0'.format(fe_crate, fe_slot)]

	# output = ngfec.send_commands(ts, cmds = reset_commands, script = False, progbar = False)
	#if not passedTests: sys.exit(1)

if __name__ == "__main__":
        

        parser = OptionParser()
        parser.add_option("-c", "--fecrate", dest="c",
                          default=-1,
                          help="FE crate (default is -1)",
                          metavar="STR"
                          )
        parser.add_option("-s", "--feslot", dest="s",
                          default="-1",
                          help="FE slot, can be integer or list of integers comma separated without spaces (default is -1)",
                          metavar="STR"
                          )
        
        (options, args) = parser.parse_args()
        fe_crate = options.c
        if ',' in options.s and not(options.s[0]=='[' and options.s[-1]==']'):
                options.s = '['+options.s+']'
        fe_slot = eval(options.s)
        
        if fe_crate == -1:
                print 'specify a crate number'
                sys.exit()


        port = serverLocations[int(fe_crate)]['port']
        host = serverLocations[int(fe_crate)]['host']

        if fe_slot == -1:
                cmd = 'get HF{0}-[1,2,3,4,5,6,7,9,10,11,12,13,14]-bkp_temp_f'.format(fe_crate)
                output = sendCommands.send_commands(cmds = cmd,port=port,control_hub=host)[0]
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
            

	outputDir = 'registerTestResults'
	if not os.path.exists(outputDir):
		os.mkdir(outputDir)
	# outputDir = 'registerTestResults/%s'%str(date.today())
	# if not os.path.exists(outputDir):
	# 	os.mkdir(outputDir)
        print 'Running over slots', filledSlots
        for i_slot in filledSlots:
            print 'Slot %i'%i_slot
            registerTest(fe_crate, i_slot)
            setQIEDefaults(fe_crate, i_slot)

