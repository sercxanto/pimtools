#!/usr/bin/python
""" vcf_egw_to_owncloud.py

    Tweaks egroupware exported vcards for import in owncloud"""
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



def main():
    '''main programm'''
    parser = optparse.OptionParser(
	    usage="%prog [options] vcard_file",
	    version="%prog " + os.linesep +
	    "Copyright (C) 2014 Georg Lutz <georg AT NOSPAM georglutz DOT de>",
	    epilog = "vcard_file: The vcard file to tweak.")
    
    parser.add_option("-d", "--debuglevel", dest="debuglevel",
	    type="int", default=logging.WARNING,
	    help="""Sets numerical debug level, see library logging module.
Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40, WARNING 30,
INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel or above are
printed. So to disable all output set debuglevel e.g. to 100.""")

    parser.add_option("-o", "--outputfile", dest="outputfile",
	    type="string", default="", action="store",
	    help="The output file. Default output is sent to STDOUT")
    (options, args) = parser.parse_args()

    logging.basicConfig(format="%(message)s", level=options.debuglevel)

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    vcard_file_name = os.path.expanduser(args[0])
    if not os.path.isfile(vcard_file_name):
        logging.error("vcard_file not found")
        sys.exit(1)

    try:
        vcard_file = open(vcard_file_name, "r")
    except:
        logging.error("Cannot open vcard_file")
        sys.exit(2)

    if len(options.outputfile) == 0:
        outputfile = sys.stdout
    else:
        try:
            outputfile = open(options.outputfile, "w")
        except:
            logging.error("Cannot open output file for writing")
            sys.exit(2)

    # Deals mainly with the situation that imported egroupware contacts have
    # the line contination / folding wrong (e.g. only the first line of a
    # multiline note is shown).
    # Egroupware encodes multiline fields with a "=0D=0A=" at the end of
    # the to-be-continued line and the next line starts immedeately with
    # the next byte:
    #
    # NOTE:;ENCODING=QUOTED-PRINTABLE:First line=0D=0A=
    # Second line
    #
    # In contrast owncloud parses the last character of the line "=" as
    # regular equal sign and expect the first character of the continued line
    # to be a space:
    #
    # NOTE:;ENCODING=QUOTED-PRINTABLE:First line=0D=0A
    #  Second line
 
    line_in = vcard_file.readline().replace("\n","").replace("\r","")
    is_cont = False

    while line_in != "":
        if is_cont:
            line_out = " " + line_in
        else:
            line_out = line_in

        if line_out.endswith("="):
            line_out = line_out[:-1]
            is_cont = True
        else:
            is_cont = False

        outputfile.write(line_out + "\r\n")
        line_in = vcard_file.readline().replace("\n","").replace("\r","")


    vcard_file.close()
    outputfile.close()


if __name__ == "__main__":
    main()

