#!/usr/bin/python
#
#    ical_jpilot_to_egw.py
#
#    Tweaks jpilot exported ical for import in egroupware
#
#    Copyright (C) 2010 Georg Lutz <georg AT NOSPAM georglutz DOT de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import optparse
import os
import re
import sys


def getField(list, field):
    '''Returns the contents of VEVENT field. Returns None if field is not found''' 
    result = None
    for line in list:
        if line.find(field + ":") == 0:
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result


def setField(entry, fieldName, fieldValue):
    '''Sets a VEVENT field. An already existing field is overwritten.'''
    found = False
    for i in range(len(entry)):
        if entry[i].find(fieldName + ":" ) == 0:
            found = True
            break
    
    line = fieldName + ":" + fieldValue
    if found:
        entry[i] = line
    else:
        entry.append(line)


def deleteField(entry, fieldName):
    '''Completely removes the first occurence of the field from the entry'''
    for i in range(len(entry)):
	if entry[i].find(fieldName + ":") == 0:
	    del entry[i]
	    break

def addOneDay(date):
    '''Adds one day from a given date. date is expected to be in the form
    "YYYYmmdd" like 20101221. In case of an error the given date is returned.'''
    result = date
    try:
        timestamp = datetime.datetime.strptime(date,"%Y%m%d")
        newTimeStamp = timestamp + datetime.timedelta(days=1)
        result = newTimeStamp.strftime("%Y%m%d")
    except:
	logging.error("addOneDay(): Cannot parse date %s" % (date))
    return result


def subtractOneDay(date):
    '''Substracts one day from a given date. date is expected to be in the form
    "YYYYmmdd" like 20101221. In case of an error the given date is returned.'''
    result = date
    try:
        timestamp = datetime.datetime.strptime(date,"%Y%m%d")
        newTimeStamp = timestamp - datetime.timedelta(days=1)
        result = newTimeStamp.strftime("%Y%m%d")
    except:
	logging.error("subtractOneDay(): Cannot parse date %s" % (date))
    return result


def parseUntilDate(rrule):
    '''Parses the UNTIL date out of an rrule. Returns empty string on parse error'''
    result = ""
    m = re.match("FREQ=[A-Z]+;UNTIL=(?P<until>[a-zA-Z0-9]+)", rrule)
    if m != None and m.groupdict().has_key("until"):
	result = m.groupdict()["until"]
    return result
   

def correctRrule(rrule):
    '''Expects a date value in the UNTIL section of an recurrence event and
    returns the corrected value. For some unknown reason jpilot exports these
    dates with an additional day at the end, at least in version 1.6.2.9. In case
    that it cannot be corrected this function returns the given rrule.'''
    result = rrule
    oldDate = parseUntilDate(rrule)
    if len(oldDate) > 0:
        newDate = subtractOneDay(oldDate)
	result = rrule.replace("UNTIL=" + oldDate, "UNTIL=" + newDate)
    return result


def tweakEntry(entry, options):
    '''Actually does the ical conversation of a single entry so that it can be imported into EGW'''
    result = entry
    if len(options.category) > 0:
        setField(result, "CATEGORIES", options.category)

    # Usually jpilot doubles the information in the summary field. The description
    # field should contain more detailed information. So we just delete it if the
    # information is the same
    if getField(entry, "SUMMARY") != None and getField(entry, "SUMMARY") == getField(entry, "DESCRIPTION"):
	deleteField(entry, "DESCRIPTION")

    # jpilot has a day to much, at least in version 1.6.2.9
    rrule = getField(result, "RRULE")
    if rrule != None:
        setField(result, "RRULE", correctRrule(rrule))

    # EGW cannot handle non existing DTEND fields, even is a recurrence rule is given
    # jpilot does not seem to set and end date in case that the event is the whole day
    dateEnd = getField(result, "DTEND")
    if dateEnd == None:
	dateStart = getField(result, "DTSTART")
	# Sometimes jpilot uses this format
	dateStart = getField(result, "DTSTART;VALUE=DATE")
	if dateStart == None:
	    logging.error("Cannot distill end date")
	else:
	    newDate = addOneDay(dateStart)
	    setField(result, "DTEND", newDate)

    return result


def writeEntryToFile(entry, file):
    '''Writes an ical entry to an file handle. VEVENT begin and end tags are appended'''
    file.write("BEGIN:VEVENT\n")
    for line in entry:
        file.write(line + "\n")
    file.write("END:VEVENT\n")
    file.write("\n")


########### MAIN PROGRAM #############
def main():

    parser = optparse.OptionParser(
	    usage="%prog [options] icalFile",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2010 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "icalfile: The ical file to tweak.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="Sets numerical debug level, see library logging module. Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are printed. So to disable all output set debuglevel e.g. to 100.")

    parser.add_option("-o", "--outputfile", dest="outputfile",
	    type="string", default="", action="store",
	    help="The output file. Default output is sent to STDOUT")

    parser.add_option("-c", "--category", dest="category",
            type="string", default="", action="store",
            help="All entries will have this category assigned. Existing categories are overwritten. Usefull for testing.")

    (options, args) = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=options.debuglevel)

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    icalFileName = os.path.expanduser(args[0])
    if not os.path.isfile(icalFileName):
        logging.error("icalFile not found")
        sys.exit(1)

    try:
        icalFile = open(icalFileName, "r")
    except:
        logging.error("Cannot open ical file")
        sys.exit(2)

    if len(options.outputfile) == 0:
        outputFile = sys.stdout
    else:
        try:
            outputFile = open(options.outputfile, "w")
        except:
            logging.error("Cannot open output file for writing")
            sys.exit(2)

    line = icalFile.readline().replace("\n","").replace("\r","")

    # An entry is an array reflecting one ical entry, without BEGIN and END tags
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []
    inEntry = False # flag if we are inside one ventry
    inPreamble = True # Before first VEVENT entry
    preamble = []
    lineNr = 1
    while line != "":

        if line.find("BEGIN:VEVENT") == 0:
            inEntry = True
            if inPreamble:
                for newLine in preamble:
                    outputFile.write(newLine + "\n")
                outputFile.write("\n")
                inPreamble = False

        else:
            if inPreamble:
                preamble.append(line)

            if line.find("END:VEVENT") == 0:
                inEntry = False
                newEntry = tweakEntry(entry, options)
                writeEntryToFile(newEntry, outputFile)
                entry = []
            else:
                if inEntry:
                    entry.append(line)
                    # inside a vcalendar entry

        line = icalFile.readline().replace("\n","").replace("\r","")
        lineNr = lineNr + 1


    outputFile.write("END:VCALENDAR\n")
    icalFile.close()
    outputFile.close()


if __name__ == "__main__":
    main()

