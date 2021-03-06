import os
import sys
import apa
import pybio
import shutil
from collections import Counter

def process(comps_id):
    name_folder = "motifs"
    fasta_folder = os.path.join(apa.path.comps_folder, comps_id, name_folder, "fasta")
    tab_folder = os.path.join(apa.path.comps_folder, comps_id, name_folder, "tab")

    if comps_id!=None:
        comps = apa.comps.read_comps(comps_id)
        genome = comps.species
        tab_file = os.path.join(apa.path.comps_folder, comps_id, "%s.pairs_de.tab" % comps_id)
        dest_folder = os.path.join(apa.path.comps_folder, comps_id, name_folder)

    assert(len(dest_folder)>5)
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)
    os.makedirs(dest_folder)
    os.makedirs(fasta_folder)
    os.makedirs(tab_folder)

    fasta_files = {}
    tab_files = {}

    for pair_type in ["tandem", "composite", "skipped", "all"]:
        for reg in ["r", "e", "c"]:
            k = "%s_%s" % (pair_type, reg)
            fname = os.path.join(fasta_folder, k+"_intersite.fasta")
            fasta_files[k] = open(fname, "wt")

    for site in ["proximal", "distal"]:
        for pair_type in ["tandem", "composite", "skipped", "all"]:
            fname = os.path.join(tab_folder, "%s_%s_%s.tab" % (comps_id, site, pair_type))
            tab_files["%s_%s" % (site, pair_type)] = open(fname, "wt")
            tab_files["%s_%s" % (site, pair_type)].write("\t".join(["id", "chr", "strand", "pos", "event_class"])+"\n")
            for reg in ["r", "e", "c"]:
                k = "%s_%s_%s" % (site, pair_type, reg)
                fname = os.path.join(fasta_folder, k+".fasta")
                fasta_files[k] = open(fname, "wt")

    pc_thr = 0.1
    fisher_thr = 0.1
    pair_dist = 450
    control_pc_thr = 0.1
    control_fisher_thr = 0.1

    # r = repressed, e = enhanced, c = control
    stats = Counter()

    f = open(tab_file, "rt")
    header = f.readline().replace("\r", "").replace("\n", "").split("\t")
    r = f.readline()
    tab_files_index = {}
    while r:
        r = r.replace("\r", "").replace("\n", "").split("\t")
        data = dict(zip(header, r))
        chr = data["chr"]
        strand = data["strand"]
        gene_id = data["gene_id"]
        gene_name = data["gene_name"]
        proximal_pos = int(data["proximal_pos"])
        distal_pos = int(data["distal_pos"])

        pc = float(data["pc"])
        fisher = float(data["fisher"])
        pair_type = data["pair_type"]

        reg_siteup = None
        if pc>0 and abs(pc)>pc_thr and fisher<fisher_thr:
            reg_siteup = "e"
        elif pc<0 and abs(pc)>pc_thr and fisher<fisher_thr:
            reg_siteup = "r"
        elif abs(pc)<control_pc_thr and fisher>control_fisher_thr:
            reg_siteup = "c"

        if reg_siteup in [None]:
            r = f.readline()
            continue

        if abs(proximal_pos-distal_pos)<pair_dist:
            r = f.readline()
            continue

        reg_sitedown = {"e":"r", "r":"e", "c":"c"}[reg_siteup]
        stats["%s.%s" % (reg_siteup, pair_type)] += 1
        stats["%s.%s" % (reg_siteup, "all")] += 1

        seq_up = pybio.genomes.seq(genome, chr, strand, proximal_pos, start=-200, stop=200)
        seq_down = pybio.genomes.seq(genome, chr, strand, distal_pos, start=-200, stop=200)

        seq_proximal_distal = pybio.genomes.seq_direct(genome, chr, strand, proximal_pos, distal_pos)
        fasta_files["%s_%s" % (pair_type, reg_siteup)].write(">%s:%s %s%s:%s-%s\n%s\n" % (gene_id, gene_name, strand, chr, proximal_pos, distal_pos, seq_proximal_distal))
        fasta_files["%s_%s" % ("all", reg_siteup)].write(">%s:%s %s%s:%s-%s\n%s\n" % (gene_id, gene_name, strand, chr, proximal_pos, distal_pos, seq_proximal_distal))

        fasta_files["proximal_%s_%s" % (pair_type, reg_siteup)].write(">%s:%s %s%s:%s\n%s\n" % (gene_id, gene_name, strand, chr, proximal_pos, seq_up))
        fasta_files["proximal_%s_%s" % ("all", reg_siteup)].write(">%s:%s %s%s:%s\n%s\n" % (gene_id, gene_name, strand, chr, proximal_pos, seq_up))
        fasta_files["distal_%s_%s" % (pair_type, reg_sitedown)].write(">%s:%s %s%s:%s\n%s\n" % (gene_id, gene_name, strand, chr, distal_pos, seq_down))
        fasta_files["distal_%s_%s" % ("all", reg_sitedown)].write(">%s:%s %s%s:%s\n%s\n" % (gene_id, gene_name, strand, chr, distal_pos, seq_down))

        tab_files_index["proximal_%s" % pair_type] = tab_files_index.setdefault("proximal_%s" % pair_type, 0) + 1
        tab_files_index["proximal_%s" % "all"] = tab_files_index.setdefault("proximal_%s" % "all", 0) + 1
        tab_files_index["distal_%s" % pair_type] = tab_files_index.setdefault("distal_%s" % pair_type, 0) + 1
        tab_files_index["distal_%s" % "all"] = tab_files_index.setdefault("distal_%s" % "all", 0) + 1

        row = [str(el) for el in [tab_files_index["proximal_%s" % pair_type], chr, strand, proximal_pos, reg_siteup]]
        tab_files["proximal_%s" % pair_type].write("\t".join(row)+"\n")
        row = [str(el) for el in [tab_files_index["distal_%s" % pair_type], chr, strand, distal_pos, reg_sitedown]]
        tab_files["distal_%s" % pair_type].write("\t".join(row)+"\n")

        row = [str(el) for el in [tab_files_index["proximal_%s" % "all"], chr, strand, proximal_pos, reg_siteup]]
        tab_files["proximal_%s" % "all"].write("\t".join(row)+"\n")
        row = [str(el) for el in [tab_files_index["distal_%s" % "all"], chr, strand, distal_pos, reg_sitedown]]
        tab_files["distal_%s" % "all"].write("\t".join(row)+"\n")

        r = f.readline()
    f.close() # end of reading gene data

    for f in fasta_files.values():
        f.close()

    for f in tab_files.values():
        f.close()

    f_stats = open(os.path.join(dest_folder, "site_stats.tab"), "wt")
    f_stats.write("# r = repressed, e = enhanced, c = control\n")
    f_stats.write("# relative to proximal site; if proximal site = r, distal = e, and vice-versa; if proximal = c, distal is also c\n")
    for pair_type in ["tandem", "composite", "skipped", "all"]:
        for reg in ["r", "e", "c"]:
            f_stats.write("%s\t%s\t%s\n" % (pair_type, reg, stats["%s.%s" % (reg, pair_type)]))
    f_stats.close()
    #dreme(comps_id)

def dreme(comps_id):
    name_folder = "motifs"
    fasta_folder = os.path.join(apa.path.comps_folder, comps_id, name_folder, "fasta")
    dreme_folder = os.path.join(apa.path.comps_folder, comps_id, name_folder, "dreme")

    if os.path.exists(dreme_folder):
        shutil.rmtree(dreme_folder)
    os.makedirs(dreme_folder)

    for site in ["proximal", "distal"]:
        for pair_type in ["tandem", "composite", "skipped"]:
            fasta_pos = os.path.join(fasta_folder, "%s_%s_%s.fasta" % (site, pair_type, "e"))
            fasta_neg = os.path.join(fasta_folder, "%s_%s_%s.fasta" % (site, pair_type, "r"))
            fasta_con = os.path.join(fasta_folder, "%s_%s_%s.fasta" % (site, pair_type, "c"))
            dest_pos = os.path.join(dreme_folder, "%s_%s_e" % (site, pair_type))
            dest_neg = os.path.join(dreme_folder, "%s_%s_r" % (site, pair_type))
            os.system("dreme -p %s -n %s -maxk 6 -o %s -g 1000 -norc -e 0.5" % (fasta_pos, fasta_con, dest_pos))
            os.system("dreme -p %s -n %s -maxk 6 -o %s -g 1000 -norc -e 0.5" % (fasta_neg, fasta_con, dest_neg))

    #dreme -p proximal_tandem_e.fasta -n proximal_tandem_c.fasta -k 4 -o abc
