#!/usr/bin/python
#
#    vcf_egw_to_muttalias.py
#
#    Converts egroupware exported vcards to mutt aliases
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
import quopri
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


def parseAndSplitField(field):
    '''Parses a VCARD field. field is a tuple consisting of the field name and the field content.
       The content is decoded (if quoted printable) and de-splited by ";". The return value is a list
       consisting of the splitted values.'''
    result = []
    if len(field) != 2:
        return
    if field[0].find("ENCODING=QUOTED-PRINTABLE") > 0:
        result = quopri.decodestring(field[1]).split(";")
    else:
        result = field[1].split(";")
    return result


def convertToMuttAliases(entry, logging):
    '''Searches for email addresses in a VCARD entry and converts it to mutt aliases.
       Returns a list of mutt aliases'''
    result = []

    addresses = getFields(entry, "EMAIL")
    if len(addresses) == 0:
        return result

    # The name of the entry. Will be used as base for alias name
    entryName = ""
    fullName = ""

    # First try: name (N) field
    name = getFields(entry, "N")
    if len(name) > 0:
        parsedName = parseAndSplitField(name[0])
        # First entry is the family name, second the given name
        if len(parsedName) >= 1:
            entryName += parsedName[0].lower().replace(" ", "")
            if len(parsedName) > 1:
                entryName += parsedName[1].lower().replace(" ", "")
                fullName = parsedName[1] + " " + parsedName[0]
   
    # We haven't found a valid name, try company (ORG) field:
    if len(entryName) == 0:
        org = getFields("ORG")
        if len(org) > 0:
            parsedName = parseAndSplitField(org[0])
            if len(parsedName) > 0:
                entryName = parsedName[0].lower().replace(" ","")
                fullName = parsedName[0]
    if len(entryName) == 0:
        logging.error("Cannot determine alias name. Ignore entry.")
        return

    i = 1
    for address in addresses:
        if len(address[1]) > 0:
            aliasName = entryName
            if i != 1:
                aliasName += str(i)
            result.append("alias %s %s <%s>" % (aliasName, fullName, address[1]))
            i += 1

    return result


########### MAIN PROGRAM #############
def main():

    parser = optparse.OptionParser(
	    usage="%prog [options] vcardFile",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2011 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "vcardFile: The vcard file to convert.")
    
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
            entry = []
        else:
            if line.find("END:VCARD") == 0:
                inEntry = False
                muttAliases = convertToMuttAliases(entry, logging)
                for alias in muttAliases:
                    outputFile.write(alias + "\n")
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

