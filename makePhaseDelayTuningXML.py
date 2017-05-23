## This script is designed to read in the previous XML file, and the CSV file that is created for the phase tuning (created by A. Buccilli) and outputs a new tuned XML
## The CSV file contains the required relative shift (in ns) of the pulses
## The old XML file is read-in, the relative shift is applied, and the new file is created with a new creationTag based on the current date

import sys

import xml.etree.ElementTree as ET
from changeHFCoordinates import FEToDetector

import csv

if not len(sys.argv)==3:
    print "the script is expecting exactly two arguments, the first being the previous xml file, and the second being the phase change csv file"
    print "%i arguments provided, exiting"%(len(sys.argv)-1)
    sys.exit()


oldXML = sys.argv[1]
phaseChangeCSVFile = sys.argv[2]

# oldXML = "/nfshome0/dnoonan/MakeXML/XML/ngHF/phaseDelay_HF_centered84.xml"
# phaseChangeCSVFile = "/nfshome0/dnoonan/170518_hf_timing_channel_corrections.txt"

from datetime import date                                                                                                                   
def loadChangeCSVFile(csvFileName):
    reader = csv.reader(open(csvFileName, 'r'))
    phaseDelayChange = {}
    for row in reader:
        eta,phi,depth, N, maxBin, deltaNS = [int(x) for x in row[:-2]] + [float(x) for x in row[-2:]] 
        if not eta in phaseDelayChange:
            phaseDelayChange[eta] = {}
        if not phi in phaseDelayChange[eta]:
            phaseDelayChange[eta][phi] = {}

        phaseDelayChange[eta][phi][depth] = int(deltaNS*2)

    return phaseDelayChange


print "Reading phase delay change file"
phaseDelayChange = loadChangeCSVFile(phaseChangeCSVFile)


NewTag = "phaseTuning_"+date.today().strftime("%d-%m-%Y")


tree = ET.parse(oldXML)
root = tree.getroot()

print "Reading old XML file"

for crateBlock in root:
    RBX = ''
    for value in crateBlock:
        if value.tag=="Parameter":
            if value.attrib["name"]=="RBX":
                RBX = value.text
                print "   ", RBX
            if value.attrib["name"]=="CREATIONTAG":
                value.text = NewTag
        if value.tag=="Data":
            card = int(value.attrib["card"])
            qie = int(value.attrib["qie"])
            side,eta,phi,depth = FEToDetector(crate = RBX, slot = int(card), channel = int(qie),verbose=False)[0]
            eta = eta*side

            oldPhase = int(value.text)
            phaseDelta = phaseDelayChange[eta][phi][depth]
            newPhase = oldPhase + phaseDelta

            
            if newPhase < 64 and newPhase > 49:
                if phaseDelta < 0:
                    newPhase  = newPhase-14
                if phaseDelta > 0:
                    newPhase  = newPhase+14

                
            value.text = str(newPhase)

print "Creating new XML file"
newXMLFileName = "phaseDelay_HF_%s.xml"%(date.today().strftime("%d-%m-%Y"))
tree.write(newXMLFileName)
