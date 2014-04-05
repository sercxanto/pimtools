#!/usr/bin/python
""" vcf_split.py

    Splits multiple VCARD entries in vcf file to multiple files"""
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
    '''Returns the contents of the first occurence of a given VCARD field.
       Returns None if field is not found''' 
    result = None
    for line in list_:
        if line.find(field + ":") == 0:
            # split returns an empty string if nothing comes after
            # so its safe to access [1]
            result = line.split(":")[1]
            break
    return result


def write_entry_to_file(entry, file_name, lineending):
    '''Writes an vcard entry to an file name.
       VCARD begin and end tags are appended

       The provided line ending e.g. "\\n" is used.
       '''
    file_ = open(file_name, "w")
    file_.write("BEGIN:VCARD" + lineending)
    for line in entry:
        file_.write(line + lineending)
    file_.write("END:VCARD" + lineending)
    file_.close()


def main():
    '''main programm'''

    parser = optparse.OptionParser(
	    usage="%prog [options] vcardFile outdir",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2014 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "vcardFile: The vcard file to split." + os.linesep +
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

    vcard_file_name = os.path.expanduser(args[0])
    if not os.path.isfile(vcard_file_name):
        logging.error("vcardFile not found")
        sys.exit(1)

    outdir = os.path.expanduser(args[1])
    if not os.path.isdir(outdir):
        logging.error("outdir not found")
        sys.exit(1)

    try:
        vcard_file = open(vcard_file_name, "r")
    except:
        logging.error("Cannot open vcard file")
        sys.exit(2)

    # An entry is an array reflecting one vcard entry, without BEGIN and
    # END tags.
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []
    in_entry = False # flag if we are inside one vcard
    no_uid_counter = 0 # vcard entries with no UID field
    lineending = ""
    for line in vcard_file:
        if len(lineending) == 0:
            lineending = get_lineending(line) # keep same line endings
        line = line.replace("\n","").replace("\r","")

        if line.find("BEGIN:VCARD") == 0:
            in_entry = True
        else:
            if line.find("END:VCARD") == 0:
                in_entry = False
                outfile_name = get_field(entry, "UID")
                if outfile_name is None:
                    no_uid_counter = no_uid_counter + 1
                    outfile_name = "nouid_%03d" % (no_uid_counter)
                outfile_name += ".vcf"
                outfile_path = os.path.join(outdir, outfile_name)
                if os.path.exists(outfile_path):
                    msg = "UID collision, file %s already exists." % (
                            outfile_path)
                    msg += " Exit."
                    logging.error(msg)
                    sys.exit(1)
                
                write_entry_to_file(entry, outfile_path, lineending)
                entry = []
            else:
                if in_entry:
                    entry.append(line)
                    # inside a vcard entry


    vcard_file.close()


if __name__ == "__main__":
    main()

