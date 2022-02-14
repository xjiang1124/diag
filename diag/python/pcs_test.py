import subprocess

for i in range(1, 11):
    subprocess.call(["turn_on_uut.sh", str(i), "2"])
    subprocess.call(["mtptest", "-pcs", "-index="+str(i)])
