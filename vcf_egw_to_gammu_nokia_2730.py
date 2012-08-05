#!/usr/bin/python
#
#    vcf_egw_to_gammu_nokia_2730.py
#
#    Tweaks egroupware exported vcards for import in gammu
#
#    Copyright (C) 2011 Georg Lutz <georg AT NOSPAM georglutz DOT de>
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
    '''Returns the contents of the first occurence of a given VCARD field.
       Returns None if field is not found''' 
    result = None
    for line in list:
        if line.find(field + ":") == 0:
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result


def getFields(list, field):
    '''Returns a list of tupels (fieldname, content) of all found VCARD fields.
       Field can either be a complete field name or be followed by a specifier
       (seperated by ";").'''
    result = []
    for line in list:
        if line.find(field + ":") == 0 or ( line.find(field + ";") == 0 and line.find(":") > line.find(field + ";")) :
            entry = line.split(":",1) # split only at the first occurence of ":"
            # Make sure that tuple is returned in case of emtpy field
            if len(entry) == 1:
                entry.append("")
            result.append(entry)
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


def appendField(entry, fieldName, fieldValue):
    '''Appends the field to the end of the entry'''
    entry.append(fieldName + ":" + fieldValue)


def deleteField(entry, fieldName):
    '''Completely removes the first occurence of the field from the entry'''
    for i in range(len(entry)):
	if entry[i].find(fieldName + ":") == 0:
	    del entry[i]
	    break


def deleteFields(entry, fieldName):
    '''Removes all occurences of the given field from the entry. Field can
       either be a complete field name or be followed by a specifier
       (seperated by ";").'''
    i = 0
    while i < len(entry):
        if entry[i].find(fieldName + ":") == 0 or entry[i].find(fieldName + ";") == 0:
            del entry[i]
        else:
            i += 1


def tweakEntry(entry, options):
    '''Actually does the vcard conversation of a single entry so that it can be
       imported into gammu / nokia phone'''
    result = entry

    telNrs = getFields(result, "TEL")
    for nr in telNrs:
        # nokia / gammu doesn't accept work cellphones, but multiple CELL entries are OK
        if nr[0] == "TEL;CELL;WORK":
            nr[0] = "TEL;CELL"
        # nokia / gammu doesn't accept anything else - except "+" in phone number
        newNr = ""
        for char in nr[1]:
            if ((char >= "0") and (char <= "9")) or (char == "+"):
                newNr += char
        nr[1] = newNr
    
    deleteFields(result, "TEL")
    for nr in telNrs:
        appendField(result, nr[0], nr[1])

    # nokia / gammu supports multiple email addresses but ignores email
    # addresses with specifiers like "EMAIL;WORK"
    emailAddrs = getFields(result, "EMAIL")
    deleteFields(result, "EMAIL")
    for addr in emailAddrs:
        appendField(result, "EMAIL", addr[1])

    # Same for "URL"
    urls = getFields(result, "URL")
    deleteFields(result, "URL")
    for url in urls:
        appendField(result, "URL", url[1])

    # Delete empty ORG field as nokia would display two semicolons
    if getField(result, "ORG") == ";;":
        deleteField(result, "ORG")
    
    return result


def writeEntryToFile(entry, file):
    '''Writes an vcard entry to an file handle. VCARD begin and end tags are appended'''
    file.write("BEGIN:VCARD\n")
    for line in entry:
        file.write(line + "\n")
    file.write("END:VCARD\n")
    file.write("\n")


########### MAIN PROGRAM #############
def main():

    parser = optparse.OptionParser(
	    usage="%prog [options] vcardFile",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2011 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "vcardFile: The vcard file to tweak.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="Sets numerical debug level, see library logging module. Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are printed. So to disable all output set debuglevel e.g. to 100.")

    parser.add_option("-o", "--outputfile", dest="outputfile",
	    type="string", default="", action="store",
	    help="The output file. Default output is sent to STDOUT")
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
        logging.error("Cannot open vcard file")
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

    # An entry is an array reflecting one vcard entry, without BEGIN and END tags
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []
    inEntry = False # flag if we are inside one vcard
    lineNr = 1
    while line != "":

        if line.find("BEGIN:VCARD") == 0:
            inEntry = True
        else:
            if line.find("END:VCARD") == 0:
                inEntry = False
                newEntry = tweakEntry(entry, options)
                writeEntryToFile(newEntry, outputFile)
                entry = []
            else:
                if inEntry:
                    entry.append(line)
                    # inside a vcard entry

        line = vcardFile.readline().replace("\n","").replace("\r","")
        lineNr = lineNr + 1


    vcardFile.close()
    outputFile.close()


if __name__ == "__main__":
    main()

