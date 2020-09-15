#!/usr/bin/python

import sys
from seidel_positions import *
import seidel_common
import seidel_par_common
import seidel_df_common
from functools import reduce

def ilen(iterable):
    return reduce(lambda sum, element: sum + 1, iterable, 0)

def dump_terminal_task(config, pref):
    if config["debug_printf"]:
        sys.stdout.write(pref+"printf(\"Creating terminal task for (")
        for dim in range(config["num_dims"]):
            sys.stdout.write("%d ");
        sys.stdout.write(") id = %d\\n\"");

        for dim in range(config["num_dims"]):
            sys.stdout.write(", id_"+config["dim_names"][dim])
        sys.stdout.write(", id);\n");

    sys.stdout.write(pref+"#pragma omp task \\\n")

    num_clauses = 0
    sys.stdout.write(pref+"\tinput(")
    sys.stdout.write("scenter_ref[id] >> center_in[center_size]")

    for dim in range(config["num_dims"]):
        if config["dim_configs"][dim] != seidel_positions.first and config["dim_configs"][dim] != seidel_positions.span:
            sys.stdout.write(", \\\n"+pref+"\t\t")
            sys.stdout.write("s"+config["dimref_names"][dim][0]+"_ref[id] >> "+config["dimref_names"][dim][0]+"_in["+config["dimref_names"][dim][0]+"_in_size]")
            num_clauses = num_clauses + 1

    sys.stdout.write(") \\\n")
    sys.stdout.write(pref+"\toutput(sdfbarrier_ref[0] << token[1])\n")
    sys.stdout.write(pref+"{\n")

    sys.stdout.write(pref+"\tseidel_%dd_df_finish(matrix"%config["num_dims"])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim])

    sys.stdout.write(", center_in);\n");

    sys.stdout.write(pref+"}\n\n")

def dump_create_terminal_task_fun_signature(config):
    sys.stdout.write("void create_terminal_task(double* matrix, int numiters")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int id_"+config["dim_names"][dim])

    sys.stdout.write(")")

def dump_create_terminal_task_fun(config):
    dump_create_terminal_task_fun_signature(config)
    sys.stdout.write("\n{\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("\tint blocks_"+config["dim_names"][dim]+" = N_"+config["dim_names"][dim]+" / block_size_"+config["dim_names"][dim]+";\n")

    sys.stdout.write("\tint blocks = 1")
    for dim in range(config["num_dims"]):
        sys.stdout.write("*blocks_"+config["dim_names"][dim]);
    sys.stdout.write(";\n")

    sys.stdout.write("\tint id = numiters*blocks")

    for dim in range(config["num_dims"]):
        sys.stdout.write(" + id_"+config["dim_names"][dim]);
        for dim_other in range(dim+1, config["num_dims"]):
            sys.stdout.write("*blocks_"+config["dim_names"][dim_other])
    sys.stdout.write(";\n")

    sys.stdout.write("\tint token[1];\n")

    sz = "1"
    for dim in range(config["num_dims"]):
        sz = sz + "*block_size_"+config["dim_names"][dim]

    sys.stdout.write("\tint center_size = "+sz+";\n")
    sys.stdout.write("\tdouble center_in[center_size];\n")

    for dim in range(config["num_dims"]):
        sz = "1"

        for dim_other in range(config["num_dims"]):
            if dim_other != dim:
                sz = sz + "*block_size_"+config["dim_names"][dim_other]

        sys.stdout.write("\tint "+config["dimref_names"][dim][0]+"_in_size = "+sz+";\n")
        sys.stdout.write("\tint "+config["dimref_names"][dim][1]+"_in_size = "+sz+";\n")
        sys.stdout.write("\tdouble "+config["dimref_names"][dim][0]+"_in["+config["dimref_names"][dim][0]+"_in_size];\n")
        sys.stdout.write("\tdouble "+config["dimref_names"][dim][1]+"_in["+config["dimref_names"][dim][0]+"_in_size];\n")

    for config_nr in range(4**config["num_dims"]):
        config["dim_configs"] = []

        for dim in range(config["num_dims"]):
            config["dim_configs"].append((config_nr / 4**dim) % 4)

        sys.stdout.write("\n\tif(1")
        for dim in range(config["num_dims"]):
            if(config["dim_configs"][dim] == seidel_positions.first):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" == 0 && blocks_"+config["dim_names"][dim]+" > 1")
            elif(config["dim_configs"][dim] == seidel_positions.mid):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" > 0 && id_"+config["dim_names"][dim]+" < blocks_"+config["dim_names"][dim]+"-1")
            elif(config["dim_configs"][dim] == seidel_positions.last):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" == blocks_"+config["dim_names"][dim]+"-1 && blocks_"+config["dim_names"][dim]+" > 1")
            elif(config["dim_configs"][dim] == seidel_positions.span):
                sys.stdout.write(" && blocks_"+config["dim_names"][dim]+" == 1")
        sys.stdout.write(") {\n")
        dump_terminal_task(config, "\t\t")
        sys.stdout.write("\t}\n")

    sys.stdout.write("}\n")

def dump_create_init_followup_task_fun_signature(config):
    sys.stdout.write("void create_init_followup_task(double* matrix, int numiters")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int id_"+config["dim_names"][dim])

    sys.stdout.write(")")

def dump_create_init_followup_task_fun(config):
    dump_create_init_followup_task_fun_signature(config)
    sys.stdout.write("\n{\n")

    sys.stdout.write("\tif(numiters > 1)\n")
    sys.stdout.write("\t\tcreate_next_iteration_task(matrix, numiters, 1")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim])
    sys.stdout.write(");\n\n")

    sys.stdout.write("\tif(numiters == 1)\n")
    sys.stdout.write("\t\tcreate_terminal_task(matrix, numiters")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim])
    sys.stdout.write(");\n")

    sys.stdout.write("}\n\n")

def dump_next_iteration_task(config, pref):
    if config["debug_printf"]:
        sys.stdout.write(pref+"printf(\"Creating task for (")
        for dim in range(config["num_dims"]):
            sys.stdout.write("%d ");
        sys.stdout.write(") it = %d, id = %d");

        for dim in range(config["num_dims"]):
            if config["dim_configs"][dim] != seidel_positions.first and config["dim_configs"][dim] != seidel_positions.span:
                sys.stdout.write(", id_"+config["dimref_names"][dim][0]+" = %d")

            if config["dim_configs"][dim] != seidel_positions.last and config["dim_configs"][dim] != seidel_positions.span:
                sys.stdout.write(", id_"+config["dimref_names"][dim][1]+" = %d")

        sys.stdout.write("\\n\"");

        for dim in range(config["num_dims"]):
            sys.stdout.write(", id_"+config["dim_names"][dim]);

        sys.stdout.write(", it, id")

        for dim in range(config["num_dims"]):
            if config["dim_configs"][dim] != seidel_positions.first and config["dim_configs"][dim] != seidel_positions.span:
                sys.stdout.write(", id_"+config["dimref_names"][dim][0])

            if config["dim_configs"][dim] != seidel_positions.last and config["dim_configs"][dim] != seidel_positions.span:
                sys.stdout.write(", id_"+config["dimref_names"][dim][1])

        sys.stdout.write(");\n");

    sys.stdout.write(pref+"#pragma omp task \\\n")

    num_clauses = 0
    sys.stdout.write(pref+"\tinout_reuse(")
    sys.stdout.write("scenter_ref[id_center] >> center[center_size] >> scenter_ref[id]")

    for dim in range(config["num_dims"]):
        if config["dim_configs"][dim] != seidel_positions.first and config["dim_configs"][dim] != seidel_positions.span:
            sys.stdout.write(", \\\n"+pref+"\t\t")
            sys.stdout.write("s"+config["dimref_names"][dim][1]+"_ref[id_"+config["dimref_names"][dim][0]+"] >> "+config["dimref_names"][dim][0]+"["+config["dimref_names"][dim][0]+"_size] >> s"+config["dimref_names"][dim][0]+"_ref[id]")
            num_clauses = num_clauses + 1

        if config["dim_configs"][dim] != seidel_positions.last and config["dim_configs"][dim] != seidel_positions.span:
            sys.stdout.write(", \\\n"+pref+"\t\t")
            sys.stdout.write("s"+config["dimref_names"][dim][0]+"_ref[id_"+config["dimref_names"][dim][1]+"] >> "+config["dimref_names"][dim][1]+"["+config["dimref_names"][dim][1]+"_size] >> s"+config["dimref_names"][dim][1]+"_ref[id]")
            num_clauses = num_clauses + 1

    sys.stdout.write(")\n")

    sys.stdout.write(pref+"{\n")

    if config["debug_printf"]:
        sys.stdout.write(pref+"\tprintf(\"Executing task for (")
        for dim in range(config["num_dims"]):
            sys.stdout.write("%d ");
        sys.stdout.write(") it = %d\\n\"");
        for dim in range(config["num_dims"]):
                sys.stdout.write(", id_"+config["dim_names"][dim]);
        sys.stdout.write(", it);\n");

    sys.stdout.write(pref+"\tseidel_%dd_df_in_place("%config["num_dims"])

    for dim in range(config["num_dims"]):
        if dim != 0:
            sys.stdout.write(", ")
        sys.stdout.write("block_size_"+config["dim_names"][dim])

    sys.stdout.write(", center")

    for dim in range(config["num_dims"]):
        if config["dim_configs"][dim] != seidel_positions.first and config["dim_configs"][dim] != seidel_positions.span:
            sys.stdout.write(", "+config["dimref_names"][dim][0])
        else:
            sys.stdout.write(", NULL")

        if config["dim_configs"][dim] != seidel_positions.last and config["dim_configs"][dim] != seidel_positions.span:
            sys.stdout.write(", "+config["dimref_names"][dim][1])
        else:
            sys.stdout.write(", NULL")

    sys.stdout.write(");\n");
    sys.stdout.write(pref+"\tcreate_followup_task(matrix, numiters, it")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim])

    sys.stdout.write(");\n")

    sys.stdout.write(pref+"}\n")

def dump_create_next_iteration_task_fun_signature(config):
    sys.stdout.write("void create_next_iteration_task(double* matrix, int numiters, int it")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int N_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int block_size_"+config["dim_names"][dim])

    for dim in range(config["num_dims"]):
        sys.stdout.write(", int id_"+config["dim_names"][dim])

    sys.stdout.write(")")

def dump_create_next_iteration_task_fun(config):
    dump_create_next_iteration_task_fun_signature(config)
    sys.stdout.write("\n{\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("\tint blocks_"+config["dim_names"][dim]+" = N_"+config["dim_names"][dim]+" / block_size_"+config["dim_names"][dim]+";\n")

    sys.stdout.write("\tint blocks = 1")
    for dim in range(config["num_dims"]):
        sys.stdout.write("*blocks_"+config["dim_names"][dim]);
    sys.stdout.write(";\n")

    sys.stdout.write("\tint id_center = it*blocks + 0")

    for dim in range(config["num_dims"]):
        sys.stdout.write(" + id_"+config["dim_names"][dim]);
        for dim_other in range(dim+1, config["num_dims"]):
            sys.stdout.write("*blocks_"+config["dim_names"][dim_other])
    sys.stdout.write(";\n")

    sys.stdout.write("\tint id = (it+1)*blocks + 0")

    for dim in range(config["num_dims"]):
        sys.stdout.write(" + id_"+config["dim_names"][dim]);
        for dim_other in range(dim+1, config["num_dims"]):
            sys.stdout.write("*blocks_"+config["dim_names"][dim_other])
    sys.stdout.write(";\n")

    for dim in range(config["num_dims"]):
        for direction in range(2):
            if direction == 0:
                itexpr = "(it+1)"
            else:
                itexpr = "it"

            sys.stdout.write("\tint id_"+config["dimref_names"][dim][direction]+" = "+itexpr+"*blocks + 0")

            for dim_other in range(config["num_dims"]):
                if dim_other == dim:
                    if direction == 0:
                        sys.stdout.write(" + (id_"+config["dim_names"][dim_other]+"-1)");
                    else:
                        sys.stdout.write(" + (id_"+config["dim_names"][dim_other]+"+1)");
                else:
                    sys.stdout.write(" + id_"+config["dim_names"][dim_other]);

                for dim_other_t in range(dim_other+1, config["num_dims"]):
                    sys.stdout.write("*blocks_"+config["dim_names"][dim_other_t])

            sys.stdout.write(";\n")

    sz = "1"
    for dim in range(config["num_dims"]):
        sz = sz + "*block_size_"+config["dim_names"][dim]

    sys.stdout.write("\tint center_size = "+sz+";\n")
    sys.stdout.write("\tdouble center[center_size];\n")

    for dim in range(config["num_dims"]):
        sz = "1"

        for dim_other in range(config["num_dims"]):
            if dim_other != dim:
                sz = sz + "*block_size_"+config["dim_names"][dim_other]

        sys.stdout.write("\tint "+config["dimref_names"][dim][0]+"_size = "+sz+";\n")
        sys.stdout.write("\tint "+config["dimref_names"][dim][1]+"_size = "+sz+";\n")
        sys.stdout.write("\tdouble "+config["dimref_names"][dim][0]+"["+config["dimref_names"][dim][0]+"_size];\n")
        sys.stdout.write("\tdouble "+config["dimref_names"][dim][1]+"["+config["dimref_names"][dim][0]+"_size];\n")

    for config_nr in range(4**config["num_dims"]):
        config["dim_configs"] = []

        for dim in range(config["num_dims"]):
            config["dim_configs"].append((config_nr / 4**dim) % 4)

        sys.stdout.write("\n\tif(1")
        for dim in range(config["num_dims"]):
            if(config["dim_configs"][dim] == seidel_positions.first):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" == 0 && blocks_"+config["dim_names"][dim]+" > 1")
            elif(config["dim_configs"][dim] == seidel_positions.mid):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" > 0 && id_"+config["dim_names"][dim]+" < blocks_"+config["dim_names"][dim]+"-1")
            elif(config["dim_configs"][dim] == seidel_positions.last):
                sys.stdout.write(" && id_"+config["dim_names"][dim]+" == blocks_"+config["dim_names"][dim]+"-1 && blocks_"+config["dim_names"][dim]+" > 1")
            elif(config["dim_configs"][dim] == seidel_positions.span):
                sys.stdout.write(" && blocks_"+config["dim_names"][dim]+" == 1")
        sys.stdout.write(") {\n")
        dump_next_iteration_task(config, "\t\t")
        sys.stdout.write("\t}\n")

    sys.stdout.write("}\n")

def dump_seidel_fun_signature(config):
    sys.stdout.write("void seidel_%dd_df_in_place("%config["num_dims"])

    for dim in range(config["num_dims"]):
        if dim != 0:
            sys.stdout.write(", ")
        sys.stdout.write("int block_size_"+config["dim_names"][dim])

    sys.stdout.write(", double* center")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", double* "+config["dimref_names"][dim][0])
        sys.stdout.write(", double* "+config["dimref_names"][dim][1])

    sys.stdout.write(")");

def dump_seidel_fun_loopnest(config, indent, mode, bounds):
    for d, bound in zip(config["dim_names"], bounds):
        sys.stdout.write(indent+"for(int "+d+" = "+bound[0]+"; "+d+" < "+bound[1]+"; "+d+"++) {\n")
        indent = indent+"\t"

    index_center_expr = "0"
    for dim in range(config["num_dims"]):
        index_center_expr += " + "+config["dim_names"][dim]+""
        for dim_other in range(dim+1, config["num_dims"]):
            index_center_expr += "*block_size_"+config["dim_names"][dim_other]

    if mode != "main":
        sys.stdout.write(indent+"int index_center = "+index_center_expr+";\n")

        for dim in range(config["num_dims"]):
            for direction in range(0, 2):
                sys.stdout.write(indent+"int index_"+config["dimref_names"][dim][direction]+"_center = 0")
                for dim_other in range(config["num_dims"]):
                    if dim_other == dim:
                        if direction == 0:
                            sys.stdout.write(" + ("+config["dim_names"][dim_other]+"-1)")
                        else:
                            sys.stdout.write(" + ("+config["dim_names"][dim_other]+"+1)")
                    else:
                        sys.stdout.write(" + "+config["dim_names"][dim_other]+"")

                    for dim_other_t in range(dim_other+1, config["num_dims"]):
                        sys.stdout.write("*block_size_"+config["dim_names"][dim_other_t])
                sys.stdout.write(";\n")

        sys.stdout.write("\n")

    if mode != "main":
        for dim in range(config["num_dims"]):
            for direction in range(0, 2):
                sys.stdout.write(indent+"int index_"+config["dimref_names"][dim][direction]+" = 0")
                for dim_other in range(config["num_dims"]):
                    if dim_other != dim:
                        sys.stdout.write(" + "+config["dim_names"][dim_other]+"")

                        for dim_other_t in range(dim_other+1, config["num_dims"]):
                            if dim_other_t != dim:
                                sys.stdout.write("*block_size_"+config["dim_names"][dim_other_t])
                sys.stdout.write(";\n")

        sys.stdout.write("\n")

    if mode == "main":
        sys.stdout.write(indent+"center["+index_center_expr+"] = (center["+index_center_expr+"]")
        for dim in range(config["num_dims"]):
            for direction in range(0, 2):
                sys.stdout.write(" +\n\t"+indent+"center[0")
                for dim_other in range(config["num_dims"]):
                    if dim_other == dim:
                        if direction == 0:
                            sys.stdout.write(" + ("+config["dim_names"][dim_other]+"-1)")
                        else:
                            sys.stdout.write(" + ("+config["dim_names"][dim_other]+"+1)")
                    else:
                        sys.stdout.write(" + "+config["dim_names"][dim_other]+"")

                    for dim_other_t in range(dim_other+1, config["num_dims"]):
                        sys.stdout.write("*block_size_"+config["dim_names"][dim_other_t])
                sys.stdout.write("]")
        sys.stdout.write(") / "+str(2*config["num_dims"]+1)+".0;\n")
    else:
        sys.stdout.write(indent+"double center_val = center[index_center];\n")

        for dim in range(config["num_dims"]):
            for direction in range(0, 2):
                sys.stdout.write(indent+"double "+config["dimref_names"][dim][direction]+"_val = ")
                if direction == 0:
                    sys.stdout.write("("+config["dim_names"][dim]+" == 0) ? ("+config["dimref_names"][dim][direction]+" ? "+config["dimref_names"][dim][direction]+"[index_"+config["dimref_names"][dim][direction]+"] : 0.0) : center[index_"+config["dimref_names"][dim][direction]+"_center]")
                else:
                    sys.stdout.write("("+config["dim_names"][dim]+" == block_size_"+config["dim_names"][dim]+"-1) ? ("+config["dimref_names"][dim][direction]+" ? "+config["dimref_names"][dim][direction]+"[index_"+config["dimref_names"][dim][direction]+"] : 0.0) : center[index_"+config["dimref_names"][dim][direction]+"_center]")
                sys.stdout.write(";\n");

        sys.stdout.write("\n")

        sys.stdout.write(indent+"center[index_center] = (center_val")
        for dim in range(config["num_dims"]):
            for direction in range(0, 2):
                sys.stdout.write("+"+config["dimref_names"][dim][direction]+"_val")
        sys.stdout.write(") / "+str(2*config["num_dims"]+1)+".0;\n")

    if mode != "main":
        for dim in range(config["num_dims"]):
            sys.stdout.write("\n"+indent+"if("+config["dim_names"][dim]+" == 0 && "+config["dimref_names"][dim][0]+")\n")
            sys.stdout.write(indent+"\t"+config["dimref_names"][dim][0]+"[index_"+config["dimref_names"][dim][0]+"] = center[index_center];\n")

            sys.stdout.write("\n"+indent+"if("+config["dim_names"][dim]+" == block_size_"+config["dim_names"][dim]+"-1 && "+config["dimref_names"][dim][1]+")\n")
            sys.stdout.write(indent+"\t"+config["dimref_names"][dim][1]+"[index_"+config["dimref_names"][dim][1]+"] = center[index_center];\n")

    for dim in range(config["num_dims"]):
        indent = indent[:len(indent)-1]
        sys.stdout.write(indent+"}\n");

    sys.stdout.write("\n")

def dump_seidel_fun(config):
    dump_seidel_fun_signature(config)
    sys.stdout.write("\n{\n");

    indent = "\t"

    for mode in ["intro", "main", "outro" ]:
        if mode == "intro":
            sys.stdout.write(indent+"/* Intro: "+("-".join(config["dim_names"]))+" corner */\n");
            bounds = map(lambda x: ["0", "1"], config["dim_names"])
            dump_seidel_fun_loopnest(config, indent, mode, bounds)

            for nzerodims in range(config["num_dims"]-1, 0, -1):
                for comb in seidel_common.partition_left_right(config["dim_names"], nzerodims):
                    zerodims = comb[0]
                    freedims = comb[1]

                    sys.stdout.write(indent+"/* Intro: "+("-".join(freedims))+" "+seidel_common.geom_name(ilen(freedims))+" */\n");
                    bounds = map(lambda x: x in zerodims and ["0", "1"] or ["1", "block_size_"+x], config["dim_names"])
                    dump_seidel_fun_loopnest(config, indent, mode, bounds)
        elif mode == "main":
            sys.stdout.write(indent+"/* Main part */\n");
            bounds = map(lambda x: ["1", "block_size_"+x+"-1"], config["dim_names"])
            dump_seidel_fun_loopnest(config, indent, mode, bounds)
        elif mode == "outro":
            for nzerodims in range(1, config["num_dims"]):
                for comb in seidel_common.partition_left_right(config["dim_names"], nzerodims):
                    zerodims = comb[0]
                    freedims = comb[1]

                    sys.stdout.write(indent+"/* Outro: "+("-".join(freedims))+" "+seidel_common.geom_name(ilen(freedims))+" */\n");
                    bounds = map(lambda x: x in zerodims and ["block_size_"+x+"-1", "block_size_"+x] or ["1", "block_size_"+x+"-1"], config["dim_names"])
                    dump_seidel_fun_loopnest(config, indent, mode, bounds)

            sys.stdout.write(indent+"/* Intro: "+("-".join(config["dim_names"]))+" corner */\n");
            bounds = map(lambda x: ["block_size_"+x+"-1", "block_size_"+x], config["dim_names"])
            dump_seidel_fun_loopnest(config, indent, mode, bounds)

    sys.stdout.write("}\n");

def dump_main_fun(config):
    sys.stdout.write("int main(int argc, char** argv)\n")
    sys.stdout.write("{\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	int N_"+config["dim_names"][dim]+" = -1;\n")

    sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	int block_size_"+config["dim_names"][dim]+" = -1;\n")

    sys.stdout.write("\n")

    sys.stdout.write("	int numiters = -1;\n")
    sys.stdout.write("\n")
    sys.stdout.write("	struct timeval start;\n")
    sys.stdout.write("	struct timeval end;\n")
    sys.stdout.write("\n")
    sys.stdout.write("	int option;\n")
    sys.stdout.write("	FILE* res_file = NULL;\n")
    sys.stdout.write("\n")
    sys.stdout.write("	/* Parse options */\n")
    sys.stdout.write("	while ((option = getopt(argc, argv, \"n:m:s:b:r:o:h\")) != -1)\n")
    sys.stdout.write("	{\n")
    sys.stdout.write("		switch(option)\n")
    sys.stdout.write("		{\n")
    sys.stdout.write("			case 'n':\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				if(optarg[0] == '"+config["dim_names"][dim]+"')\n")
        sys.stdout.write("					N_"+config["dim_names"][dim]+" = atoi(optarg+1);\n")

    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 's':\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				if(optarg[0] == '"+config["dim_names"][dim]+"')\n")
        sys.stdout.write("					N_"+config["dim_names"][dim]+" = 1 << atoi(optarg+1);\n")

    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 'b':\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				if(optarg[0] == '"+config["dim_names"][dim]+"')\n")
        sys.stdout.write("					block_size_"+config["dim_names"][dim]+" = 1 << atoi (optarg+1);\n")

    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 'm':\n")
    for dim in range(config["num_dims"]):
        sys.stdout.write("				if(optarg[0] == '"+config["dim_names"][dim]+"')\n")
        sys.stdout.write("					block_size_"+config["dim_names"][dim]+" = atoi(optarg+1);\n")

    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 'r':\n")
    sys.stdout.write("				numiters = atoi (optarg);\n")
    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 'o':\n")
    sys.stdout.write("				res_file = fopen(optarg, \"w\");\n")
    sys.stdout.write("				break;\n")
    sys.stdout.write("			case 'h':\n")
    sys.stdout.write("				printf(\"Usage: %s [option]...\\n\\n\"\n")
    sys.stdout.write("				       \"Options:\\n\"\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				       \"  -n "+config["dim_names"][dim]+"<size>                   Number of elements in "+config["dim_names"][dim]+"-direction of the matrix\\n\"\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				       \"  -s "+config["dim_names"][dim]+"<power>                  Set number of elements in "+config["dim_names"][dim]+"-direction of the matrix to 1 << <power>\\n\"\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				       \"  -m "+config["dim_names"][dim]+"<size>                   Number of elements in "+config["dim_names"][dim]+"-direction of a block\\n\"\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("				       \"  -b "+config["dim_names"][dim]+"<block size power>       Set the block size in "+config["dim_names"][dim]+"-direction to 1 << <block size power>\\n\"\n")

    sys.stdout.write("				       \"  -r <iterations>              Number of iterations\\n\"\n")
    sys.stdout.write("				       \"  -o <output file>             Write data to output file\\n\",\n")
    sys.stdout.write("				       argv[0]);\n")
    sys.stdout.write("				exit(0);\n")
    sys.stdout.write("				break;\n")
    sys.stdout.write("			case '?':\n")
    sys.stdout.write("				fprintf(stderr, \"Run %s -h for usage.\\n\", argv[0]);\n")
    sys.stdout.write("				exit(1);\n")
    sys.stdout.write("				break;\n")
    sys.stdout.write("		}\n")
    sys.stdout.write("	}\n")
    sys.stdout.write("\n")
    sys.stdout.write("	if(optind != argc) {\n")
    sys.stdout.write("		fprintf(stderr, \"Too many arguments. Run %s -h for usage.\\n\", argv[0]);\n")
    sys.stdout.write("		exit(1);\n")
    sys.stdout.write("	}\n")
    sys.stdout.write("\n")

    sys.stdout.write("	if(numiters == -1) {\n")
    sys.stdout.write("		fprintf(stderr, \"Please set the size of iterations (using the -r switch).\\n\");\n")
    sys.stdout.write("		exit(1);\n")
    sys.stdout.write("	}\n")
    sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	if(N_"+config["dim_names"][dim]+" == -1) {\n")
        sys.stdout.write("		fprintf(stderr, \"Please set the size of the matrix in "+config["dim_names"][dim]+"-direction (using the -n or -s switch).\\n\");\n")
        sys.stdout.write("		exit(1);\n")
        sys.stdout.write("	}\n")
        sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	if(block_size_"+config["dim_names"][dim]+" == -1) {\n")
        sys.stdout.write("		fprintf(stderr, \"Please set the block size of the matrix in "+config["dim_names"][dim]+"-direction (using the -m or -b switch).\\n\");\n")
        sys.stdout.write("		exit(1);\n")
        sys.stdout.write("	}\n")
        sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	if(N_"+config["dim_names"][dim]+" % block_size_"+config["dim_names"][dim]+" != 0) {\n")
        sys.stdout.write("		fprintf(stderr, \"Block size in "+config["dim_names"][dim]+"-direction (%d) does not divide size of the matrix in "+config["dim_names"][dim]+"-direction (%d).\\n\", block_size_"+config["dim_names"][dim]+", N_"+config["dim_names"][dim]+");\n")
        sys.stdout.write("		exit(1);\n")
        sys.stdout.write("	}\n")
        sys.stdout.write("\n")

    sys.stdout.write("	size_t matrix_size = sizeof(double)")
    for dim in range(config["num_dims"]):
        sys.stdout.write("*N_"+config["dim_names"][dim])
    sys.stdout.write(";\n")

    sys.stdout.write("	double* matrix = malloc_interleaved(matrix_size);\n")
    sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	int blocks_"+config["dim_names"][dim]+" = N_"+config["dim_names"][dim]+" / block_size_"+config["dim_names"][dim]+";\n")

    sys.stdout.write("\n")

    sys.stdout.write("	int blocks = 1")
    for dim in range(config["num_dims"]):
        sys.stdout.write(" * blocks_"+config["dim_names"][dim])
    sys.stdout.write(";\n")

    sys.stdout.write("\n")

    sys.stdout.write("	int sdfbarrier[2] __attribute__((stream));\n")
    sys.stdout.write("	sdfbarrier_ref = malloc(2*sizeof (void *));\n")
    sys.stdout.write("	memcpy (sdfbarrier_ref, sdfbarrier, 2*sizeof (void *));\n")
    sys.stdout.write("\n")

    sys.stdout.write("	double scenter[(numiters+2)*blocks] __attribute__((stream));\n")
    sys.stdout.write("	scenter_ref = malloc((numiters+2)*blocks * sizeof (void *));\n")
    sys.stdout.write("	memcpy (scenter_ref, scenter, (numiters+2)*blocks * sizeof (void *));\n")
    sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        for direction in range(0, 2):
            sys.stdout.write("	double s"+config["dimref_names"][dim][direction]+"[(numiters+2)*blocks] __attribute__((stream));\n")
            sys.stdout.write("	s"+config["dimref_names"][dim][direction]+"_ref = malloc((numiters+2)*blocks * sizeof (void *));\n")
            sys.stdout.write("	memcpy (s"+config["dimref_names"][dim][direction]+"_ref, s"+config["dimref_names"][dim][direction]+", (numiters+2)*blocks * sizeof (void *));\n")
            sys.stdout.write("\n")

    indent = ""
    for dim in range(config["num_dims"]):
        indent = indent + "\t"
        sys.stdout.write(indent+"for(int "+config["dim_names"][dim]+" = 0; "+config["dim_names"][dim]+" < N_"+config["dim_names"][dim]+"; "+config["dim_names"][dim]+"++) {\n")

    indent = indent + "\t"

    sys.stdout.write(indent + "size_t pos = 0")

    for dim in range(config["num_dims"]):
        sys.stdout.write(" + "+config["dim_names"][dim])
        for dim_other in range(dim+1, config["num_dims"]):
            sys.stdout.write("*N_"+config["dim_names"][dim_other])
    sys.stdout.write(";\n\n")

    sys.stdout.write(indent + "matrix[pos] = 0.0;\n\n")
    num = 0
    for init_pos in config["init_positions"]:
        if num == 0:
            sys.stdout.write(indent + "if(1")
        else:
            sys.stdout.write(indent + "else if(1")

        for idx in range(config["num_dims"]):
            sys.stdout.write(" && "+config["dim_names"][idx] + " == "+init_pos["pos"][idx])
        sys.stdout.write(")\n")
        sys.stdout.write(indent + "\tmatrix[pos] = "+init_pos["val"]+";\n")
        num = 1

    for dim in range(config["num_dims"]):
        indent = indent[:len(indent)-1]
        sys.stdout.write(indent+"}\n");

    sys.stdout.write("\n")
    sys.stdout.write("	gettimeofday(&start, NULL);\n")
    sys.stdout.write("	openstream_start_hardware_counters();\n")
    sys.stdout.write("\n")

    for dim in range(config["num_dims"]):
        sys.stdout.write("	int tasks_per_block_"+config["dim_names"][dim]+" = int_min(blocks_"+config["dim_names"][dim]+", 4);\n")
    sys.stdout.write("\n")

    indent = ""
    for dim in range(config["num_dims"]):
        indent = indent + "\t"
        sys.stdout.write(indent+"for(int oid_"+config["dim_names"][dim]+" = 0; oid_"+config["dim_names"][dim]+" < blocks_"+config["dim_names"][dim]+"; oid_"+config["dim_names"][dim]+" += tasks_per_block_"+config["dim_names"][dim]+") {\n")

    indent = indent + "\t"

    sys.stdout.write(indent+"#pragma omp task\n")
    sys.stdout.write(indent+"{\n")
    indent = indent + "\t"

    for dim in range(config["num_dims"]):
        sys.stdout.write(indent+"for(int id_"+config["dim_names"][dim]+" = oid_"+config["dim_names"][dim]+"; id_"+config["dim_names"][dim]+" < oid_"+config["dim_names"][dim]+" + tasks_per_block_"+config["dim_names"][dim]+"; id_"+config["dim_names"][dim]+"++) {\n")
        indent = indent + "\t"

    sys.stdout.write(indent+"create_initial_task(matrix, numiters")

    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim]);

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim]);

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim]);

    sys.stdout.write(");\n")

    sys.stdout.write(indent+"create_next_iteration_task(matrix, numiters, 0")
    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim]);

    for dim in range(config["num_dims"]):
        sys.stdout.write(", block_size_"+config["dim_names"][dim]);

    for dim in range(config["num_dims"]):
        sys.stdout.write(", id_"+config["dim_names"][dim]);

    sys.stdout.write(");\n")

    for dim in range(config["num_dims"]):
        indent = indent[:len(indent)-1]
        sys.stdout.write(indent+"}\n")

    indent = indent[:len(indent)-1]
    sys.stdout.write(indent+"}\n")

    for dim in range(config["num_dims"]):
        indent = indent[:len(indent)-1]
        sys.stdout.write(indent+"}\n");

    sys.stdout.write("\n")

    sys.stdout.write("	/* Wait for all the tasks to finish */\n")
    sys.stdout.write("	int dfbarrier_tokens[blocks];\n")
    sys.stdout.write("	#pragma omp task input(sdfbarrier_ref[0] >> dfbarrier_tokens[blocks])\n")
    sys.stdout.write("	{\n")
    if config["debug_printf"]:
        sys.stdout.write("		printf(\"FINISH\\n\");\n")
    sys.stdout.write("	}\n")
    sys.stdout.write("\n")
    sys.stdout.write("	#pragma omp taskwait\n")
    sys.stdout.write("\n")
    sys.stdout.write("	openstream_pause_hardware_counters();\n")
    sys.stdout.write("	gettimeofday(&end, NULL);\n")
    sys.stdout.write("\n")
    sys.stdout.write("	printf(\"%.5f\\n\", tdiff(&end, &start));\n")
    sys.stdout.write("\n")

    sys.stdout.write("	if(res_file) {\n")
    sys.stdout.write("	\tdump_matrix_%dd(matrix, res_file"%config["num_dims"])
    for dim in range(config["num_dims"]):
        sys.stdout.write(", N_"+config["dim_names"][dim])
    sys.stdout.write(");\n")
    sys.stdout.write("	\tfclose(res_file);\n")
    sys.stdout.write("	}\n\n")

    sys.stdout.write("	free(matrix);\n")
    sys.stdout.write("	free(scenter_ref);\n")
    sys.stdout.write("	free(sdfbarrier_ref);\n")

    for dim in range(config["num_dims"]):
        for direction in range(0, 2):
            sys.stdout.write("	free(s"+config["dimref_names"][dim][direction]+"_ref);\n")

    sys.stdout.write("\n")
    sys.stdout.write("	return 0;\n")
    sys.stdout.write("}\n")
    sys.stdout.write("\n")

def dump_file(config):
    if config["bodyfuncs_only"]:
        seidel_par_common.dump_bodyfuncs_global_defs(config)

    if not config["bodyfuncs_only"]:
        seidel_par_common.dump_global_defs(config)
        sys.stdout.write("\n");

    dump_seidel_fun_signature(config)
    sys.stdout.write(";\n");

    seidel_df_common.dump_init_fun_signature(config)
    sys.stdout.write(";\n");

    seidel_df_common.dump_finish_fun_signature(config)
    sys.stdout.write(";\n");

    if not config["bodyfuncs_only"]:
        dump_create_init_followup_task_fun_signature(config)
        sys.stdout.write(";\n");

        seidel_df_common.dump_create_followup_task_fun_signature(config)
        sys.stdout.write(";\n");

        seidel_df_common.dump_create_initial_task_fun_signature(config)
        sys.stdout.write(";\n");

        dump_create_next_iteration_task_fun_signature(config)
        sys.stdout.write(";\n");

        dump_create_terminal_task_fun_signature(config)
        sys.stdout.write(";\n");

    seidel_par_common.dump_dump_matrix_fun_signature(config)
    sys.stdout.write(";\n\n");

    if not config["openstream_only"]:
        seidel_par_common.dump_dump_matrix_fun(config)
        sys.stdout.write("\n")

        dump_seidel_fun(config)
        sys.stdout.write("\n")

        seidel_df_common.dump_init_fun(config)
        sys.stdout.write("\n")

        seidel_df_common.dump_finish_fun(config)
        sys.stdout.write("\n")

    if not config["bodyfuncs_only"]:
        dump_create_terminal_task_fun(config)
        sys.stdout.write("\n")

        dump_create_init_followup_task_fun(config)
        sys.stdout.write("\n")

        seidel_df_common.dump_create_followup_task_fun(config)
        sys.stdout.write("\n")

        seidel_df_common.dump_create_initial_task_fun(config)
        sys.stdout.write("\n")

        dump_create_next_iteration_task_fun(config)
        sys.stdout.write("\n")

        dump_main_fun(config)
        sys.stdout.write("\n")
