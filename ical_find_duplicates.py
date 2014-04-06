#!/usr/bin/python
""" ical_find_duplicates.py

    Find duplicate VEVENT entries by looking at SUMMARY and DTSTART"""
#
#    Copyright (C) 2014 Georg Lutz <georg AT NOSPAM georglutz DOT de>
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
import sys


def get_field(list_, field):
    '''Returns the contents of the first occurence of a given ICAL field.
       Returns None if field is not found''' 
    result = None
    for line in list_:
        if line.find(field + ":") == 0 or line.find(field + ";") == 0 :
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result



def main():
    '''main programm'''

    parser = optparse.OptionParser(
	    usage="%prog [options] ical_file",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2014 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "ical_file: The ical file to analyze.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="""Sets numerical debug level, see library logging module.
Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30,
INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are
printed. So to disable all output set debuglevel e.g. to 100.""")

    (options, args) = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=options.debuglevel)

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    ical_file_name = os.path.expanduser(args[0])
    if not os.path.isfile(ical_file_name):
        logging.error("ical_file not found")
        sys.exit(1)

    try:
        ical_file = open(ical_file_name, "r")
    except:
        logging.error("Cannot open ical file")
        sys.exit(2)

    # An entry is an array reflecting one VEVENT entry, without BEGIN and
    # END tags.
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []

    in_entry = False # flag if we are inside one VEVENT

    # Data to match duplicates
    # Array of dictionaries consisting of "SUMMARY" and "DTSTART")
    duplicate_match = []
    for line in ical_file:
        line = line.replace("\n","").replace("\r","")

        if line.find("BEGIN:VEVENT") == 0:
            in_entry = True
        else:
            if line.find("END:VEVENT") == 0:
                in_entry = False
                duplicate_entry = { "SUMMARY": get_field(entry, "SUMMARY") ,
                                    "DTSTART": get_field(entry, "DTSTART") }
                if duplicate_entry in duplicate_match:
                    print "Found a duplicate for the following entry:"
                    print str(duplicate_entry)
                    print ""
                else:
                    duplicate_match.append(duplicate_entry)
                entry = []
            else:
                if in_entry:
                    entry.append(line)
                    # inside a VEVENT entry


    ical_file.close()


if __name__ == "__main__":
    main()

