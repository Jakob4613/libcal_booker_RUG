#!/usr/bin/python2.7

import csv
import json
import re
import requests as req
from datetime import datetime, timedelta
import sys


def findGIDEID(seatID):
	with open('/home/pi/RuGUB_Booker1/idFile.csv') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		for row in csv_reader:
			if(int(row[0]) == int(seatID)):
				return int(row[1]), int(row[2])


debugMode = True

#Check of CLI commands are used.
if(len(sys.argv) == 8):
	StartBlock = int(sys.argv[1]) #beginning block of the reservation
	EndBlock = int(sys.argv[2]) #End of reservation
	Name = str(sys.argv[3])
	Surname = str(sys.argv[4])
	Email = str(sys.argv[5])
	StudentNumber = str(sys.argv[6])
	Phone = "0" + str(sys.argv[7])
	print("UB_Booker_v2.py: Is runned using: ", sys.argv)

else:
	if(debugMode):
		print("UB_Booker_v2.py: Something went wrong processing the CLI-input, reverting back to default parameters.")
		StartBlock = int(1) #beginning block of the reservation
		EndBlock = int(35) #End of reservation
		Name = str("John")
		Surname = str("Doe")
		Email = str("j.doe.5%40student.rug.nl")
		StudentNumber = str("s1234567")
		Phone = str("0612345678")	
	else:
		print("UB_Booker_v2.py: Something went wrong processing the CLI-input.")
		exit()

#Input validator
errorBoolean = False
	
#Checks could be implemented here
if(errorBoolean):
	print("UB_Booker_v2.py: The input was not valid.")

GID = "3634"
LibraryID = "1443" #Global constant that indicates the floor

#GridRequest-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
GridUrl = "https://libcal.rug.nl/spaces/availability/grid"
eid="-1"
seat="1"
seatId="0"
zone="1330"
accessible="0"
pageIndex="1"
pageSize="92"#"447"->full-capacity#000"#Amount of chairs that get fetched
planDaysAhead = 4#4
BookingDate = (datetime.now() + timedelta(days=(planDaysAhead))).strftime('%Y-%m-%d') #start parameter
BookingDateOne = (datetime.now() + timedelta(days=(planDaysAhead+1))).strftime('%Y-%m-%d') #end parameter
GridData = "lid=" + LibraryID + "&gid=" + GID + "&eid=" + eid + "&seat=" + seat + "&seatId=" + seatId + "&zone=" + zone + "&accessible=" + accessible + "&start=" + BookingDate + "&end=" + BookingDateOne + "&pageIndex=" + pageIndex + "&pageSize=" + pageSize
GridDataLength = len(GridData)
GridResp = req.post(GridUrl, GridData, headers={'referer': GridUrl, 'origin':"https://libcal.rug.nl",'Content-Type':"application/x-www-form-urlencoded; charset=UTF-8", 'Content-Length':str(GridDataLength)})
FinishPage = GridResp.text.encode('utf-8')
TheGrid = json.loads(FinishPage)

#Gather all of the individual seat ids.
possibleSeatIds = []
for slots in TheGrid['slots']:
	possibleSeatIds.append(slots['itemId'])
possibleSeatIds = list(set(possibleSeatIds))

if(debugMode):
	print("UB_Booker_v2.py: Succesfully fetched seats with ID's=" + str(possibleSeatIds[0]) + "-" + str(possibleSeatIds[len(possibleSeatIds)-1]) + ".")

#Determine which seatId we are going te book (bestId)
foundASeat = False
for possibleSeat in possibleSeatIds:
	blocksArray = []
	succesForSeat = True
	counterForSeat = 0
	for block in TheGrid['slots']:
		if(block['itemId'] == possibleSeat):
			if(counterForSeat >= StartBlock and counterForSeat <= EndBlock):
				blocksArray.append(block)
				if "className" in block:
					succesForSeat = False
			counterForSeat = counterForSeat + 1
	if succesForSeat == True and possibleSeat % 2 == 1:
		foundASeat = True
		seatId = possibleSeat
		#if one is found it will stop looking for a seat.
		break

if(not foundASeat):
	print("UB_Booker_v2.py: From the fetched seats, none was available in the requested time.")
	exit()

if(debugMode):
	print("UB_Booker_v2.py: Seat with ID=" + str(seatId) + " was chosen.")

#seatId = the seat that is going to be booked.
#firstAdd request------------------------------------------------------------------------------------------------------------------------------------------------------------------
TheReferer = "https://libcal.rug.nl/spaces?lid=1443&zone=1328&gid=0&capacity=-1"
EID, GID = findGIDEID(seatId)
EID = str(EID)
GID = str(GID)
addFirstStart = blocksArray[0]['start'][:-3].replace(" ", "+").replace(":", "%3A", 1)
checksumOfFirstBlock = blocksArray[0]['checksum']
addFirstUrl = "https://libcal.rug.nl/spaces/availability/booking/add"
addFirstData = "add%5Beid%5D=" + EID + "&add%5Bseat_id%5D=" + str(seatId) + "&add%5Bgid%5D=" + GID + "&add%5Blid%5D=" + LibraryID + "&add%5Bstart%5D=" + addFirstStart + "&add%5Bchecksum%5D=" + checksumOfFirstBlock + "&lid=" + LibraryID + "&gid=" + GID + "&start=" + BookingDate + "&end=" + BookingDateOne + "&session=0"
addFirstDataLength = len(addFirstData)
addFirstResp = req.post(addFirstUrl, addFirstData, headers={'referer': TheReferer, 'origin':"https://libcal.rug.nl",'Content-Type':"application/x-www-form-urlencoded; charset=UTF-8", 'Content-Length':str(addFirstDataLength)})
addFirstPage = addFirstResp.text.encode('utf-8')
addFirstJSON = json.loads(addFirstPage)
if ("isRefreshRequired" in addFirstJSON) and (addFirstJSON["isRefreshRequired"] == True):
	print("UB_Booker_v2.py: Chosen seat was already reserved in the meantime.")
	exit()

#----------------------------------------------------------prepare second add request
SessionId = addFirstJSON['session']
BookingId = addFirstJSON['bookings'][0]['id']
AmountOfBlocks =  EndBlock - StartBlock + 1

#If the UB closes earlier, make it maximum-lasting
if(AmountOfBlocks > len(addFirstJSON['bookings'][0]['optionChecksums'])):
	AmountOfBlocks = len(addFirstJSON['bookings'][0]['optionChecksums']) - 1

SecAddChecksum = addFirstJSON['bookings'][0]['optionChecksums'][AmountOfBlocks]
SecAddUpdEnd = ((addFirstJSON['bookings'][0]['options'][AmountOfBlocks]).replace(" ", "+")).replace(":", "%3A")
SecAddBookCheck = addFirstJSON['bookings'][0]['checksum']
SecAddBookSta = ((addFirstJSON['bookings'][0]['start'][:-3]).replace(" ", "+")).replace(":", "%3A", 1)
SecAddBookEnd = ((addFirstJSON['bookings'][0]['end'][:-3]).replace(" ", "+")).replace(":", "%3A", 1)
SecAddData = "update%5Bid%5D=" + str(BookingId) + "&update%5Bchecksum%5D=" + str(SecAddChecksum) + "&update%5Bend%5D=" + str(SecAddUpdEnd) + "&lid=" + str(LibraryID) + "&gid=" + str(GID) + "&start=" + str(BookingDate) + "&end=" + str(BookingDateOne) + "&session=" + str(SessionId) + "&bookings%5B0%5D%5Bid%5D=" + str(BookingId) + "&bookings%5B0%5D%5Beid%5D=" + str(EID) + "&bookings%5B0%5D%5Bseat_id%5D=" + str(seatId) + "&bookings%5B0%5D%5Bgid%5D=" + str(GID) + "&bookings%5B0%5D%5Blid%5D=" + str(LibraryID) + "&bookings%5B0%5D%5Bstart%5D=" + str(SecAddBookSta) + "&bookings%5B0%5D%5Bend%5D=" + str(SecAddBookEnd) + "&bookings%5B0%5D%5Bchecksum%5D=" + str(SecAddBookCheck)
SecAddUrl = addFirstUrl
SecAddDataLength = len(SecAddData)

#secondAdd request-------------------------------------------------------------------------------------------------------------------------------------------------------------------
SecAddResp = req.post(SecAddUrl, SecAddData, headers={'referer': TheReferer, 'origin':"https://libcal.rug.nl",'Content-Type':"application/x-www-form-urlencoded; charset=UTF-8", 'Content-Length':str(SecAddDataLength)})
SecAddPage = SecAddResp.text.encode('utf-8')
SecAddJSON = json.loads(SecAddPage)

print(SecAddJSON)

#prepare and execute times request
BookName = str(Name)
BookLname = str(Surname)
BookDMail = str(Email)
BookQ731 = str(Phone)
BookQ749 = str(StudentNumber)
BookSession = str(SessionId)
BookId = str(BookingId)
BookEid = str(EID)
BookSeatId = str(seatId)
BookGid = str(GID)
BookLid = str(LibraryID)
BookStart = ((SecAddJSON['bookings'][0]['start'][:-3]).replace(" ", "+")).replace(":", "%3A", 1) #Format = "2020-10-08 19:00"
BookEnd =  ((SecAddJSON['bookings'][0]['end'][:-3]).replace(" ", "+")).replace(":", "%3A", 1) #Format = "2020-10-08 20:30"
BookChecksum = str(SecAddJSON['bookings'][0]['checksum'])
BookRetUrl = str(TheReferer)
TimesData = "session=" + BookSession + "&patron=" + "" + "&patronHash=" + "" + "&bookings%5B0%5D%5Bid%5D=" + BookId + "&bookings%5B0%5D%5Beid%5D=" + BookEid + "&bookings%5B0%5D%5Bseat_id%5D=" + BookSeatId + "&bookings%5B0%5D%5Bgid%5D=" + BookGid + "&bookings%5B0%5D%5Blid%5D=" + BookLid + "&bookings%5B0%5D%5Bstart%5D=" + BookStart + "&bookings%5B0%5D%5Bend%5D=" + BookEnd + "&bookings%5B0%5D%5Bchecksum%5D=" + BookChecksum
TimesURL = "https://libcal.rug.nl/ajax/space/times"
TimesDataLength = len(TimesData)
TimesResp = req.post(TimesURL, TimesData, headers={'referer': TheReferer, 'origin':"https://libcal.rug.nl",'Content-Type':"application/x-www-form-urlencoded; charset=UTF-8", 'Content-Length':str(TimesDataLength)})

print(TimesResp)
#-------------------------------------------------------------prepare booking request!

#BookinREquest
BookData = "formData%5Bfname%5D=" + BookName + "&formData%5Blname%5D=" + BookLname + "&formData%5Bemail%5D=" + BookDMail + "&formData%5Bq731%5D=" + BookQ731 + "&formData%5Bq749%5D=" + BookQ749 + "&forcedEmail=&session=" + BookSession + "&bookings%5B0%5D%5Bid%5D=" + BookId + "&bookings%5B0%5D%5Beid%5D=" + BookEid + "&bookings%5B0%5D%5Bseat_id%5D=" + BookSeatId + "&bookings%5B0%5D%5Bgid%5D=" + BookGid + "&bookings%5B0%5D%5Blid%5D=" + BookLid + "&bookings%5B0%5D%5Bstart%5D=" + BookStart + "&bookings%5B0%5D%5Bend%5D=" + BookEnd + "&bookings%5B0%5D%5Bchecksum%5D=" + BookChecksum + "&/r/new?lid=1443&gid=0&zone=1328&capacity=-1&accessible=0&powered=0" + "&method=" + "13"
BookURL = "https://libcal.rug.nl/ajax/space/book"
BookDataLength = len(BookData)
BookResp = req.post(BookURL, BookData, headers={'referer': TheReferer, 'origin':"https://libcal.rug.nl",'Content-Type':"application/x-www-form-urlencoded; charset=UTF-8", 'Content-Length':str(BookDataLength)})
BookPage = BookResp.text.encode('utf-8')
print(BookURL)
BookJSON = json.loads(BookPage)

if "bookId" in BookJSON:
	print("UB_Booker_v2.py: Booking was succesfully made")
