#!/usr/bin/python
# (jEdit options) :folding=explicit:collapseFolds=1:
from math import log
import sys, os, getopt, re, pprint, collections
import datetime
from optparse import OptionParser
import molparser

#{{{ parse_cmdline
#parse the command line--------------------------------------------------------------------------
def parse_cmdline():
  parser = OptionParser()
  parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
    help="quiet mode")
  parser.add_option("-s", "--sans", action="store", dest="sans_location",
    type="string", default=None,
    help="sans parser location, needed for nmrstar output")
  opts, args = parser.parse_args()
  if opts.sans_location is not None and not os.path.isfile(opts.sans_location):
    sys.stderr.write("sans_location entered is: "+opts.sans_location+"\n")
    sys.stderr.write("\n**ERROR: sans location must exist!\n")
    sys.exit(help())
  if len(args) < 11:
    sys.stderr.write("\n**ERROR: Must have 11 arguments!\n")
    sys.exit(help())
  return opts, args
  #try:
  #  opts, args = getopt.getopt(sys.argv[1:], 'h',['help'])
  #except getopt.GetoptError:
  #  help()
  #  sys.exit()
  #for o, a in opts:
  #  if o in ("-h", "--help"):
  #    help()
  #    sys.exit()
  #  if o in ("-q", "--quiet"):
  #    quiet = True
  #if len(args) < 2:
  #  sys.stderr.write("\n**ERROR: User must specify output directory and input PDB file\n")
  #  sys.exit(help())
  #return opts, args;
  #else:
  #  outdir = args[0]
  #  if (os.path.isdir(outdir)):
  #    return outdir, args[1:]
  #  else:
  #    sys.stderr.write("\n**ERROR: First argument must be a directory!\n")
  #    sys.exit(help())
#------------------------------------------------------------------------------------------------
#}}}

#{{{ help
def help():
  print """
This script parses the output files from the various programs in MP to duplicate
a set of the oneline analysis.  This script reimplements a significant portion
of analysis.php.

USAGE:   python molparser.py [MP output files]

  [MP output files] In order: pdbname (string)
                              model number
                              clashlist output file
                              cbetadev output file
                              rota output file
                              rama output file
                              protein bond geometry output file
                              rna bond geometry output file
                              dna bond geometry output file
                              base ppperp output file
                              suitname output file
                              maxBfactor file
                              tau/omega file
                              disulfides file
                              output_directory
                              hydrogen-positions (nuclear or ecloud)
                              molprobity-flips (original/build/nobuild)

FLAGS:
  -h     Print this help message
"""
#}}}

#{{{ list_residues
def list_residues(model):
  res = []
  with open(model) as f:
    for line in f:
      if line.startswith("ATOM") or line.startswith("HETATM"):
        cnit = line[20:27]+line[17:20]
        if not cnit in res:
          res.append(cnit)
  return res
#}}}

#{{{ residue_analysis_old
def residue_analysis_old(files, quiet):
  list_res = list_residues(files[0])
  #print list_res
  out = ""

  clash = molparser.loadClashlist(files[2])
  cbdev = molparser.loadCbetaDev(files[3])
  badCbeta = molparser.findCbetaOutliers(cbdev)
  rota = molparser.loadRotamer(files[4])
  badRota = molparser.findRotaOutliers(rota);
  rama = molparser.loadRamachandran(files[5])
  geom = molparser.loadBondGeometryReport(files[6], "protein")
  geom.update(molparser.loadBondGeometryReport(files[7], "rna"))
  geom.update(molparser.loadBondGeometryReport(files[8], "dna"))
  totalRes = len(geom) # total residues
  outBondCount = 0
  outAngleCount = 0
  totalBonds = 0
  totalAngles = 0
  for res, data in geom.iteritems():
    if 'isbondOutlier' in data:
      if(data['isbondOutlier']):
        outBondCount += data['bondoutCount']
      totalBonds += data['bondCount']
    if 'isangleOutlier' in data:
      if(data['isangleOutlier']):
        outAngleCount += data['angleoutCount']
      totalAngles += data['angleCount']
  #pprint.pprint(geom)
  if not (totalRes > 0 and totalBonds > 0 and totalAngles > 0):
    sys.stderr.write("No standard residues detected in "+files[0]+"!\n")

  bondOut = molparser.findBondGeomOutliers(geom)
  angleOut = molparser.findAngleGeomOutliers(geom)
  #print clash
  pperp = molparser.loadBasePhosPerp(files[9])
  badPperp = molparser.findBasePhosPerpOutliers(pperp)
  suites = molparser.loadSuitenameReport(files[10])
  badSuites = molparser.findSuitenameOutliers(suites)

  for res in list_res:
    outCount = 0
    outCountSep = 0
    #print res in clash['clashes']
    #if res in clash['clashes']:
    #  outCount += 1
    #  outCountSep += 1

    out = out+os.path.basename(files[0])+":"+(os.path.basename(files[0])[:-4])[:4]+":"+files[1]+":"+res
    if res in clash['clashes']:
      outCount += 1
      outCountSep += 1
      out = out+":"+repr(clash['clashes'][res])+":"+clash['clashes-with'][res]['srcatom']+":"+clash['clashes-with'][res]['dstatom']+":"+clash['clashes-with'][res]['dstcnit']
    else:
      out += "::::"

    if res in badCbeta:
      outCountSep += 1
      out = out+":" + repr(badCbeta[res])
    else:
      out += ":"

    if res in rota:
      out = out+":" + repr(rota[res]['scorePct'])
      if (rota[res]['scorePct'] <= 1.0):
        outCount += 1
        outCountSep += 1
        out += ":OUTLIER"
      else:
        out += ":" + repr(rota[res]['rotamer'])
    else:
      out += "::"

    if res in rama:
      outCount += 1
      outCountSep += 1
      out += ":"+repr(rama[res]['scorePct'])+":"+rama[res]['eval']+":"+rama[res]['type']
    else:
      out += ":::"

    if (totalRes > 0 and totalBonds > 0 and totalAngles > 0): # catches a bug with PNA residues
      if res in bondOut:
        outCountSep += 1
        out += ":"+repr(geom[res]['bondoutCount'])+":"+geom[res]['worstbondmeasure']+":"+repr(geom[res]['worstbondvalue'])+":"+repr(geom[res]['worstbondsigma'])
      else:
        out += "::::"
      if res in angleOut:
        outCountSep += 1
        out += ":"+repr(geom[res]['angleoutCount'])+":"+geom[res]['worstanglemeasure']+":"+repr(geom[res]['worstanglevalue'])+":"+repr(geom[res]['worstanglesigma'])
      else:
        out += "::::"
    else:
      out += ":-1:-1:-1:-1:-1:-1:-1:-1"

    if (res in badCbeta) or (res in bondOut and geom[res]['bondoutCount'] > 0) or (res in angleOut and geom[res]['angleoutCount'] > 0):
      outCount += 1

    #pprint.pprint(pperp)
    pperpval = ""
    if res in badPperp:
      outCount += 1
      outCountSep += 1
      if pperp[res]['deltaOut']:
        pperpval = "OUTLIER-DELTA"
      if pperp[res]['epsilonOut']:
        pperpval = "OUTLIER-EPSILON"
    out += ":"+pperpval

    if res in suites:
      out = out+":"+repr(suites[res]['suiteness'])
      if suites[res]['isOutlier']:
        outCount += 1
        outCountSep += 1
        out += ":OUTLIER:"+suites[res]['triage']
      else:
        out += ":"+suites[res]['conformer']+":"
    else:
      out += "::"
    out += repr(outCountSep)+":"+repr(outCount)
    out += "\n"
  print out

#}}}

#{{{ setup_nmrstar
def setup_nmrstar(header, output_str, filename, sans_loc):
  import bmrb
  #if os.path.isfile(output_str):
  #  saver = bmrb.Saveframe.from_file(output_str)
  #  loop = saver.get_loop_by_category("Residue_analysis")
  #else:

  if not os.path.isfile(output_str):
    entrier = bmrb.Entry.from_scratch((os.path.basename(filename)[:-4])[:4]+"_residue")
    software_saver = bmrb.Saveframe.from_scratch("MolProbity", "Software")
    software_saver.add_tag("Sf_category", "software")
    software_saver.add_tag("Sf_framecode", "MolProbity")
    software_saver.add_tag("Entry_ID", "?")
    software_saver.add_tag("ID", "1")
    software_saver.add_tag("Name", "MolProbity")
    software_saver.add_tag("Version", "4.0")
    software_saver.add_tag("Details", ".")
    software_saver2 = bmrb.Saveframe.from_scratch("CYRANGE", "Software")
    software_saver2.add_tag("Sf_category", "software")
    software_saver2.add_tag("Sf_framecode", "CYRANGE")
    software_saver2.add_tag("Entry_ID", "?")
    software_saver2.add_tag("ID", "2")
    software_saver2.add_tag("Name", "CYRANGE")
    software_saver2.add_tag("Version", "2.0")
    software_saver2.add_tag("Details", ".")
    entrier.add_saveframe(software_saver)
    entrier.add_saveframe(software_saver2)

    saver = bmrb.Saveframe.from_scratch("Structure_validation_residue", "Structure_validation_residue")
    saver.add_tag("Sf_category", "structure_validation")
    saver.add_tag("Sf_framecode", "Structure_validation_residue")
    saver.add_tag("Entry_ID", "?")
    saver.add_tag("List_ID", "1")
    #saver.add_tag("Software_label", "molprobity")
    #saver.add_tag("Software_version", "4.0")
    #saver.add_tag("File_name", os.path.basename(filename))
    saver.add_tag("PDB_accession_code", (os.path.basename(filename)[:-4])[:4])
    saver.add_tag("Date_analyzed", datetime.date.today().isoformat())
    entrier.add_saveframe(saver)

    software_loop = bmrb.Loop.from_scratch(category="Residue_analysis_software")
    loop_tags = ["Software_ID", "Software_label", "Method_ID", "Method_label", "Entry_ID", "Structure_validation_oneline_list_ID"]
    software_loop.add_columns(loop_tags)
    software_loop.add_data(["1", "MolProbity", ".", ".", "?", "1"])
    software_loop.add_data(["2", "CYRANGE", ".", ".", "?", "1"])
    saver.add_loop(software_loop)

    with open(output_str[:-4]+".header", "a+") as str_write:
      str_write.write(str(entrier))
  loop = bmrb.Loop.from_scratch(category="Residue_analysis")
  header = ["ID"]+header
  loop.add_columns(header)
  return loop
#}}}

#{{{ write_nmrstar
def write_nmrstar(output_str, loop):
  print_header = False
  if not os.path.isfile(output_str):
    print_header = True
  #  saver.add_loop(loop)
  #print loop.get_data_as_csv(print_header, True)
  loop_csv = loop.get_data_as_csv(print_header, True)
  with open(output_str, 'a+') as str_write:
    str_write.write(loop_csv)
  #print saver
#}}}

#{{{ residue_analysis
def residue_analysis(files, quiet, sans_location):
  list_res = list_residues(files[0])
  #print list_res
  #out = []
  #need h position, flip info,
  header = ["Filename",                                    #0
            "PDB_accession_code",                          #1
            "PDB_model_num",                               #2
            "Hydrogen_positions",                          #3
            "MolProbity_flips",                            #4
            "Cyrange_core_flag",                           #5
            "Two_letter_chain_ID",                         #6
            "PDB_strand_ID",                               #7
            "PDB_residue_no",                              #8
            "PDB_ins_code",                                #9
            "PDB_residue_name",                            #10
            "Assembly_ID",                                 #11
            "Entity_assembly_ID",                          #12
            "Entity_ID",                                   #13
            "Comp_ID",                                     #14
            "Comp_index_ID",                               #15
            "Clash_value",                                 #16
            "Clash_source_PDB_atom_name",                  #17
            "Clash_destination_PDB_atom_name",             #18
            "Clash_destination_PDB_strand_ID",             #19
            "Clash_destination_PDB_residue_no",            #20
            "Clash_destination_PDB_ins_code",              #21
            "Clash_destination_PDB_residue_name",          #22
            "Cbeta_deviation_value",                       #23
            "Rotamer_score",                               #24
            "Rotamer_name",                                #25
            "Ramachandran_phi",                            #26
            "Ramachandran_psi",                            #27
            "Ramachandran_score",                          #28
            "Ramachandran_evaluation",                     #29
            "Ramachandran_type",                           #30
            "Bond_outlier_count",                          #31
            "Worst_bond",                                  #32
            "Worst_bond_value",                            #33
            "Worst_bond_sigma",                            #34
            "Angle_outlier_count",                         #35
            "Worst_angle",                                 #36
            "Worst_angle_value",                           #37
            "Worst_angle_sigma",                           #38
            "RNA_phosphate_perpendicular_outlier",         #39
            "RNA_suitness_score",                          #40
            "RNA_suite_conformer",                         #41
            "RNA_suite_triage",                            #42
            "Max_b_factor",                                #43
            "Tau_angle",                                   #44
            "Omega_dihedral",                              #45
            "Disulfide_chi1",                              #46
            "Disulfide_chi2",                              #47
            "Disulfide_chi3",                              #48
            "Disulfide_ss_angle",                          #49
            "Disulfide_ss",                                #50
            "Disulfide_ss_angle_prime",                    #51
            "Disulfide_chi2prime",                         #52
            "Disulfide_chi1prime",                         #53
            "Outlier_count_separate_geometry",             #54
            "Outlier_count",                               #55
            "Entry_ID",                                    #56
            "Structure_validation_residue_list_ID"         #57
  ]

  output_dir = os.path.realpath(files[14])
  if sans_location:
    output_str = (os.path.basename(files[0])[:-4])[:4]+"-"+files[16]+"-residue-str.csv"
    loop = setup_nmrstar(header[2:], output_str, files[0], sans_location)

  clash = molparser.loadClashlist(files[2])
  cbdev = molparser.loadCbetaDev(files[3])
  badCbeta = molparser.findCbetaOutliers(cbdev)
  rota = molparser.loadRotamer(files[4])
  badRota = molparser.findRotaOutliers(rota);
  rama = molparser.loadRamachandran(files[5])
  geom = molparser.loadBondGeometryReport(files[6], "protein")
  geom.update(molparser.loadBondGeometryReport(files[7], "rna"))
  geom.update(molparser.loadBondGeometryReport(files[8], "dna"))
  bfactor = molparser.loadMaxBfactor(files[11])
  tauomega = molparser.loadTauOmegaReport(files[12])
  disulf = molparser.loadDisulfidesReport(files[13])
  totalRes = len(geom) # total residues
  outBondCount = 0
  outAngleCount = 0
  totalBonds = 0
  totalAngles = 0
  for res, data in geom.iteritems():
    if 'isbondOutlier' in data:
      if(data['isbondOutlier']):
        outBondCount += data['bondoutCount']
      totalBonds += data['bondCount']
    if 'isangleOutlier' in data:
      if(data['isangleOutlier']):
        outAngleCount += data['angleoutCount']
      totalAngles += data['angleCount']
  #pprint.pprint(geom)
  if not (totalRes > 0 and totalBonds > 0 and totalAngles > 0):
    sys.stderr.write("No standard residues detected in "+files[0]+"!\n")

  bondOut = molparser.findBondGeomOutliers(geom)
  angleOut = molparser.findAngleGeomOutliers(geom)
  #print clash
  pperp = molparser.loadBasePhosPerp(files[9])
  badPperp = molparser.findBasePhosPerpOutliers(pperp)
  suites = molparser.loadSuitenameReport(files[10])
  badSuites = molparser.findSuitenameOutliers(suites)

  csv_out = []
  if not quiet:
    csv_out.append("#"+(":".join(header)))

  for res in list_res:
    out = []
    outCount = 0
    outCountSep = 0
    #print res in clash['clashes']
    #if res in clash['clashes']:
    #  outCount += 1
    #  outCountSep += 1

    out.append(os.path.basename(files[0])) # filename
    out.append((os.path.basename(files[0])[:-4])[:4]) # pdbID
    out.append(files[1]) # model num
    flips_used = files[16]
    #print flips_used
    #print type(flips_used)
    #print flips_used == "na"
    if flips_used == "na":
      out.append("original")
    else:
      out.append(files[15]) # Hydrogen_positions
    out.append(files[16]) # MolProbity_flips
    if "-cyranged" in os.path.basename(files[0]):
      out.append("core")
    else:
      out.append("full") # Cyrange_core_flag (tells whether this structure is core or full
    out.append(res[0:2]) # Two_letter_chain_ID
    out.append(res[1:2]) # PDB_strand_ID
    out.append(res[2:6]) # PDB_residue_no
    out.append(res[6:7]) # PDB_ins_code
    out.append(res[7:10]) # PDB_residue_name

    out.append("") # "Assembly_ID",       bmrb specific, to be filled in later
    out.append("") # "Entity_assembly_ID",bmrb specific, to be filled in later
    out.append("") # "Entity_ID",         bmrb specific, to be filled in later
    out.append("") # "Comp_ID",           bmrb specific, to be filled in later
    out.append("") # "Comp_index_ID",     bmrb specific, to be filled in later

    if res in clash['clashes']:
      outCount += 1
      outCountSep += 1
      #out = out+":"+repr(clash['clashes'][res])+":"+clash['clashes-with'][res]['srcatom']+":"+clash['clashes-with'][res]['dstatom']+":"+clash['clashes-with'][res]['dstcnit']
      out.append(clash['clashes'][res])
      out.append(clash['clashes-with'][res]['srcatom'])
      out.append(clash['clashes-with'][res]['dstatom'])
      dest_cnit = clash['clashes-with'][res]['dstcnit']
      out.append(dest_cnit[0:2])
      out.append(dest_cnit[2:6])
      out.append(dest_cnit[6:7])
      out.append(dest_cnit[7:10])
    else:
      out.extend(["","","","","","",""])

    if res in badCbeta:
      outCountSep += 1
      out.append(badCbeta[res])
    else:
      out.append("")

    if res in rota:
      out.append(rota[res]['scorePct'])
      if (rota[res]['scorePct'] <= 1.0):
        outCount += 1
        outCountSep += 1
        out.append("OUTLIER")
      else:
        out.append(rota[res]['rotamer'])
    else:
      out.extend(["",""])

    if res in rama:
      outCount += 1
      outCountSep += 1
      out.append(rama[res]['phi'])
      out.append(rama[res]['psi'])
      out.append(rama[res]['scorePct'])
      out.append(rama[res]['eval'])
      out.append(rama[res]['type'])
    else:
      out.extend(["","","","",""])

    if (totalRes > 0 and totalBonds > 0 and totalAngles > 0): # catches a bug with PNA residues
      if res in bondOut:
        outCountSep += 1
      if res in geom and 'bondoutCount' in geom[res]:
        out.append(geom[res]['bondoutCount'])
        out.append(geom[res]['worstbondmeasure'])
        out.append(geom[res]['worstbondvalue'])
        out.append(geom[res]['worstbondsigma'])
      else:
        out.extend(['','','',''])
      if res in angleOut:
        outCountSep += 1
      if res in geom and 'angleoutCount' in geom[res]:
        out.append(geom[res]['angleoutCount'])
        out.append(geom[res]['worstanglemeasure'])
        out.append(geom[res]['worstanglevalue'])
        out.append(geom[res]['worstanglesigma'])
      else:
        out.extend(['','','',''])
    else:
      out.extend([-1,-1,-1,-1,-1,-1,-1,-1])

    if (res in badCbeta) or (res in bondOut and geom[res]['bondoutCount'] > 0) or (res in angleOut and geom[res]['angleoutCount'] > 0):
      outCount += 1

    #pprint.pprint(pperp)
    pperpval = ""
    if res in badPperp:
      outCount += 1
      outCountSep += 1
      if pperp[res]['deltaOut']:
        pperpval = "OUTLIER-DELTA"
      if pperp[res]['epsilonOut']:
        pperpval = "OUTLIER-EPSILON"
    out.append(pperpval)

    if res in suites:
      out.append(suites[res]['suiteness'])
      if suites[res]['isOutlier']:
        outCount += 1
        outCountSep += 1
        out.append("OUTLIER")
        out.append(suites[res]['triage'])
      else:
        out.append(suites[res]['conformer'])
        out.append("")
    else:
      out.extend(["","",""])

    if res in bfactor:
      out.append(repr(bfactor[res]['maxB']))
    else:
      out.append("")

    if res in tauomega:
      out.extend([tauomega[res]['tau'], tauomega[res]['omega']])
    else:
      out.extend(["",""])

    if res in disulf:
      out.extend([disulf[res]['chi1'],disulf[res]['chi2'],disulf[res]['chi3'],disulf[res]['cb-s-s'],disulf[res]['s-s'],disulf[res]['s-s-cbprime'],disulf[res]['chi2prime'],disulf[res]['chi1prime']])
    else:
      out.extend(["","","","","","","",""])

    out.extend([outCountSep,outCount])

    # This is for the entry_ID and list_ID
    out.extend(["","1"])
    #print out
    csv_out.append(":".join(str(e) for e in out))
    if sans_location:
      #add an extra column on front for the "Residue_analysis.ID" for possible use as a primary key
      loop.add_data(["."]+(["." if x=="" else x for x in out][2:]))

  output_file = (os.path.basename(files[0])[:-4])[:4]+"-"+files[16]+"-residue.csv"

  #if os.path.isfile(output_file):
  #  sys.stderr.write("output_file: "+output_file+' exists\n')
  with open(output_file, "a+") as out_write:
    out_write.write("\n".join(csv_out))
    out_write.write('\n')

  #sys.stderr.write(" ".join(os.listdir(os.path.dirname(output_str))))
  if sans_location:
    write_nmrstar(output_str, loop)


#}}}

# for testing
# py-residue-analysis.py -s '/home/vbc3/programs/sans/python' ../../../1ubqH.pdb 1 1ubqH_001-clashlist 1ubqH_001-cbdev 1ubqH_001-rotalyze 1ubqH_001-ramalyze 1ubqH_001-dangle_protein 1ubqH_001-dangle_rna 1ubqH_001-dangle_dna 1ubqH_001-prekin_pperp 1ubqH_001-suitename 1ubqH_001-dangle_maxb 1ubqH_001-dangle_tauomega 1ubqH_001-dangle_ss .. cmd1 cmd2
# py-residue-analysis.py -s '/home/vbc3/programs/sans/python' ../../../1UBQ.pdb 1 1UBQ_001FH-clashlist 1UBQ_001FH-cbdev 1UBQ_001FH-rotalyze 1UBQ_001FH-ramalyze 1UBQ_001FH-dangle_protein 1UBQ_001FH-dangle_rna 1UBQ_001FH-dangle_dna 1UBQ_001FH-prekin_pperp 1UBQ_001FH-suitename 1UBQ_001FH-dangle_maxb 1UBQ_001FH-dangle_tauomega 1UBQ_001FH-dangle_ss .. cmd1 cmd2
# ../../../MolProbity/cmdline/molprobity-htc/py-residue-analysis.py ../condor_sub_files_0000_old6/pdbs/0000/orig/1a03_001.pdb 001 1a03_001-clashlist 1a03_001-cbdev 1a03_001-rotalyze 1a03_001-ramalyze 1a03_001-dangle_protein 1a03_001-dangle_rna 1a03_001-dangle_dna 1a03_001-prekin_pperp 1a03_001-suitename 1a03_001-dangle_maxb 1a03_001-dangle_tauomega 1a03_001-dangle_ss . nuclear orig

# Takes as input a whole series of different results files from MP analysis
# e.g. clashlist, ramalyze, rotalyze, dangle, pperp, cbdev, etc.
if __name__ == "__main__":
  opts, args = parse_cmdline()
  #analyze_file(args)
  residue_analysis(args, opts.quiet, opts.sans_location)
  #for arg in args:
  #  if os.path.exists(arg):
  #    if (os.path.isfile(arg)):
  #      analyze_file(arg)
        #files = os.listdir(arg)
        #print arg
        #for f in files:
        #  arg_file = os.path.join(arg, f)
        #  if (not os.path.isdir(os.path.realpath(arg_file))):
        #    #print os.path.abspath(arg_file)
        #    #print os.path.join(arg,f)
        #    analyze_file(outdir, arg_file)
      #else:
      #  analyze_file(outdir, arg)
   # else:
   #   print "trouble opening " + arg
