#!/usr/bin/env python3

import json,subprocess,sys

with open(sys.argv[1]) as f:
    env_vars = json.loads(f.read())


proc = subprocess.Popen(["/usr/bin/obfs4proxy","-enableLogging","-logLevel=DEBUG"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        env=env_vars)

print(f"Started obfs4proxy with PID {proc.pid}")

try:
    for m in proc.stdout:
        print(m.decode())

    print(proc.returncode)

except KeyboardInterrupt:
    proc.terminate()
