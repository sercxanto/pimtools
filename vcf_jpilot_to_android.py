#!/usr/bin/python
#
#    vcf_jpilot_to_android.py
#
#    Tweaks jpilot exported VCF for import in android contact
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
    '''Returns the contents of VCARD field. Returns None if field is not found''' 
    result = None
    for line in list:
        if line.find(field + ":") == 0:
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result


def setField(entry, fieldName, fieldValue):
    '''Sets a VCARD field. An already existing field is overwritten.'''
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


def tweakEntry(entry, options):
    '''Actually does the vcf conversation of a single entry so that it can be imported into android contact app'''
    result = entry

    if len(options.category) > 0:
	setField(result, "CATEGORIES", options.category)

    # android cannot handle email as telephone number
    email = getField(result, "TEL;TYPE=email")
    if email != None:
	setField(result, "EMAIL", email)
	deleteField(result, "TEL;TYPE=email")

    # If the birthdayfield is a user specific field it is stored in something like "X-"
    if len(options.birthdayfieldname) > 0:
	bday = getField(result, options.birthdayfieldname)
	if bday != None:
	    setField(result, "BDAY", bday)
	    deleteField(result, options.birthdayfieldname)
    return result


def writeEntryToFile(entry, file):
    '''Writes an vcf entry to an file handle. VCARD begin and end tags are appended'''
    file.write("BEGIN:VCARD\n")
    for line in entry:
        file.write(line + "\n")
    file.write("END:VCARD\n")
    file.write("\n")


########### MAIN PROGRAM #############
def main():

    parser = optparse.OptionParser(
	    usage="%prog [options] icalFile",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2010 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "vcardfile: The vcf file to tweak.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="Sets numerical debug level, see library logging module. Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are printed. So to disable all output set debuglevel e.g. to 100.")

    parser.add_option("-b", "--birthdayfieldname", dest="birthdayfieldname",
	    type="string", default="", action="store",
	    help="The name of the birthday field. Will be moved to standard field \"BDAY\"")

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

    vcardFileName = os.path.expanduser(args[0])
    if not os.path.isfile(vcardFileName):
        logging.error("vcardFile not found")
        sys.exit(1)

    try:
        vcardFile = open(vcardFileName, "r")
    except:
        logging.error("Cannot open vcf file")
        sys.exit(2)

    if len(options.outputfile) == 0:
        outputFile = sys.stdout
    else:
        try:
            outputFile = open(options.outputfile, "w")
        except:
            logging.error("Cannot open output file for writing")
            sys.exit(2)

    line = vcardFile.readline().replace("\n","").replace("\r","")

    # An entry is an array reflecting one vcf entry, without BEGIN and END tags
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []
    inEntry = False # flag if we are inside one entry
    lineNr = 1
    while line != "":

        if line.find("BEGIN:VCARD") == 0:
            inEntry = True
        else:
            if line.find("END:VCARD") == 0:
                # @todo process last entry and write into file
                inEntry = False
                newEntry = tweakEntry(entry, options)
                writeEntryToFile(newEntry, outputFile)
                entry = []
            else:
                if inEntry:
                    entry.append(line)
                    # inside a vcalendar entry

        line = vcardFile.readline().replace("\n","").replace("\r","")
        lineNr = lineNr + 1


    vcardFile.close()
    outputFile.close()


if __name__ == "__main__":
    main()

