#!/usr/bin/env python3

import json,subprocess,sys

def pt_startup_wait(proc):
    """
    Wait for the PT process proc to complete initialization 
    
    Return PT state information 
    """
    pt_state = {"methods": []} 
    
    for m in stdout.decode():
        fs = m.split(" ")
            
        if fs[0].endswith("ERROR"):
            raise RuntimeError("Pluggable transport: " + m) 

        elif fs[0] == "CMETHOD":
            ip,port = fs[3].split(":")

            pt_state["methods"].append({"transport": fs[1],
                                        "proto": fs[2],
                                        "addr": (ip,int(port))})

        elif fs[0] == "CMETHODS" and fields[1] == "DONE":
            pt_state["mode"] = "client"
            break       
 
        elif fs[0] == "SMETHOD":
            ip,port = fs[2].split(":")

            method["transport"] = fs[1]
            method["addr"] = (ip,int(port)) 

            try:
                method["args"] = fs[3][5:]
            except IndexError:
                pass

            pt_state["methods"].append(method)

        elif fs[0] == "SMETHODS" and fields[1] == "DONE":
            pt_state["mode"] = "server"
            break

    return pt_state

def start_pt(pt_env_fname):
    """
    Start the PT using the environment specified in the pt_env_filename file
    """
    with open(pt_env_fname) as f:
        pt_env = json.loads(f.read()) 

    pt_proc = subprocess.Popen(["/usr/bin/obfs4proxy","-enableLogging","-logLevel=DEBUG"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            env=pt_env)

    print("Started obfs4proxy with PID",pt_proc.pid)

    pt_state = pt_startup_wait(pt_proc)   

    return pt_proc,pt_state
 
if __name__ == "__main__":

    # config file names
    pt_env_fname = sys.argv[1]
    ovpn_conf_fname = sys.argv[2]
    ovpn_auth_fname = sys.argv[3]

    # start pluggable transport
    pt_proc, pt_state = start_pt(pt_env_fname)
 
    # start OpenVPN
    
    # all OpenVPN options and configuration except the SOCKS5 proxy
    # should be configured using a regular OpenVPN config file
    confarg = "--config {}".format(ovpn_conf_name)
    
    if pt_state["mode"] == "client":
        # find first available SOCKS5 proxy provided by pluggable transport
        try:
            s5p = next( (m for m in pt_state["methods"] if m["proto"] == "socks5") )
        except StopIteration:
            raise RuntimeError("No suitable SOCKS5 proxy available to OpenVPN")
       
        # OpenVPN command line option to use the SOCKS5 proxy provided by PT
        socksarg = "--socks-proxy {} {} {}".format(s5p["addr"][0],
                                                   s5p["addr"][1],
                                                   ovpn_auth_fname)

        ovpn_proc = subprocess.Popen(["/usr/sbin/openvpn",socksarg,confarg])

    elif pt_state["mode"] == "server": 
        print(pt_state["methods"]
        ovpn_proc = subprocess.Popen(["/usr/sbin/openvpn",confarg])

    print("Started OpenVPN with PID",ovpn_proc.pid)

    while ovpn_proc.poll() == None or pt_proc.poll() == None:
        pass

    ovpn_proc.terminate()
    while ovpn_proc.poll() == None:
        pass

    pt_proc.terminate()
    while pt_proc.poll() == None:
        pass    
