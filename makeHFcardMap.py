from sendCommands import *

port = 63000
host = 'hcalngccm01'

import sqlite3
UIDtoSerialMap = sqlite3.connect("serialNumberToUIDmap.db")
cursor = UIDtoSerialMap.cursor()


print 'Crate,  Slot,   Unique ID,              S/N'
for side in ['HFM','HFP']:
    commands = []

    for crate in range(1,9):
        if crate%2==1:
            slotList = [1,3,4,5,6,10,11,12,13,14]
        else:
            slotList = [3,4,5,6,10,11,12,13,14]
        for slot in slotList:
            location = "{0}0{1}-{2}".format(side,crate,slot)
            commands.append('get {0}-UniqueID'.format(location))

    rawIDs = send_commands(commands,port=port,control_hub=host)

    i = 0
    for crate in range(1,9):
        if crate%2==1:
            slotList = [1,3,4,5,6,10,11,12,13,14]
        else:
            slotList = [3,4,5,6,10,11,12,13,14]
        for slot in slotList:
            rawID = rawIDs[i]['result']
            uID = "{0} {1}".format(rawID.split()[1],rawID.split()[2])

            serial = cursor.execute('select serial from UIDtoSerialNumber where uid="{0}"'.format(uID)).fetchone()

            print "{0}0{1},\t{2},\t{3},\t{4}".format(side,crate,slot,uID,serial[0]+500000)
            i += 1



