#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
""" vcf_egw_to_muttalias.py
    Converts egroupware exported vcards to mutt aliases"""
#
#    Copyright (C) 2011-2020 Georg Lutz <georg AT NOSPAM georglutz DOT de>
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

import argparse
import logging
import os
import quopri
import sys



def get_fields(list_, field):
    '''Returns a list of tupels (fieldname, content) of all found VCARD fields.
       Field can either be a complete field name or be followed by a specifier
       (seperated by ";").'''
    result = []
    for line in list_:
        if line.find(field + ":") == 0 or \
        (line.find(field + ";") == 0 and line.find(":") > line.find(field + ";")):
            entry = line.split(":", 1) # split only at the first occurence of ":"
            # Make sure that tuple is returned in case of emtpy field
            if len(entry) == 1:
                entry.append("")
            result.append(entry)
    return result


def parse_and_split_field(field):
    '''Parses a VCARD field. field is a tuple consisting of the field name and the field content.
       The content is decoded (if quoted printable) and de-splited by ";". The return value is a
       list consisting of the splitted values.'''
    result = []
    if len(field) != 2:
        return result
    if field[0].find("ENCODING=QUOTED-PRINTABLE") > 0:
        result = quopri.decodestring(field[1]).split(";")
    else:
        result = field[1].split(";")
    return result


def convert_to_mutt_aliases(entry):
    '''Searches for email addresses in a VCARD entry and converts it to mutt aliases.
       Returns a list of mutt aliases'''
    result = []

    addresses = get_fields(entry, "EMAIL")
    if not addresses:
        return result

    # The name of the entry. Will be used as base for alias name
    entry_name = ""
    full_name = ""

    # First try: name (N) field
    name = get_fields(entry, "N")
    if name:
        parsed_name = parse_and_split_field(name[0])
        # First entry is the family name, second the given name
        if len(parsed_name) >= 1:
            entry_name += parsed_name[0].lower().replace(" ", "")
            if len(parsed_name) > 1:
                entry_name += parsed_name[1].lower().replace(" ", "")
                full_name = parsed_name[1] + " " + parsed_name[0]

    # We haven't found a valid name, try company (ORG) field:
    if not entry_name:
        org = get_fields(entry, "ORG")
        if org:
            parsed_name = parse_and_split_field(org[0])
            if parsed_name:
                entry_name = parsed_name[0].lower().replace(" ", "")
                full_name = parsed_name[0]
    if not entry_name:
        logging.error("Cannot determine alias name. Ignore entry.")
        return []

    i = 1
    for address in addresses:
        if address[1]:
            alias_name = entry_name
            if i != 1:
                alias_name += str(i)
            result.append("alias %s %s <%s>" % (alias_name, full_name, address[1]))
            i += 1

    return result


def get_args():
    '''Configures command line parser and returns parsed parameters'''
    parser = argparse.ArgumentParser(
        description="Converts (not only egroupware exported) vcards to mutt aliases")
    parser.add_argument(
        "-d", "--debuglevel", dest="debuglevel", type=int, default=logging.WARNING,
        help="""Sets numerical debug level, see library logging module.
        Default is 30 (WARNING). Possible values are CRITICAL 50, ERROR 40
        WARNING 30, INFO 20, DEBUG 10, NOTSET 0. All log messages with debuglevel
        or above are printed. So to disable all output set debuglevel e.g. to 100.""")
    parser.add_argument(
        "-o", "--output_file", dest="output_file",
        help="The output file. Default output is sent to STDOUT")
    parser.add_argument(
        "vcard_file_name",
        help="The vcard file to convert")
    return parser.parse_args()


def main():
    '''main function, called when script file is executed directly'''

    args = get_args()

    logging.basicConfig(format="%(message)s", level=args.debuglevel)

    vcard_file_name = args.vcard_file_name
    if not os.path.isfile(vcard_file_name):
        logging.error("vcard_file not found")
        sys.exit(1)

    try:
        vcard_file = open(vcard_file_name, "r")
    except IOError:
        logging.error("Cannot open vcard file")
        sys.exit(2)

    if not args.output_file:
        output_file = sys.stdout
    else:
        try:
            output_file = open(args.output_file, "w")
        except IOError:
            logging.error("Cannot open output file for writing")
            sys.exit(2)

    # An entry is an array reflecting one vcard entry, without BEGIN and END tags
    # Usually on each line reflects another field (execpt for multiline field)
    entry = []
    in_entry = False # flag if we are inside one vcard
    line_nr = 1
    for line in vcard_file:
        line = line.replace("\n", "").replace("\r", "")

        if line.find("BEGIN:VCARD") == 0:
            in_entry = True
            entry = []
        else:
            if line.find("END:VCARD") == 0:
                in_entry = False
                mutt_aliases = convert_to_mutt_aliases(entry)
                for alias in mutt_aliases:
                    output_file.write(alias + "\n")
            else:
                if in_entry:
                    entry.append(line)
                    # inside a vcard entry

        line_nr = line_nr + 1

    vcard_file.close()
    output_file.close()


if __name__ == "__main__":
    main()
