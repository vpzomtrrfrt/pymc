import json, argparse, os.path, random, sys, subprocess, zipfile, os, shutil, shlex
parser = argparse.ArgumentParser()
parser.add_argument("version")
parser.add_argument("--mcdir", dest="mcdir", default=os.path.expanduser("~")+"/.minecraft")
parser.add_argument("--username", dest="username", default="Player"+str(random.randrange(1000)))
parser.add_argument("--game-directory", dest="gamedir")
parser.add_argument("--access-token", dest="token", default="no")
parser.add_argument("--uuid", dest="uuid")
parser.add_argument("--jvm-args", dest="jargs")
ns = parser.parse_args()
if ns.gamedir == None:
    ns.gamedir = ns.mcdir
platform = sys.platform
h = open(ns.mcdir+os.sep+"versions"+os.sep+ns.version+os.sep+ns.version+".json")
j = json.load(h)
h.close()
classpath = ""
nativesdir = ns.mcdir+os.sep+"versions"+os.sep+ns.version+os.sep+ns.version+"-natives-"+str(random.randrange(100000))
os.mkdir(nativesdir)
libraries = j["libraries"]
tmp = j
while "inheritsFrom" in tmp:
    inherit = tmp["inheritsFrom"]
    h = open(ns.mcdir+os.sep+"versions"+os.sep+inherit+os.sep+inherit+".json")
    tmp = json.load(h)
    for k in tmp:
        if not k in j:
            j[k] = tmp[k]
    libraries += tmp["libraries"]
    #classpath += ":"+ns.mcdir+"/versions/"+inherit+os.sep+inherit+".jar"
    h.close()
for l in libraries:
    action = True
    if "rules" in l:
        action = False
        for rule in l["rules"]:
            accept = True
            if "os" in rule and rule["os"]["name"] != platform:
                accept = False
            if accept:
                action = rule["action"]=="allow"
    if action:
        spl = l["name"].split(":")
        path = ns.mcdir+os.sep+"libraries"+os.sep+spl[0].replace(".", os.sep)+os.sep+spl[1]+os.sep+spl[2]+os.sep+spl[1]+"-"+spl[2]
        if "natives" in l:
            path += "-"+l["natives"][platform]
        path += ".jar"
        if os.path.exists(path):
            if "natives" in l:
                zp = zipfile.ZipFile(path)
                zp.extractall(nativesdir)
            else:
                if len(classpath) > 0:
                    classpath += ":"
                classpath += path
        else:
            print("Could not find "+l["name"])
            print(path)
            exit()
classpath += ":"+ns.mcdir+os.sep+"versions"+os.sep+ns.version+os.sep+ns.version+".jar"
args = ["java"]
if ns.jargs != None:
    args += shlex.split(ns.jargs)
args += ["-Djava.library.path="+nativesdir,"-cp", classpath, j["mainClass"]]
spl = j["minecraftArguments"][2:].split(" --")
srcargs = {
    "auth_player_name": ns.username,
    "auth_access_token": ns.token,
    "game_directory": ns.gamedir,
    "version_name": ns.version,
    "assets_root": ns.mcdir+os.sep+"assets",
    "assets_index_name": j["assetIndex"]["id"] if "assetIndex" in j else j["assets"],
    "version_type": j["type"],
    "user_type": "mojang"
}
if ns.uuid != None:
    srcargs["auth_uuid"] = ns.uuid
for s in spl:
    ss = s.split(" ")
    res = None
    if ss[1][:2] == "${" and ss[1][-1] == "}":
        tf = ss[1][2:-1]
        if tf in srcargs:
            res = srcargs[tf]
        else:
            print("Don't know what "+tf+" is")
    else:
        res = ss[1]
    if res != None:
        args.append("--"+ss[0])
        args.append(res)
print(" ".join(args))
subprocess.call(args)
shutil.rmtree(nativesdir)
