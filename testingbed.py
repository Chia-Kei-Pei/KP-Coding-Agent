import os, subprocess

# os.system("dir")
print(subprocess.run(["dir"], capture_output=True))