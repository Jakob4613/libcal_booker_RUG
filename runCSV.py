#!/usr/bin/python2.7

import csv
import os
import datetime
import json
import re
import requests as req

#Determine the EID/GID for each seatID
f = open('idFile.csv', 'wb')
IDwriter = csv.writer(f)

TimesURL = "https://libcal.rug.nl/r/new/availability?lid=1443&zone=0&gid=0&capacity=-1"
TimesResp = req.get(TimesURL)

firstIndex = TimesResp.text.find("resources.push({")
lastIndex = TimesResp.text.rfind("resources.push({")

allSeats = TimesResp.text[firstIndex:lastIndex+333]

for seat in re.finditer('seatId: ', allSeats):
    endOfSeatIdLine = seat.start() + allSeats[seat.start():].find('\n')
    stringSeatIdLine = allSeats[seat.start():endOfSeatIdLine]
    seatId = int(re.findall(r'\d+', stringSeatIdLine)[0])

    stringEidLine = allSeats[(allSeats[:seat.start()].rfind('\n')) - 11:allSeats[:seat.start()].rfind('\n')]
    eId = int(re.findall(r'\d+', stringEidLine)[0])
    
    GIDLine = allSeats[endOfSeatIdLine: (endOfSeatIdLine + allSeats[endOfSeatIdLine+1:].find('\n'))]
    gId = int(re.findall(r'\d+', GIDLine)[0])
    
    
    newRow = [seatId, eId, gId]
    IDwriter.writerow(newRow)

f.close()


#Make the individual reservations.
with open('/home/pi/RuGUB_Booker1/booker.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    count=0
    currentDay = datetime.datetime.today().weekday()
    columnIndex = ((currentDay + 4) % 7) + 5

    for row in csv_reader:
        if(count > 0):
            try:
                if(row[columnIndex] != "x" and row[columnIndex] != "X"):
                    startBlock = row[columnIndex].split('_')[0]
                    stopBlock = row[columnIndex].split('_')[1]
                    print("runCSV.py: Time= " + str(datetime.datetime.now().time()))
                    print("runCSV.py: Booking is being made for: " + str(row[0]))
                    output = os.system("python /home/pi/RuGUB_Booker1/UB_Booker_v2.py " + str(startBlock) + " " + str(stopBlock) + " " + str(row[0]) + " " + str(row[1]) + " " + str(row[2]) + " " + str(row[3]) + " " + str(row[4]))
                    print("runCSV.py: Status: " + str(output))
                else:
                    print("runCSV.py: " + str(row[0]) + " has no reservation planned for day: " + str(columnIndex - 5))
            except:
                print("runCSV.py: Reading and booking row " + str(count) + " has failed with an exception.")
        count = count + 1
        print("\n")