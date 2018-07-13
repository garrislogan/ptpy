#!/usr/bin/env python3

import subprocess,sys,configparser

def pt_startup_wait(proc):
    """
    Wait for the PT process proc to complete initialization 
    
    Return PT state information 
    """
    pt_state = {"methods": []} 
    
    for m in proc.stdout:
        fs = m.decode().strip().split(" ")
 
        if fs[0].endswith("ERROR"):
            raise RuntimeError("Pluggable transport: " + m.decode().strip()) 

        elif fs[0] == "CMETHOD":
            ip,port = fs[3].split(":")

            pt_state["methods"].append({"transport": fs[1],
                                        "proto": fs[2],
                                        "addr": (ip,int(port))})

        elif fs[0] == "CMETHODS" and fs[1] == "DONE":
            pt_state["mode"] = "client"
            break       
 
        elif fs[0] == "SMETHOD":
            ip,port = fs[2].split(":")

            method = {"transport": fs[1],
                      "addr": (ip,int(port))}

            try:
                method["args"] = fs[3][5:]
            except IndexError:
                pass

            pt_state["methods"].append(method)

        elif fs[0] == "SMETHODS" and fs[1] == "DONE":
            pt_state["mode"] = "server"
            break

    return pt_state

def start_pt(conf):
    """
    Start the PT according to the options from the PT config section 
    """
    env = {}
    env["TOR_PT_MANAGED_TRANSPORT_VER"] = conf["transport_version"]
    env["TOR_PT_STATE_LOCATION"] = conf["state_dir"]
    env["TOR_PT_EXIT_ON_STDIN_CLOSE"] = "0" 
   
    if conf["type"] == "client":
        env["TOR_PT_CLIENT_TRANSPORTS"] = conf["transports"] 

    elif conf["type"] == "server":
        env["TOR_PT_SERVER_TRANSPORTS"] = conf["transports"]
        env["TOR_PT_SERVER_BINDADDR"] = conf["bindaddr"] 
    
        if "orport" in conf:
            env["TOR_PT_ORPORT"] = conf["orport"]

        if "extorport" in conf:
            env["TOR_PT_EXTORPORT"] = conf["extorport"]

    pt_proc = subprocess.Popen(conf["exec"].split(" "),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            env=env)

    print("Started obfs4proxy with PID",pt_proc.pid)

    pt_state = pt_startup_wait(pt_proc)   

    return pt_proc,pt_state

def start_ovpn(conf,pt_state):
    # all OpenVPN options and configuration except the SOCKS5 proxy
    # should be configured using a regular OpenVPN config file

    proc_cmd = [conf["exec"],
                "--config {}".format(conf["config"])]
    
    if pt_state["mode"] == "client":
        # find first available SOCKS5 proxy provided by pluggable transport
        try:
            s5p = next( (m for m in pt_state["methods"] if m["proto"] == "socks5") )
        except StopIteration:
            raise RuntimeError("No suitable SOCKS5 proxy available to OpenVPN")
       
        # OpenVPN command line option to use the SOCKS5 proxy provided by PT
        proc_cmd.append("--socks-proxy {} {} {}".format(s5p["addr"][0],
                                                        s5p["addr"][1],
                                                        conf["socks_auth"]))

    ovpn_proc = subprocess.Popen(proc_cmd)

    print("Started OpenVPN with PID",ovpn_proc.pid)

    return ovpn_proc

if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    # start pluggable transport
    pt_proc, pt_state = start_pt(config["PT"])

    # start OpenVPN
    ovpn_proc = start_ovpn(config["OpenVPN"],pt_state)   
 
    while ovpn_proc.poll() == None or pt_proc.poll() == None:
        pass

    ovpn_proc.terminate()
    while ovpn_proc.poll() == None:
        pass

    pt_proc.terminate()
    while pt_proc.poll() == None:
        pass    
