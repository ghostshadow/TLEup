#!/usr/bin/python3
##
# Copyright (c) 2018 Ghostshadow
# MIT License (see LICENSE file)
##
"""
Update Program for Two-Line-Element Lists (Version 2).

Generate a TLE file from selected current online TLE data (from celestrak.com) and
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

def parse_tle_bytes(f):
    """Read TLEs from multible byte lines"""
    lines=f.splitlines()

    tles=[]
    ctle=None
    state="none"
    for l in lines:
        m_name=re.fullmatch(b"^\s*((\S.*)?\S)\s*$",l)
        m_line1=re.fullmatch("^\s*(1)\s+(\d{1,5})(\w)\s+"\
                "(\d{2})(\d{3})(\w{0,3})\s+(\d{2})(\s{0,2}\d{1,3}\.\d{8})\s+"\
                "([-+ 0]\.\d{8})\s+([-+ ]\d{5}[-+]\d)\s+([-+ ]\d{5}[-+]\d)\s+"\
                "(0)\s+(\d{1,4})(\d)\s*$",l.decode("ascii"))
        m_line2=re.fullmatch("^\s*(2)\s+(\d{1,5})\s+"\
                "(\d{1,3}\.\d{4})\s+(\d{1,3}\.\d{4})\s+(\d{1,7})\s+"\
                "(\d{1,3}\.\d{4})\s+(\d{1,3}\.\d{4})\s+"\
                "(\d{1,2}\.\d{8})(\s*\d{1,5})(\d)\s*$",l.decode("ascii"))
        if (state=="name" and m_line1 is None) or (state=="line1" and m_line2 is None):
            if not _quiet:
                print("WARNING: Non consecutive TLE line ("+str(l)+\
                        "), discards partial TLE (\""+str(ctle.name)+"\":"+\
                        str(ctle.id)+")",file=sys.stderr)
            ctle=None
            state="none"

        if state=="line1" and m_line2 is not None:
                cksum=int(m_line2.group(10))
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
                newid=int(m_line2.group(2))
                if newid!=ctle.id:
                    if not _quiet:
                        print("ERROR: unexpeced id in second line, skipping!",
                                file=sys.stderr)
                    ctle=None
                    state="none"
                    continue
                ctle.inc=float(m_line2.group(3))
                ctle.raan=float(m_line2.group(4))
                ctle.ecc=float("0."+m_line2.group(5))
                ctle.aop=float(m_line2.group(6))
                ctle.ma=float(m_line2.group(7))
                ctle.mm=float(m_line2.group(8))
                ctle.revol=int(m_line2.group(9))
                tles.append(copy.deepcopy(ctle))
                if _verbose:
                    print("Successfully read in TLE for \""+ctle.name+"\": "+str(ctle.id),
                        file=sys.stderr)
                ctle=None
                state="none"
        elif state=="name" and m_line1 is not None:
                cksum=int(m_line1.group(14))
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
                ctle.id=int(m_line1.group(2))
                ctle.desig["year"]=int(m_line1.group(4))
                ctle.desig["launch"]=int(m_line1.group(5))
                ctle.desig["object"]=m_line1.group(6)
                ctle.epoch["year"]=int(m_line1.group(7))
                ctle.epoch["day"]=float(m_line1.group(8))
                fdmm_str=m_line1.group(9)
                ctle.fdmm=float(fdmm_str[0]+"0"+fdmm_str[1:])
                sdmm_str=m_line1.group(10)
                ctle.sdmm=float(sdmm_str[0]+"0."+sdmm_str[1:6]+"e"+sdmm_str[6:])
                bstar_str=m_line1.group(11)
                ctle.bstar=float(bstar_str[0]+"0."+bstar_str[1:6]+"e"+bstar_str[6:])
                ctle.nr=int(m_line1.group(13))
                state="line1"
        elif state=="none" and m_name is not None:
                ctle=tle()
                ctle.name=m_name.group(1).decode("ascii")
                state="name"
    return tles

def peri_apo_from_mm_ecc(mm,ecc):
    mu_e=3.986004418e+14
    r_e=6.371e+3
    a=pow(mu_e/(mm*mm),1/3.)
    return a*(1-ecc)-r_e, a*(1+ecc)-r_e

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(description=__doc__,add_help=False)
    ap.add_argument("--help",action="help",help="Print this help message")
    ap.add_argument("--list","-l",action="store_true",help="only list "\
            "names and id numbers of the objects, which are selected, "\
            "do not generate tle file.")
    ap.add_argument("--filter","-f",action="store",type=str,default=None,
            help="specify a filter list; if a none exsistent file is specified, "\
                    "the file is created and filled with a template of the syntax "\
                    "(if none is specified then online loading is disabled)")
    ap.add_argument("--output","-o",action="store",default="tles.txt",
            help="specify the output file (default is \"tles.txt\")")
    ap.add_argument("--user-tles","-u",action="store",type=str,default=None,
            help="specify the list of manual tles, which will always be included")
    ap.add_argument("--no-online","-n",action="store_true",
            help="disable reading online tles, only use user defined tles")
    ap.add_argument("--force-user-filtering",action="store_true",
            help="force the user tles to be filtered by the filter as well")
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
    if ns.filter is not None:
        if _verbose:
            print("Loading filter list from "+ns.filter+" ...",file=sys.stderr)
        try:
            with open(ns.filter,"rt") as ff:
                for l in ff:
                    l=l.rstrip(" \r\n")
                    if len(l)<1 or l[0]=="#":
                        continue
                    elif l[0]=="?" or l[0]=="\\":
                        if len(l[1:].strip())>0:
                            filterlist["name"].append(l[1:])
                        elif not _quiet:
                            print("ERROR: An empty name is not a valid filter!",
                                    file=sys.stderr)
                    elif l[0]=="$":
                        if all(c.isdigit() for c in l[1:].strip()):
                            filterlist["id"].append(int(l[1:].strip()))
                        elif not _quiet:
                            print("ERROR: \""+l[1:]+"\" is not a valid NORAD "\
                                    "ID!",file=sys.stderr)
                    elif l[0]=="~":
                        match=re.fullmatch("^~(\d{1,2}\d{,2}?)-?((\d{,3})"\
                                "([a-zA-Z]{,3})?)?\s*$",l)
                        if match is not None:
                            filterlist["launch"].append({
                                "year":int(match.group(1)) if match.group(1) \
                                        is not None else None,
                                "launch":int(match.group(3)) if match.group(3) \
                                        is not None else None,
                                "object":match.group(4)
                                })
                        elif not _quiet:
                            print("ERROR: \""+l[1:]+"\" is not a valid launch "\
                                    "designator!",file=sys.stderr)
                    elif l[0]=="%":
                        match=re.fullmatch("^%(inc|apo|peri)\s+{\s*([\d.+-eE]+)\s*,"\
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
                    print("ERROR: Filter list contains no valid filters!",file=sys.stderr)
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
                            "# ^^Matches all satellites launched in 2018\n"\
                            "# An extended version with the year beeing written in as "\
                            "4 digits is also available (but the year has to be "\
                            "seperated by a hyphon \"-\" from the launch number)\n"\
                            "#~2018-002\n"\
                            "# ^^Matches all objects launched with the 2nd launch "\
                            "of 2018\n\n"\
                            "# Orbit parameter filter:\n"\
                            "# All satellites with the apropriate parameter in the "\
                            "range specified in the braces\n"\
                            "# One of \"inc\" (inclination), \"apo\" (apoapsis height),"\
                            "\"peri\" (periapsis height) prefixed with \"%\" and "\
                            "followed by curly braces in which the lower and upper "\
                            "(inclusiv) bounds of the range.\n"\
                            "#%inc {40,60}\n"\
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
    elif ns.filter is None and ns.user_tles is None:
        if not _quiet:
            print("ERROR: A filter is required if no user tles are provided!",
                    file=sys.stderr)
        sys.exit(1)
    else:
        if not _quiet:
            print("WARNING: If no filter is specified, online loading is disabled!",
                    file=sys.stderr)
        ns.no_online=True

    tles=[]
# load user tles
    try:
        if ns.user_tles is not None:
            with open(ns.user_tles,"rb") as uf:
                if _verbose:
                    print("Reading user defined TLEs ...",file=sys.stderr)
                    oc=len(tles)
                tles.extend(parse_tle_bytes(uf.read()))
                if _verbose:
                    print("Done reading user TLEs ("+str(len(tles)-oc)+" tles found)",
                            file=sys.stderr)
        elif _verbose:
            print("No file given for user tles. Skipping",file=sys.stderr)
    except IOError as ioe:
        if not _quiet:
            print("ERROR: Failed to read file "+ns.user_tles+"! Skipping! ("+str(ioe)+")",
                    file=sys.stderr)

# filter user tles (if forced)
    if ns.force_user_filtering:
        if _verbose:
            print("Filtering user supplied TLEs ...",file=sys.stderr)
        told=tles
        tles=[]
        for tle in told:
            found=False
            for nf in filterlist["name"]:
                if tle.name.upper().startswith(nf.upper()):
                    tles.append(tle)
                    found=True
                    break
            if found:
                continue
            for launf in filterlist["launch"]:
                if ("%(year)02d%(launch)03d%(object)-s" % tle.desig).upper()\
                        .startswith(launf.upper()):
                    tles.append(tle)
                    found=True
                    break
            if found:
                continue
            for idf in filterlist["id"]:
                if all(c.isdigit() for c in idf) and tle.id==int(idf):
                    tles.append(tle)
                    found=True
                    break
            if found:
                continue
            for ff in filterlist["field"]:
                peri, apo = peri_apo_from_mm_ecc(tle.mm, tle.ecc)
                if ff["field"]=="inc":
                    if tle.inc<=ff["max"] and tle.inc>=ff["min"]:
                        tles.append(tle)
                        found=True
                        break
                elif ff["field"]=="peri":
                    if peri<=ff["max"] and peri>=ff["min"]:
                        tles.append(tle)
                        found=True
                        break
                elif ff["field"]=="apo":
                    if apo<=ff["max"] and apo>=ff["min"]:
                        tles.append(tle)
                        found=True
                        break
        if _verbose:
            print("Done filtering user supplied TLEs ("+str(len(tles))+\
                    "/"+str(len(told))+" selected)",file=sys.stderr)

# load online tles
    if not ns.no_online:
        if _verbose:
            print("Fetching online TLEs ...",file=sys.stderr)
            print("Reading SATCAT ...",file=sys.stderr)
        altsatnames=[]
        with rq.urlopen("http://www.celestrak.com/pub/satcat-annex.txt") as scar:
            for bl in scar:
                l=bl.decode("ascii").rstrip("\r\n")
                le=l.split("|")
                if len(le)>1 and all(c.isdigit() for c in le[0]):
                    altsatnames.append({
                        "id":int(le[0]),
                        "names":[n.strip() for n in le[1:]]})
# read in satellite catalog (discard decayed satellites)
        satcat=[]
        with rq.urlopen("http://www.celestrak.com/pub/satcat.txt") as scr:
            for bl in scr:
                l=bl.decode("ascii").rstrip("\r\n")
                if l[21]=="D":
                    continue
                launch_s=l[0:11]
                if re.match("\s*[-\+\d]+-[-\+\d]+\a*",launch_s) is not None:
                    launch={"year":int(launch_s.split("-")[0]),
                            "launch":int(launch_s.split("-")[1][0:3]),
                             "object":launch_s.split("-")[1][3:].strip()}
                nid_s=l[13:18]
                if re.match("\s*[-\+\d\.eE]+",nid_s) is not None:
                    nid=int(nid_s)
                name_s=l[23:47]
                names=[name_s.strip()]
                if "&" in name_s:
                    names=[n.strip() for n in name_s.split("&")]
                if "nid" in locals() and nid in [an["id"] for an in altsatnames]:
                    names.extend(altsatnames[[an["id"] for an in altsatnames].\
                            index(nid)]["names"])
                inc_s=l[96:101]
                if re.match("\s*[-\+\d\.eE]+",inc_s) is not None:
                    inc=float(inc_s)
                apo_s=l[103:109]
                if re.match("\s*[-\+\d\.eE]+",apo_s) is not None:
                    apo=int(apo_s)
                peri_s=l[111:117]
                if re.match("\s*[-\+\d\.eE]+",peri_s) is not None:
                    prei=int(peri_s)
                orbc_s=l[129:132]
                satcat.append({
                    "raw":{"launch":launch_s, "nid":nid_s, "name":name_s,
                        "inc":inc_s, "apo":apo_s, "peri":peri_s, "orbc":orbc_s},
                    "launch":launch if "launch" in locals() else None,
                    "nid":nid if "nid" in locals() else None,
                    "names":names if len(names)>1 or len(names[0])>0 else None,
                    "inc":inc if "inc" in locals() else None,
                    "apo":apo if "apo" in locals() else None,
                    "peri":peri if "peri" in locals() else None })
        if _verbose:
            print("SATCAT loaded; "+str(len(satcat))+" not decayed satellites "\
                    "found!",file=sys.stderr)
            print("Compiling list of TLEs to download...",file=sys.stderr)
# compile list of TLEs to download
        dlids=[]
        dlscentry=[]
    # check name filters
        idcnt=len(dlids)
        for nf in filterlist["name"]:
            found=False
            for usn in [tle["name"] for tle in tles]:
                if usn.upper().startswith(nf.strip().upper()):
                    found=True
                    break
            if found==True:
                continue
            for scent in satcat:
                for satn in scent["names"]:
                    if satn.upper().startswith(nf.strip().upper()):
                        dlids.append(scent["nid"])
                        dlscentry.append(scent)
                        found=True
                        break
                if found==True:
                    break
            else:
                if not _quiet:
                    print("WARNING: No entry found for \"name\" filter \""+\
                            str(nf)+"\"!",file=sys.stderr)
        if _verbose:
            print("Added",len(dlids)-idcnt,"IDs from \"name\" filters",
                    file=sys.stderr)
    # check id filters
        idcnt=len(dlids)
        for idf in filterlist["id"]:
            found=False
            for usid in [tle["id"] for tle in tles]:
                if usid==idf:
                    found=True
                    break
            if found==True:
                continue
            for scent in satcat:
                if scent["nid"]==idf:
                    dlids.append(scent["nid"])
                    dlscentry.append(scent)
                    found=True
                    break
            else:
                if not _quiet:
                    print("WARNING: No entry found for \"id\" filter \""+str(idf)+\
                            "\"!",file=sys.stderr)
        if _verbose:
            print("Added",len(dlids)-idcnt,"IDs from \"id\" filters",
                    file=sys.stderr)
    # check launch designator filters
        idcnt=len(dlids)
        for lf in filterlist["launch"]:
            found=False
            for ul in [tle["id"] for tle in tles]:
                if ul["launch"]["year"]==(lf["year"]%100) and \
                        (lf["launch"] is None or ul["launch"]["launch"]==\
                        lf["launch"]) and (lf["object"] is None or \
                        ul["launch"]["object"]==lf["object"]):
                    found=True
                    break
            if found==True:
                continue
            for scent in satcat:
                if scent["launch"] is not None and \
                        (scent["launch"]["year"]%100)==(lf["year"]%100) and \
                        (lf["launch"] is None or scent["launch"]["launch"]==\
                        lf["launch"]) and (lf["object"] is None or scent["launch"]\
                        ["object"]==lf["object"]):
                    dlids.append(scent["nid"])
                    dlscentry.append(scent)
                    found=True
                    break
            else:
                if not _quiet:
                    print("WARNING: No entry found for \"launch designator\" "\
                            "filter \""+str(lf)+"\"!",file=sys.stderr)
        if _verbose:
            print("Added",len(dlids)-idcnt,"IDs from \"launch designator\" "\
                    "filters",file=sys.stderr)
    # check field filters
        idcnt=len(dlids)
        for ff in filterlist["field"]:
            for scent in satcat:
                if scent[ff["field"]]<=ff["max"] and scent[ff["field"]]>=ff["min"]:
                    dlids.append(scent["nid"])
                    dlscentry.append(scent)
        if _verbose:
            print("Added",len(dlids)-idcnt,"IDs from \"orbit parameter\" filters",
                    file=sys.stderr)
    # how many objects to download
        if len(dlids)==0 and not _quiet:
            print("WARNING: No IDs to download!",file=sys.stderr)
        elif _verbose:
            print(len(dlids)," TLEs to download...",file=sys.stderr)
        
# downloading TLEs
        otlecnt=len(tles)

        from html.parser import HTMLParser

        class TLE_HTML(HTMLParser):
            def __init__(self,*args,**kwargs):
                self.read_tle_data=False
                self.tle_data=""
                HTMLParser.__init__(self,*args,**kwargs)
            def handle_starttag(self, tag, attr):
                if tag=="pre":
                    self.read_tle_data=True
            def handle_endtag(self, tag):
                if tag=="pre":
                    self.read_tle_data=False
            def handle_data(self, data):
                if "read_tle_data" in dir(self) and self.read_tle_data:
                    self.tle_data+=data


        for dlid, dlentry in zip(dlids,dlscentry):
            ts=None
            with rq.urlopen("http://www.celestrak.com/cgi-bin/TLE.pl?CATNR="+\
                    str(dlid)) as tlr:
                tp=TLE_HTML()
                tp.feed(tlr.read().decode())
                ts=parse_tle_bytes(tp.tle_data.lstrip().encode("ascii"))
            if ts is not None and len(ts)>0:
                tles.extend(ts)
            elif not _quiet:
                print("WARNING: No TLE found for \""+str(dlentry["names"][0])+"\":"+\
                        str(dlid)+" (Note: Orbit comment: \""+str(dlentry["raw"]\
                        ["orbc"])+"\")!",file=sys.stderr)
        if _verbose:
            print("Downloaded",len(tles)-otlecnt,file=sys.stderr)

    if _verbose:
        print("A total of "+str(len(tles))+" TLEs have been loaded",file=sys.stderr)

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
