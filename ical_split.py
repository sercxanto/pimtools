#!/usr/bin/python
""" ical_split.py

    Splits a single ical file in multiple ones for each entry"""
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


def get_lineending(line):
    '''Detects line ending of the given line and returns it.
       Can be either \\n, \\r or \\r\\n.

       Returns empty string if none of these is detected.
    '''
    # Take care to match the longest ones first:
    possible_endings = [ "\r\n", "\r", "\n" ]
    for ending in possible_endings:
        if line.endswith(ending):
            return ending
    return ""


def get_field(list_, field):
    '''Returns the contents of the first occurence of a given ICAL field.
       Returns None if field is not found''' 
    result = None
    for line in list_:
        if line.find(field + ":") == 0:
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result


def write_entry_to_file(entry, component, file_name, lineending):
    '''Writes an vcard entry to an file name.
       VCARD begin and end tags are appended

       entry: The whole entry as array without the BEGIN/END marker
       component: RFC5545 component name like VEVENT, VTODO, VJOURNAL
       lineending: Appended to all lines, e.g. "\\n" '''
    file_ = open(file_name, "w")
    file_.write("BEGIN:" + component + lineending)
    for line in entry:
        file_.write(line + lineending)
    file_.write("END:" + component + lineending)
    file_.close()


def get_component_match(line):
    """Get ical component name and limiter ("LIMITER:component",
    e.g. "BEGIN:VEVENT")

    line: The line to match

    Returns dictionary e.g. {"limiter": "BEGIN", "component":"VEVENT"}
    Returns None if no match

    Example:
         get_component_limiter("END:VTODO")

    returns:
        {"limiter": "END", "component": "VTODO"}"""
    possible_components = [
            "VEVENT", "VTODO", "VJOURNAL", "VFREEBUSY", "VTIMEZONE"]

    for component in possible_components:
        if line.startswith("BEGIN:" + component):
            return {"limiter": "BEGIN", "component" : component}
        if line.startswith("END:" + component):
            return {"limiter": "END", "component" : component}
    return None


def main():
    '''main programm'''

    parser = optparse.OptionParser(
	    usage="%prog [options] ical_file outdir",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2014 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "ical_file: The ical file to split." + os.linesep +
                      "outdir: The directory, where to write files to.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="""Sets numerical debug level, see library logging module.
Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30,
INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are
printed. So to disable all output set debuglevel e.g. to 100.""")

    (options, args) = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=options.debuglevel)

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    ical_file_name = os.path.expanduser(args[0])
    if not os.path.isfile(ical_file_name):
        logging.error("ical_file not found")
        sys.exit(1)

    outdir = os.path.expanduser(args[1])
    if not os.path.isdir(outdir):
        logging.error("outdir not found")
        sys.exit(1)

    try:
        ical_file = open(ical_file_name, "r")
    except:
        logging.error("Cannot open ical file")
        sys.exit(2)

    # An entry is an array reflecting one vcard entry, without BEGIN and
    # END tags.
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []

    current_component = ""
    in_entry = False # flag if we are inside one vcard
    no_uid_counter = 0 # vcard entries with no UID field
    lineending = ""
    line_number = 0
    process_entry = False
    for line in ical_file:
        line_number = line_number + 1
        if len(lineending) == 0:
            lineending = get_lineending(line) # keep same line endings
        line = line.replace("\n","").replace("\r","")

        component_match = get_component_match(line)

        if component_match is None:
            if in_entry:
                entry.append(line)
        else:
            if component_match["limiter"] == "BEGIN":
                if len(current_component) > 0:
                    msg = "Parse error at line %d" % (line_number)
                    logging.error(msg)
                    sys.exit(1)
                current_component = component_match["component"]
                in_entry = True
            else:
                if component_match["limiter"] == "END":
                    if component_match["component"] != current_component:
                        msg = "Parse error at line %d" % (line_number)
                        logging.error(msg)
                        sys.exit(1)
                    in_entry = False
                    process_entry = True


        if process_entry:
            outfile_name = get_field(entry, "UID")
            if outfile_name is None:
                no_uid_counter = no_uid_counter + 1
                outfile_name = "nouid_%03d" % (no_uid_counter)
            outfile_name = current_component + "_" + outfile_name + ".ics"
            outfile_path = os.path.join(outdir, outfile_name)
            if os.path.exists(outfile_path):
                msg = "UID collision, file %s already exists." % (
                        outfile_path)
                msg += " Exit."
                logging.error(msg)
                sys.exit(1)
            write_entry_to_file(
                    entry, current_component, outfile_path, lineending)
            entry = []
            current_component = ""
            process_entry = False

    ical_file.close()


if __name__ == "__main__":
    main()

