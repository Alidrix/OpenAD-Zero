#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess
CHECKS = {
 'nmap':['nmap','--version'], 'nxc':['nxc','--version'], 'nuclei':['nuclei','-version'], 'enum4linux-ng':['enum4linux-ng','-h'],
 'kerbrute':['kerbrute','-h'], 'GetNPUsers.py':['GetNPUsers.py','-h'], 'GetUserSPNs.py':['GetUserSPNs.py','-h'], 'lookupsid.py':['lookupsid.py','-h'], 'smbclient.py':['smbclient.py','-h'],
 'gMSADumper.py':['gMSADumper.py','-h'], 'DonPAPI':['DonPAPI','-h'], 'coercer':['coercer','-h'], 'bloodyAD':['bloodyAD','-h'], 'responder':['responder','-h'], 'msfconsole':['msfconsole','-v']}

def main():
 out={}
 for name, argv in CHECKS.items():
  if not shutil.which(argv[0]): out[name]={'available':False,'reason':f'{argv[0]} not installed'}; continue
  try:
   cp=subprocess.run(argv,shell=False,capture_output=True,text=True,timeout=15)
   out[name]={'available':True,'version':((cp.stdout or cp.stderr).splitlines() or ['available'])[0]}
  except Exception as e: out[name]={'available':False,'reason':str(e)}
 print(json.dumps(out,indent=2))
if __name__=='__main__': main()
