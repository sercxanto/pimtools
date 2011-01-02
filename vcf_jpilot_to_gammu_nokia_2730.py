#!/usr/bin/python
#
#    vcf_jpilot_to_gammu_nokia_2730.py
#
#    Converts vcard file for import into Nokia 2730
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


import logging
import optparse
import os
import re
import shutil
import sys
import types

VERSIONSTRING = "0.1"


def processNote(note, birthdayfieldname):
    '''Processes JPilots vcard note. JPilot adds the user defined fields to the note field.
       Example:
       NOTE:Geburtstag:\n
        1972-08-11\n
    '''
    insideBirthday = False
    birthday = None
    realNote = []
    if len(birthdayfieldname) > 0:
	for line in note:
	    if insideBirthday:
		insideBirthday = False
		birthday = line.rstrip("\\n")
	    else:
		matchstr = "(?:^| )" + birthdayfieldname + ":\\\\n"
		result = re.match(matchstr, line)
		if type(result) != types.NoneType:
		    insideBirthday = True # Next line contains birthday
		else:
		    realNote.append(line)
    else:
	realNote = note
    return [realNote, birthday]


########### MAIN PROGRAM #############
def main():

    parser = optparse.OptionParser(
	    usage="%prog [options] jpilotfile",
	    version="%prog " + VERSIONSTRING + os.linesep +
	    "Copyright (C) 2010 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "directory: Where to store the single vcard files. vcardfile: The vcardfile to split")
    parser.add_option("-b", "--birthday", dest="birthday",
	    type="string", default = "",
	    help="The name of the birthday user defined field (if available)")
    parser.add_option("-n", "--note", dest="note",
	    type="string", default = "",
	    help="The name jpilot uses for the real note, usually language dependend")
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="Sets numerical debug level, see library logging module. Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are printed. So to disable all output set debuglevel e.g. to 100.")

    (options, args) = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=options.debuglevel)

    if len(args) < 1:
	parser.print_help()
	sys.exit(2)

    jpilotFileName = os.path.expanduser(args[0])
    if not os.path.isfile(jpilotFileName):
	logging.error("jpilotfile not found")
	sys.exit(1)

    try:
	jpilotFile = open(jpilotFileName, "r")
    except:
	logging.error("Cannot open jpilotfile")
	sys.exit(2)

    inLine = jpilotFile.readline()

    insideNote = True
    note = [] # usually note is multiline

    while inLine != "": # inLine contains at least \n
	inLine = inLine.rstrip("\n\r")
	# jpilot output is UTF-8, nokia / gammu expect latin1
	inLine = unicode(inLine, "utf-8").encode("iso-8859-1")

	complete = False
	outLine = []
	result = re.match("^VERSION:3.0", inLine)
	if type(result) != types.NoneType:
	    complete = True
	    outLine.append("VERSION:2.1")
	
	# Do not check for complete here
	if insideNote:
	    result = re.match("^ (.*)", inLine)
	    if type(result) != types.NoneType:
		if len(result.groups()) == 1:
		    note.append(result.groups()[0])
		    complete = True
	    else:
		# note ended, process note
		insideNote = False
		[realNote, birthday] = processNote(note, options.birthday)
		if type(birthday) != types.NoneType:
		    outLine.append("BDAY:" + birthday)
		if len(realNote) > 0:
		    outLine.append("NOTE:")
		for entry in realNote:
		    outLine.append(" " + entry)
		note = []

	if not complete:
	    result = re.match("^TEL;TYPE=email:(.*)", inLine)
	    if type(result) != types.NoneType:
	        complete = True
		outLine.append("EMAIL:")
		if len(result.groups()) == 1:
		    outLine[-1] += result.groups()[0]
	if not complete:
	    result = re.match("^TEL;TYPE=([a-zA-Z0-9]+)(?:,[a-zA-Z0-9]*)*:(.*)", inLine)
	    if type(result) != types.NoneType:
		complete = True
		outLine.append("TEL;")
		if len(result.groups()) == 2:
		    # nokia / gammu doesn't accept anything else - except "+" in phone number
		    number = ""
		    for char in result.groups()[1]:
			if ( char >= "0" and char <= "9" ) or char == "+":
			    number += char
		    outLine[-1] += result.groups()[0].upper() + ":" + number
	if not complete:
	    result = re.match("^NOTE(?:;[a-zA-Z0-9]*)*:(.*)", inLine)
	    if type(result) != types.NoneType:
		complete = True
		insideNote = True
		if len(result.groups()) == 1:
		    note.append(result.groups()[0])

	if not complete:
	    outLine.append(inLine)
	for line in outLine:
	    print line
	inLine = jpilotFile.readline()

    jpilotFile.close()




if __name__ == "__main__":
    main()

