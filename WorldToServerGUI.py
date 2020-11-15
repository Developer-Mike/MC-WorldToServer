import requests, os, shutil, sys
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
from getpass import getuser

useSpigot = False
worldPath = "C:/Users/" + getuser() + "/AppData/Roaming/.minecraft/saves/TestWorld"
serverPath = "C:/Users/" + getuser() + "/Documents/WorldToServer/"
filedialog.Tk().withdraw()

def setUseSpigot():
    global useSpigot
    useSpigot = False if useSpigot else True

def selectWorldPath():
    global worldPath, worldLocationEntry
    worldPath = worldLocationEntry.get()
    path = filedialog.askdirectory(initialdir=worldPath, title="Select World")
    if (path != ""):
        worldPath = path
    worldLocationEntry.delete(0, tk.END)
    worldLocationEntry.insert(0, worldPath)

def selectServerPath():
    global serverPath, targetLocationEntry
    serverPath = targetLocationEntry.get()
    path = filedialog.askdirectory(initialdir=serverPath, title="Select Server Path")
    if (path != ""):
        serverPath = path + "/"
    targetLocationEntry.delete(0, tk.END)
    targetLocationEntry.insert(0, serverPath)

def compileWorld():
    global useSpigot, worldPath, serverPath, targetLocationEntry, worldLocationEntry
    serverPath = targetLocationEntry.get()
    if (serverPath[-1] != "/"):
        serverPath = serverPath + "/"
    worldPath = worldLocationEntry.get()

    print("Getting data version db...") 
    r = requests.get("https://minecraft.gamepedia.com/Data_version")
    versions = {}
    doc = BeautifulSoup(r.text, "html.parser")
    table = doc.find('table', {'class': 'wikitable sortable jquery-tablesorter'})
    tableBody = table.findChildren("tbody", recursive=False)[0]
    rows = tableBody.findChildren("tr", recursive=False)

    for row in rows:
        childrens = row.findChildren(recursive=True)
        try:
            versions[childrens[3].text] = childrens[0].text
        except:
            pass

    print("Getting world version...") #Version num (https://minecraft.gamepedia.com/Data_version) in stats/playerID.json in DataVersion
    playerUUID = os.listdir(worldPath + "/stats/")[0]
    content = open(worldPath + "/stats/" + playerUUID, "r").read()
    dataVersion = content.split("\"DataVersion\":")[1].replace("}", "")
    print("Version:", versions[dataVersion])

    print("Finding server jars...")
    jars = {}
    if useSpigot:
        r = requests.get("https://getbukkit.org/download/spigot")
    else:
        r = requests.get("https://getbukkit.org/download/vanilla")
    doc = BeautifulSoup(r.text, "html.parser")
    table = doc.find_all("div", {'class': 'row vdivide'})
    for row in table:
        jars[row.findChild("h2", recursive=True).text] = row.findChild("a", {'id': 'downloadr'}, recursive=True)["href"]

    print("Finding correct server jar...")
    try:
        url = jars[versions[dataVersion].split()[-1]]
    except:
        print("Failed. Select version manually.")

    os.makedirs(serverPath)

    print("Downloading server jar...") 
    r = requests.get(url, allow_redirects=True)
    doc = BeautifulSoup(r.text, "html.parser")
    download = doc.find("div", {'class': 'well'}).findChild("a")
    url = download["href"]

    r = requests.get(url, allow_redirects=True)
    open(serverPath + "server.jar", "wb").write(r.content)

    print("Accepting eula...")
    eula = open(serverPath + "eula.txt", "w")
    eula.write("eula=true")
    eula.close()

    print("Transfer overworld...")
    shutil.copytree(worldPath, serverPath + "world/")

    if (useSpigot):
        print("Transfer nether...")
        shutil.move(serverPath + "/world/DIM-1", serverPath + "world_nether/DIM-1/", copy_function=shutil.move)

        print("Transfer the end...")
        shutil.move(serverPath + "/world/DIM1", serverPath + "world_the_end/DIM/", copy_function=shutil.move)

    print("Creating run file...")
    open(serverPath + "Run.bat", "w").write("java -Xmx1024M -Xms1024M -jar server.jar nogui")

    print("Done!")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root = tk.Tk()
root.title("World 2 Server")
try:
    root.iconbitmap(resource_path("icon.ico"))
except:
    pass

targetFrame = tk.Frame(root)
targetLocationLabel = tk.Label(targetFrame, text="Server Output Location:")
targetLocationLabel.grid(row=0, column=0)
targetLocationEntry = tk.Entry(targetFrame, width=70)
targetLocationEntry.insert(0, serverPath)
targetLocationEntry.grid(row=1, column=0)
browseTargetLocation = tk.Button(targetFrame, text="...", command=selectServerPath)
browseTargetLocation.grid(row=1, column=1)

worldLocationLabel = tk.Label(targetFrame, text="World Folder Location:")
worldLocationLabel.grid(row=2, column=0)
worldLocationEntry = tk.Entry(targetFrame, width=70)
worldLocationEntry.insert(0, worldPath)
worldLocationEntry.grid(row=3, column=0)
browseWorldLocation = tk.Button(targetFrame, text="...", command=selectWorldPath) 
browseWorldLocation.grid(row=3, column=1)
targetFrame.pack()

useSpigotCheckButton = tk.Checkbutton(root, text="Use Spigot", command=setUseSpigot)
useSpigotCheckButton.pack()

compileButton = tk.Button(root, text="Compile", command=compileWorld)
compileButton.pack()

root.protocol("WM_DELETE_WINDOW", sys.exit)
root.mainloop()