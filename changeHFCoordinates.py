import sqlite3
import sys
DB_name = "/Users/dnoonan/Work/CMS/HCAL_HF/Mapping/ngHF2017LMap_20170206_pre05.db"

hf_lmap_db = sqlite3.connect(DB_name)
hf_lmap_db.text_factory = str

cursor = hf_lmap_db.cursor()

trunkSector = {14191:28,
               14192:30,
               14193:34,
               14194:2 ,
               14195:6 ,
               14196:10,
               14197:14,
               14198:18,
               14199:22,
               14200:26,
               14201:28,
               14202:30,
               14203:34,
               14204:2 ,
               14205:6 ,
               14206:10,
               14207:14,
               14208:18,
               14209:22,
               14210:26,
               }               
               

def printFECoordinates(crate, slot, channel):
    print "  --Crate   {0}".format(crate)
    print "    Slot    {0}".format(slot)
    print "    Channel {0}".format(channel)

def printDetectorCoordinates(side, eta, phi, depth):
    print "  --Side {0}".format(side)
    print "    Eta  {0}".format(eta)
    print "    Phi  {0}".format(phi)
    print "    Dep  {0}".format(depth)

def printBECoordinates(crate, uHTR, uHTR_FI, fiber_channel):
    print "  --uHTR    {0}:{1}".format(crate,uHTR)
    print "    Fiber   {0}".format(uHTR_FI)
    print "    Channel {0}".format(fiber_channel)

def printAllInfo(values):
    a = "Side    Eta     Phi     dPhi    Depth   Det     ngRBX   Wedge   PMTBx   PMTtype W_Cable Tower   PMT     BaseBrd Anode   S_PMT   S_QIE   R_PMT   R_QIE   QIE10   QIETB   QIECH   QIEFI   FI_CH   Tr_FI   nCable  MTP     Crate   uHTR    uHTR_Rx uHTR_FI FEDid   QIEID"
    
    print a
    b = a.split()

    for v in values:
        printline = ""
        for i in range(len(v)):
            if not i+1==len(v):
                printline += "{0}".format(str(v[i]).ljust(8))
            else:
                printline +="{0}".format(v[i])
        print printline


def DetectorToFE(eta=0, phi=0, side=0, depth=0,verbose=True):
    """
    Converts Eta Phi coordinates to front end crate slot channel coordinates
    Returns a list of detector coordinates (crate, slot, channel) that correspond to the eta/phi coordinates provided
    """


    if side==0:
        if int(eta) > 0:
            side = 1
        if int(eta) < 0:
            side = -1

    if int(eta) < 0:
        eta = abs(int(eta))

    if depth==0:
        depth="'%'"

    values = cursor.execute("select ngRBX, QIE10, QIECH from ngHF_Mapping where Side like {0} and Eta like {1} and Phi like {2} and Depth like {3}".format(side, eta, phi, depth)).fetchall()
    if verbose:
        for v in values:
            print 
            printFECoordinates(v[0],v[1],v[2])

    return values

def DetectorToBE(eta=0, phi=0, side=0, depth=0,verbose=True):
    """
    Converts Eta Phi coordinates to back end uHTR crate slot channel coordinates
    Returns a list of detector coordinates (uHTR crate, slot, channel) that correspond to the eta/phi coordinates provided
    """


    if side==0:
        if int(eta) > 0:
            side = 1
        if int(eta) < 0:
            side = -1

    if int(eta) < 0:
        eta = abs(int(eta))

    if depth==0:
        depth="'%'"
        
    values = cursor.execute("select distinct Crate, uHTR, uHTR_FI, FI_CH from ngHF_Mapping where Side like {0} and Eta like {1} and Phi like {2} and Depth like {3}".format(side, eta, phi, depth)).fetchall()

    if verbose:
        for v in values:
            print             
            printBECoordinates(v[0],v[1],v[2],v[3])

    return values

def FEToDetector(crate="HFP01",slot=3,channel=1,verbose=True):
    """
    Converts front end coordinates (crate, channel, slot) to detector coordinates (side, eta, phi, depth)
    Returns a list of detector coordinates (side, eta, phi, depth) that correspond to the eta/phi coordinates provided
    """
    values = cursor.execute("select side, eta, phi, depth from ngHF_Mapping where ngRBX=? and QIE10=? and QIECH=?",(crate,slot,channel)).fetchall()
    if verbose:
        for v in values:
            print 
            printDetectorCoordinates(v[0],v[1],v[2],v[3])

    return values
    

def printFullMapInfo(Eta, Phi):
    values = cursor.execute("select * from ngHF_Mapping where Eta=? and Phi=?",(Eta, Phi)).fetchall()
    printAllInfo(values)


def FEToBE(crate="HFP01", slot=3, channel=-1, verbose=True):

    if channel==-1:
        values = cursor.execute("select distinct Crate, uHTR from ngHF_Mapping where ngRBX=? and QIE10=?",(crate,slot)).fetchall()
        if verbose:
            print "uHTR {0}:{1}".format(values[0][0],values[0][1])
        return values[0][0],values[0][1]

    else:
        values = cursor.execute("select distinct Crate, uHTR, uHTR_FI, FI_CH from ngHF_Mapping where ngRBX=? and QIE10=? and QIECH=?",(crate,slot,channel)).fetchall()
        if verbose:
            print "uHTR {0}:{1} link {2} channel {3}".format(values[0][0],values[0][1],values[0][2],values[0][3])
        return values[0][0],values[0][1],values[0][2],values[0][3]


def printWinchesterCablingMap_FE(crate):
    
    values = cursor.execute("select distinct ngRBX, QIE10, QIETB, PMTBx, W_Cable from ngHF_Mapping where ngRBX='{0}'".format(crate)).fetchall()
    print crate
    print      "Slot  1   2     3      4      5      6    7   8   9    10     11     12     13     14"
    for con in ["TOP","BOT"]:
        line = "{0} |   |   |".format(con)
        for i_slot in [3,4,5,6]:
            for val in values:
                if val[1]==i_slot and val[2]==con:
                    line += " {0}-{1} |".format(str(val[3]).rjust(2),val[4])
        line += "   |   |   |" 
        for i_slot in [10,11,12,13,14]:
            for val in values:
                if val[1]==i_slot and val[2]==con:
                    line += " {0}-{1} |".format(str(val[3]).rjust(2),val[4])
        print line


def printWinchesterCablingMap():
    crateList = ['HFP01','HFP02','HFP03','HFP04','HFP05','HFP06','HFP07','HFP08',
                 'HFM01','HFM02','HFM03','HFM04','HFM05','HFM06','HFM07','HFM08']

    for crate in crateList:
        printWinchesterCablingMap_FE(crate)
        print

def printFEtoUHTRMap():
    uHTRCrates = [22,29,32]

    info = {}

    for Crate in uHTRCrates:
        info[Crate]={}
        for uHTR in [1,2,3,4,5,6,7,8,9,10,11,12]:
            info[Crate][uHTR]=[]
            for link in [0,6,12,18]:
                values = cursor.execute('select distinct Crate, uHTR, ngRBX, QIE10, PMTBx, Wedge, side from ngHF_Mapping where Crate={0} and uHTR={1} and uHTR_FI={2}'.format(Crate,uHTR,link)).fetchall()
                info[Crate][uHTR].append(values[0][2:])


    for Crate in uHTRCrates:
        print "uTCA Crate {0}".format(Crate)
        output = "Links |".format(Crate)
        for i in range(12):
            output += "{0}|".format(str(i+1).center(10))
        print output
        outputLine0  = ' 0-5  |'
        outputLine6  = ' 6-11 |'
        outputLine12 = '12-17 |'
        outputLine18 = '18-23 |'
        outputPMT    = 'PMTBx |'
        outputWedge  = 'Wedge |'



        for i in range(1,13):
            outputLine0  += "{0}:{1}".format(info[Crate][i][0][0],info[Crate][i][0][1]).center(10)
            outputLine6  += "{0}:{1}".format(info[Crate][i][1][0],info[Crate][i][1][1]).center(10)
            outputLine12 += "{0}:{1}".format(info[Crate][i][2][0],info[Crate][i][2][1]).center(10)
            outputLine18 += "{0}:{1}".format(info[Crate][i][3][0],info[Crate][i][3][1]).center(10)
            outputPMT    += "{0}/{1}".format(int(info[Crate][i][1][2])*int(info[Crate][i][3][4]),int(info[Crate][i][3][2])*int(info[Crate][i][3][4])).center(10)
            outputWedge  += "{0}".format(int(info[Crate][i][3][3])*int(info[Crate][i][3][4])).center(10)
            outputLine0  += "|"
            outputLine6  += "|"
            outputLine12 += "|"
            outputLine18 += "|"
            outputPMT    += "|"
            outputWedge  += "|"

        print outputLine0
        print outputLine6
        print outputLine12
        print outputLine18
        print outputPMT
        print outputWedge
        print


def printUHTRMap_FE(crate, table=True):
    
    values = cursor.execute('select distinct ngRBX, QIE10, crate, uHTR, uHTR_FI, nCable, MTP from ngHF_Mapping where ngRBX="{0}" and (uHTR_FI%6=0)'.format(crate)).fetchall()
    if table:
        print        "{0}  | 1 | 2 |   3   |   4   |   5   |   6   | 7 | 8 | 9 |   10  |   11  |   12  |   13  |   14  |".format(crate)
        print        "-------|---|---|-------|-------|-------|-------|---|---|---|-------|-------|-------|-------|-------|"
        crateline  = "Crate  |   |   |"
        uHTRline   = "uHTR   |   |   |"
        linksline  = "Links  |   |   |"
        trunk1line = "nCable |   |   |"
        trunk2line = "Sector |   |   |"
        trunk3line = "MTP    |   |   |"
        yfiberline = "Y-fiber|   |   |"
        for i_slot in [3,4,5,6]:
            for val in values:
                if val[1]==i_slot:
                    crateline  += " {0} |".format(str(val[2]).center(5))
                    uHTRline   += " {0} |".format(str(val[3]).center(5))
                    linksline  += " {0} |".format(str("{0}-{1}".format(val[4],val[4]+5)).center(5))
                    trunk1line += " {0} |".format(str(val[5]).center(5))
                    trunk2line += " {0} |".format(str(trunkSector[val[5]]).center(5))
                    trunk3line += " {0} |".format(str(val[6]).center(5))
                    yfiberline += " {0} |".format(str(1+(val[4]/6)%2).center(5))
        crateline  += "   |   |   |"
        uHTRline   += "   |   |   |"
        linksline  += "   |   |   |"
        trunk1line += "   |   |   |"
        trunk2line += "   |   |   |"
        trunk3line += "   |   |   |"
        yfiberline += "   |   |   |"
        for i_slot in [10,11,12,13,14]:
            for val in values:
                if val[1]==i_slot:
                    crateline  += " {0} |".format(str(val[2]).center(5))
                    uHTRline   += " {0} |".format(str(val[3]).center(5))
                    linksline  += " {0} |".format(str("{0}-{1}".format(val[4],val[4]+5)).center(5))
                    trunk1line += " {0} |".format(str(val[5]).center(5))
                    trunk2line += " {0} |".format(str(trunkSector[val[5]]).center(5))
                    trunk3line += " {0} |".format(str(val[6]).center(5))
                    yfiberline += " {0} |".format(str(1+(val[4]/6)%2).center(5))
        print crateline  
        print uHTRline   
        print linksline  
        print trunk1line 
        print trunk2line 
        print trunk3line 
        print yfiberline
    else:
        for i_slot in [3,4,5,6,10,11,12,13,14]:
            for val in values:
                if val[1]==i_slot:
                    print "{0}-{1}".format(val[0],val[1])
                    print "uHTR    {0}:{1}".format(val[2],val[3])
                    print "links   {0}-{1}".format(val[4],val[4]+5)
                    print "nCable  {0}".format(val[5])
                    print "MTP     {0}".format(val[6])
                    print "Y-fiber {0}".format((val[4]/6)%2)
                    print

def printUHTRMap(table=True):
    crateList = {'HFP Near':['HFP01','HFP02','HFP07','HFP08'],
                 'HFP Far':['HFP03','HFP04','HFP05','HFP06'],
                 'HFM Near':['HFM01','HFM02','HFM07','HFM08'],
                 'HFM Far':['HFM03','HFM04','HFM05','HFM06'],
                 }

    for side in crateList:
        print side.center(100)
        for crate in crateList[side]:
            printUHTRMap_FE(crate,table)
            print
        print
        print




if __name__=="__main__":

    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("--UHTR","--UHTRtoFE", dest="UHTRtoFE",
                      default=False, action="store_true",
                      help="convert from uHTR coordinates to FE coordinates"
                      )
    parser.add_option("--FEtoDET",dest="FEtoDET",
                      default=False, action="store_true",
                      help="convert from FrontEnd coordinates to Detector coordinates"
                      )
    parser.add_option("--FEtoUHTR",dest="FEtoUHT",
                      default=False, action="store_true",
                      help="convert from FrontEnd coordinates to uHTR coordinates"
                      )
    parser.add_option("--DETtoFE",dest="DETtoFE",
                      default=False, action="store_true",
                      help="convert from Detector coordinates to FrontEnd coordinates"
                      )
    parser.add_option("--DETtoBE",dest="DETtoBE",
                      default=False, action="store_true",
                      help="convert from Detector coordinates to BackEnd coordinates"
                      )
    parser.add_option("--full",dest="full",
                      default=False, action="store_true",
                      help="print full detector information for selected option"
                      )
    parser.add_option("--reverse",dest="reverse",
                      default=False, action="store_true",
                      help="get the reverse mapping"
                      )                      
    parser.add_option("-c","--crate",dest="crate",
                      default=-1,
                      help="specify crate"
                      )
    parser.add_option("-s","--slot",dest="slot",
                      default=-1,
                      help="specify slot"
                      )
    parser.add_option("--channel",dest="channel",
                      default=-1,
                      help="specify channel"
                      )
    parser.add_option("-l","--link",dest="link",
                      default=-1,
                      help="specify link"
                      )
    parser.add_option("--eta",dest="eta",
                      default=0,
                      help="specify eta"
                      )
    parser.add_option("--phi",dest="phi",
                      default=0,
                      help="specify phi"
                      )
    parser.add_option("--depth",dest="depth",
                      default=0,
                      help="specify depth"
                      )
    parser.add_option("--side",dest="side",
                      default=0,
                      help="specify side"
                      )

    (options, args) = parser.parse_args()

    if options.UHTRtoFE:
        if not options.reverse:
            if options.full:
                printUHTRMap()
            else:
                if options.crate==-1:
                    print 'Need to specify a crate, or the --full option to print all crates'
                    sys.exit()
                printUHTRMap_FE(options.crate)
        else:
            printFEtoUHTRMap()


    if options.DETtoFE:
        DetectorToFE(eta=options.eta,
                     phi=options.phi,
                     depth=options.depth,
                     side=options.side,
                     verbose=True)

    if options.DETtoBE:
        DetectorToBE(eta=options.eta,
                     phi=options.phi,
                     depth=options.depth,
                     side=options.side,
                     verbose=True)

    if options.FEtoDET:
        FEToDetector(crate=options.crate, slot = options.slot, channel=options.channel)


#     a = DetectorToFE(Eta=29, Phi=1, verbose=True)
#     print a
#    printFullMapInfo(Eta=29,Phi=1)


#     FEToBE("HFP01",3)

#    printWinchesterCablingMap_FE("HFP01")
#    printWinchesterCablingMap()

#    printUHTRMap_FE("HFP01")
#    printUHTRMap()
