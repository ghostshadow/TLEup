#!/usr/bin/python3
##
# Copyright (c) 2018 Ghostshadow
# MIT License (see LICENSE file)
##
"""
Update Program for Two-Line-Element Lists.

Generate a filtered TLE list from current online TLE data (from celestrak.com) and
user provided manual TLE data.
"""

import sys
import urllib.request as rq
import re
from math import *
import copy

_verbose=False
_quiet=False

class tle:
    def __init__(self):
        self.line1valid=False
        self.line2valid=False
        self.name=""
        self.id=0
        self.desig={"year":0, "launch":0, "object":"A"}
        self.epoch={"year":0, "day":0.}
        self.fdmm=0.
        self.sdmm=0.
        self.bstar=0.
        self.nr=0 # tle nr (inc with new release)
        self.inc=0.
        self.raan=0.
        self.ecc=0.
        self.aop=0.
        self.ma=0.
        self.mm=0.
        self.revol=0

    def __bytes__(self):
        """Creates the propper TLE formating"""
        line1=self.name.encode("ascii").ljust(24,b" ")
        line2=b"1 %05dU %02d%03d%-3b %02d%012.8f %c.%08d %c%05d%+01d %c%05d%+01d 0 %04d" %\
                (self.id,self.desig["year"]%100,self.desig["launch"],\
                self.desig["object"].encode("ascii"),self.epoch["year"]%100,\
                self.epoch["day"],b"-" if self.fdmm<0 else b" ",abs(self.fdmm*1.e8),\
                b"-" if self.sdmm<0 else b" ",\
                abs(self.sdmm*pow(10,5-(ceil(log(abs(self.sdmm),10)) if \
                abs(self.sdmm)>0 else 0))),\
                (ceil(log(abs(self.sdmm),10)) if abs(self.sdmm)>0 else 0),\
                b"-" if self.bstar<0 else b" ",\
                abs(self.bstar*pow(10,5-(ceil(log(abs(self.bstar),10)) if \
                abs(self.bstar)>0 else 0))),\
                (ceil(log(abs(self.bstar),10)) if abs(self.bstar)>0 else 0),\
                self.nr,)
        line3=b"2 %05d %08.4f %08.4f %07d %08.4f %08.4f %011.8f%05d" %\
                (self.id,self.inc,self.raan,self.ecc*1.e7,self.aop,\
                self.ma,self.mm,self.revol,)
        l2cs=0
        for c in line2:
            bc=bytes([c])
            if bc.isdigit():
                l2cs+=int(bc.decode("ascii"))
            elif bc==b"-":
                l2cs+=1
        l2cs%=10

        l3cs=0
        for c in line3:
            bc=bytes([c])
            if bc.isdigit():
                l3cs+=int(bc.decode("ascii"))
            elif bc==b"-":
                l3cs+=1
        l3cs%=10
        return line1+b"\r\n"+line2+str(l2cs).encode("ascii")+b"\r\n"+line3+\
                str(l3cs).encode("ascii")+b"\r\n"
    
    def __str__(self):
        return bytes(self).decode("ascii")

def read_tles_from_bytes(f):
    """Read TLEs from multible byte lines"""
    lines=f.splitlines()

    tles=[]
    ctle=None
    state="none"
    for l in lines:
        if state=="line1":
            match=re.fullmatch("^\s*(2)\s+(\d{1,5})\s+"\
                "(\d{1,3}\.\d{4})\s+(\d{1,3}\.\d{4})\s+(\d{1,7})\s+"\
                "(\d{1,3}\.\d{4})\s+(\d{1,3}\.\d{4})\s+"\
                "(\d{1,2}\.\d{8})(\s*\d{1,5})(\d)\s*$",l.decode("ascii"))
            if match:
                cksum=int(match.group(10))
                nsum=0
                for c in l.strip(b" \r\n\t")[:-1].decode("ascii"):
                    if c.isdigit():
                        nsum+=int(c)
                    elif c=="-":
                        nsum+=1
                nsum%=10
                ctle.line2valid=cksum==nsum
                if ((not _quiet) and (cksum!=nsum)):
                    print("WARNING: checksum did not match [check(\""+\
                            l.strip(b" \r\n\t").decode("ascii")+"\")="+\
                            str(nsum)+"!="+str(cksum)+"]",file=sys.stderr)
                newid=int(match.group(2))
                if newid!=ctle.id:
                    if not _quiet:
                        print("ERROR: unexpeced id in second line, skipping!",
                                file=sys.stderr)
                    ctle=None
                    state="none"
                    continue
                ctle.inc=float(match.group(3))
                ctle.raan=float(match.group(4))
                ctle.ecc=float("0."+match.group(5))
                ctle.aop=float(match.group(6))
                ctle.ma=float(match.group(7))
                ctle.mm=float(match.group(8))
                ctle.revol=int(match.group(9))
                tles.append(copy.deepcopy(ctle))
                if _verbose:
                    print("Successfully read in TLE for \""+ctle.name+"\": "+str(ctle.id),
                        file=sys.stderr)
                ctle=None
                state="none"
                continue
        if state=="name":
            match=re.fullmatch("^\s*(1)\s+(\d{1,5})(\w)\s+"\
                "(\d{2})(\d{3})(\w{0,3})\s+(\d{2})(\s{0,2}\d{1,3}\.\d{8})\s+"\
                "([-+ 0]\.\d{8})\s+([-+ ]\d{5}[-+]\d)\s+([-+ ]\d{5}[-+]\d)\s+"\
                "(0)\s+(\d{1,4})(\d)\s*$",l.decode("ascii"))
            if match:
                cksum=int(match.group(14))
                nsum=0
                for c in l.strip(b" \r\n\t")[:-1].decode("ascii"):
                    if c.isdigit():
                        nsum+=int(c)
                    elif c=="-":
                        nsum+=1
                nsum%=10
                ctle.line1valid=cksum==nsum
                if ((not _quiet) and (cksum!=nsum)):
                    print("WARNING: checksum did not match [check(\""+\
                            l.strip(b" \r\n\t").decode("ascii")+"\")="+\
                            str(nsum)+"!="+str(cksum)+"]",file=sys.stderr)
                ctle.id=int(match.group(2))
                ctle.desig["year"]=int(match.group(4))
                ctle.desig["launch"]=int(match.group(5))
                ctle.desig["object"]=match.group(6)
                ctle.epoch["year"]=int(match.group(7))
                ctle.epoch["day"]=float(match.group(8))
                fdmm_str=match.group(9)
                ctle.fdmm=float(fdmm_str[0]+"0"+fdmm_str[1:])
                sdmm_str=match.group(10)
                ctle.sdmm=float(sdmm_str[0]+"0."+sdmm_str[1:6]+"e"+sdmm_str[6:])
                bstar_str=match.group(11)
                ctle.bstar=float(bstar_str[0]+"0."+bstar_str[1:6]+"e"+bstar_str[6:])
                ctle.nr=int(match.group(13))
                state="line1"
                continue
        if state=="none":
            match=re.fullmatch(b"^\s*((\S.*)?\S)\s*$",l)
            if match:
                ctle=tle()
                ctle.name=match.group(1).decode("ascii")
                state="name"
                continue
        if not _quiet:
            print("WARNING: Non-TLE line, might discard partial TLE ("+str(l)+")",
                    file=sys.stderr)
        ctle=None
        state="none"
    return tles


def get_celestrak_tle():
    """Search celestrak.com for tle files and parse all you find"""
    if _verbose:
        print("Gathering online TLE files ...",file=sys.stderr)
    with rq.urlopen("http://www.celestrak.com/NORAD/elements/") as resp:
        tles=[]
        for f in re.findall("\".*\.txt\"",resp.read().decode()):
            if _verbose:
                oc=len(tles)
                print("Reading "+f+" ...",file=sys.stderr)
            with rq.urlopen("http://www.celestrak.com/NORAD/elements/"+f.strip("\"")) as tf:
                tles.extend(read_tles_from_bytes(tf.read()))
            if _verbose:
                print("Found "+str(len(tles)-oc)+" tles in "+f,file=sys.stderr)
    return tles


        
if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(description=__doc__,add_help=False)
    ap.add_argument("--help",action="help",help="Print this help message")
    ap.add_argument("--list","-l",action="store_true",help="only list "\
            "names and id numbers of the objects, which are selected, "\
            "do not generate tle file. (in combination with \"-a\": "\
            "list all available objects)")
    ap.add_argument("--all-objects","-a",dest="allobjects",action="store_true",
            help="disable filtering, allways output all available objects")
    ap.add_argument("--filter","-f",action="store",type=str,default=None,
            help="specify a filter list (if a none exsistent file is specified, "\
                    "the file is created and filled with a template of the syntax)")
    ap.add_argument("--output","-o",action="store",default="tles.txt",
            help="specify the output file (default is \"tles.txt\")")
    ap.add_argument("--user-tles","-u",action="store",type=str,default=None,
            help="specify the list of manual tles")
    ap.add_argument("--no-online","-n",action="store_true",
            help="disable reading online tles, only use user defined tles")
    apvg=ap.add_mutually_exclusive_group()
    apvg.add_argument("--verbose","-v",action="store_true",
            help="print progess messages to stderr")
    apvg.add_argument("--quiet","-q",action="store_true",
            help="suppress even error and warning messages")
    ns=ap.parse_args()
    _verbose=ns.verbose
    _quiet=ns.quiet

# read filter
    filterlist={"name":[],"id":[],"launch":[],"field":[]}
    if ns.filter is None and not ns.allobjects:
        if not _quiet:
            print("ERROR: Not specifying a filter without requesting all TLEs "\
                    "is invalid!",file=sys.stderr)
        sys.exit(2)
    elif ns.filter is not None:
        if _verbose:
            print("Loading filter list from "+ns.filter+" ...",file=sys.stderr)
        try:
            with open(ns.filter,"rt") as ff:
                for l in ff:
                    l=l.rstrip("\r\n")
                    if len(l)<1 or l[0]=="#":
                        continue
                    elif l[0]=="?" or l[0]=="\\":
                        filterlist["name"].append(l[1:])
                    elif l[0]=="$":
                        filterlist["id"].append(l[1:])
                    elif l[0]=="~":
                        filterlist["launch"].append(l[1:])
                    elif l[0]=="&":
                        match=re.fullmatch("^&(\S+)\s+{\s*([\d.+-eE]+)\s*,"\
                                "\s*([\d.+-eE]+)\s*}\s*$",l)
                        if match:
                            filterlist["field"].append({"field":match.group(1),
                                "min":float(match.group(2)),"max":float(match.group(3))})
                        elif not _quiet:
                            print("ERROR: Invalid filter \""+l+"\"",file=sys.stderr)
                    else:
                        filterlist["name"].append(l)
            if not any(len(filterlist[k])>0 for k in filterlist.keys()):
                if not _quiet:
                    print("ERROR: Filter list contains no valid filters but "\
                            "to get an unfiltered list you have to use the "\
                            "\"-a\" paramter!",file=sys.stderr)
                sys.exit(1)
            if _verbose:
                print("Filter list successfull loaded. \n"+str(filterlist),
                        file=sys.stderr)
        except FileNotFoundError as fnf:
            if not _quiet:
                print("WARNING: Filter file does not exist, creating a template "\
                        "which contains an example!",file=sys.stderr)
# create filter template
            try:
                with open(ns.filter,"wt") as ff:
                    ff.write("# Filter file for the TLE update script\n"\
                            "# This is a template, adjust to your needs\n\n"\
                            "# Lines starting with \"#\" are comments and ignored\n\n"\
                            "# Filter for satellite name:\n"\
                            "# The filter compares the names converted to upper "\
                            "case and matches even if the name in the tle is longer\n"\
                            "# Names are prefixed with \"?\" or without a prefix\n"\
                            "#?NOAA\n"\
                            "# ^^Matches all satellites with a name starting with "\
                            "\"NOAA\"\n\n"\
                            "# Filter for satellite id:\n"\
                            "# Ids are prefixed with \"$\"\n"\
                            "#$40977\n"\
                            "# ^^Matches the satellite with the NORAD ID 40977\n\n"\
                            "# Filter for international (launch) designator:\n"\
                            "# Designators are prefixed with \"~\" and match even "\
                            "if only the beginning is specified\n"\
                            "#~17036N\n"\
                            "# ^^Matches the satellite launched on the 36th launch "\
                            "of 2017 which is designated object \"N\" of the launch\n"\
                            "#~18\n"\
                            "# ^^Matches all satellites launched in 2018\n\n"\
                            "# Advanced filter for TLE elements:\n"\
                            "# TLE element name prefixed with \"&\" followed by "\
                            "a space and a range (min and max) of values enclosed "\
                            "in curly braces, seperated by a comma\n"\
                            "# Available TLE elements are:\n"\
                            "# \"fdmm\"=First derivate of mean motion\n"\
                            "# \"sdmm\"=Second derivate of mean motion\n"\
                            "# \"bstar\"=B*-drag term\n"\
                            "# \"inc\"=Inclination\n"\
                            "# \"raan\"=Right ascention of ascending node\n"\
                            "# \"ecc\"=Eccentricity\n"\
                            "# \"aop\"=Argument of preigee\n"\
                            "# \"ma\"=Mean anomaly\n"\
                            "# \"mm\"=Mean motion\n"\
                            "#&inc {40,60}\n"\
                            "# ^^Matches all satellites with a inclination between "\
                            "40° and 60°\n\n\n")
                if _verbose:
                    print("Template filter successfully created",file=sys.stderr)
                sys.exit(0)
            except IOError as ioe:
                if not _quiet:
                    print("ERROR: Failed to read file "+ns.filter+"! ("+str(ioe)+")",
                            file=sys.stderr)
                sys.exit(1)
        except IOError as ioe:
            if not _quiet:
                print("ERROR: Failed to read file "+ns.filter+"! ("+str(ioe)+")",
                        file=sys.stderr)
            sys.exit(1)

    tles=[]
# load user tles
    try:
        if ns.user_tles is not None:
            with open(ns.user_tles,"rb") as uf:
                if _verbose:
                    print("Reading user defined TLEs ...",file=sys.stderr)
                    oc=len(tles)
                tles.extend(read_tles_from_bytes(uf.read()))
                if _verbose:
                    print("Done reading user TLEs ("+str(len(tles)-oc)+" tles found)",
                            file=sys.stderr)
        elif _verbose:
            print("No file given for user tles. Skipping",file=sys.stderr)
    except IOError as ioe:
        if not _quiet:
            print("ERROR: Failed to read file "+ns.user_tles+"! Skipping! ("+str(ioe)+")",
                    file=sys.stderr)

# load online tles
    if not ns.no_online:
        if _verbose:
            print("Fetching online TLEs ...",file=sys.stderr)
        tles.extend(get_celestrak_tle())
        if _verbose:
            print("Done fetching online TLEs ("+str(len(tles))+" tles found)",
                    file=sys.stderr)

# deduplicate tles
    if _verbose:
        print("Deduplicating TLEs (based on ID)...",file=sys.stderr)
    tles_old=tles
    tles=[]
    for tle in tles_old:
        if not any(t.id==tle.id for t in tles):
            tles.append(tle)
            continue
        if _verbose:
            print("Duplicate TLE, dropping ... ("+str(tle.name)+": "+str(tle.id)+")",
                    file=sys.stderr)
    del tles_old
    if _verbose:
        print("Deduplication done, "+str(len(tles))+" TLEs remaining",file=sys.stderr)

# filter tles
    if not ns.allobjects and any(len(filterlist[k])>0 for k in filterlist.keys()):
        if _verbose:
            print("Filtering "+str(len(tles))+" TLEs based on whitelist "+ns.filter+" ...",
                    file=sys.stderr)
        atles=tles
        tles=[]
        # TODO find more efficient way to do the filtering
        for tle in atles:
            for nfilt in filterlist["name"]:
                if tle.name.upper().startswith(nfilt.upper()):
                    tles.append(tle)
            for lfilt in filterlist["launch"]:
                if ("%(year)02d%(launch)03d%(object)-s" % tle.desig).upper()\
                        .startswith(lfilt.upper()):
                    tles.append(tle)
            for ifilt in filterlist["id"]:
                if all(c.isdigit() for c in ifilt) and tle.id==int(ifilt):
                    tles.append(tle)
            for ffilt in filterlist["field"]:
                if getattr(tle,ffilt["field"])>=ffilt["min"] and\
                        getattr(tle,ffilt["field"])<ffilt["max"]:
                    tles.append(tle)
        if _verbose:
            print("Filtering done, selected "+str(len(tles))+"/"+str(len(atles))+
                    " TLEs",file=sys.stderr)
    elif _verbose and ns.allobjects:
        print("Filtering disable by user request ...",file=sys.stderr)

# list tles
    if ns.list:
        if _verbose:
            print("Listing TLE objects ...",file=sys.stderr)
        for tle in tles:
            print("\""+tle.name+"\": "+str(tle.id))
        if _verbose:
            print("Done listing TLE objects ...",file=sys.stderr)
        sys.exit(0)

# save tles to file
    try:
        with open(ns.output,"wb") as of:
            if _verbose:
                print("Writing "+str(len(tles))+" TLEs to "+ns.output+" ...",
                        file=sys.stderr)
            for tle in tles:
                of.write(bytes(tle))
        if _verbose:
            print("Done writing!",file=sys.stderr)
    except IOError as ioe:
        if not _quiet:
            print("ERROR: Failed to write file "+ns.output+"! ("+str(ioe)+")",
                    file=sys.stderr)
        sys.exit(1)
