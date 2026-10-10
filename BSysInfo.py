#!/usr/bin/env python3
import os
import time
import shutil
import pwd
import datetime
import argparse

def standartausgabe():

    global gesamtarbeitsspeicher
    os.chdir("/proc") #change das directory so dass ich nicht immer den ganzen pfad eingeben muss
    uptime = 0.0
    with open("uptime","r") as f:  #oeffne die datei und liest die erste zeile, der erste wert ist dann unsere uptime in sekunden
        line = f.read()
        uptime=line.split()[0]

    Anzahl_User = 0
    Anzahl_Tasks = 0
    Anzahl_running_tasks = 0
    Anzahl_stopped_tasks = 0
    Anzahl_sleeping_tasks = 0
    Anzahl_zombie_tasks = 0
    with open("loadavg","r") as f:
        line = f.readline()
        line = line.split()
        Anzahl_Tasks = line[3].split("/")[1]
        Anzahl_running_tasks = line[3].split("/")[0]   #das ist der output der detei 2.08 1.48 1.04 3/1030 35228 die / zahl hat vorne aktive tasks und hinten alle tasks


    alleordnernamen = []
    prozess_cpu_referenz = {} #in dem dict speichere ich mir die referenz werte (cpu ticks) damit ich nachher die richtige cpu percentage bekomme der Processe -> brauche dass um die cpu der einzelnen processe zu berechnen
    for folder in os.listdir('/proc'):   #hole mir alle zahlen ordnernahmen mit listdir und is digit
        if folder.isdigit():
            alleordnernamen.append(folder)

    for p in alleordnernamen:
        try:
            with open(f"/proc/{p}/stat", "r") as f_stat:
                parts = f_stat.readline().rsplit(")", 1)[1].split()
                # utime + stime (Index 11 und 12 nach dem Split)
                prozess_cpu_referenz[p] = int(parts[11]) + int(parts[12])
        except Exception:
            pass
    CPU_Auslastung = 0
    idel1 = 0
    idel2 = 0
    with open("stat","r") as f:            #die stat datei hat das als ausgabe  cpu  98503 7 15606 2081035 1202 0 166 0 0 0  der 4 wert ist der idel um also die auslastung zu bekommen muss ich die idel zweimal messen und die differenz ist meine cpu auslastung
        werte1 = f.readline().split()
        idle1 = int(werte1[4])  # Index 4 ist der echte Idle-Wert
        total1 = sum(int(x) for x in werte1[1:])  # Alle Ticks zusammenrechnen
    time.sleep(1) #wird verwendet um neue dBSaten zu haebn um system und einzelne process cpu daten zu berechnen (differenz neu-referenz)
    with open("stat","r") as f:
        werte2 = f.readline().split()
        idle2 = int(werte2[4])
        total2 = sum(int(x) for x in werte2[1:])

    total_diff = total2 - total1
    idle_diff = idle2 - idle1
    CPU_Auslastung = int(100 * (total_diff - idle_diff) / total_diff)


    Arbeitsspeicher_Auslastung = 0
    Swap_Speicher_frei = 0
    Swap_Speicher_verwendet = 0
    with open("meminfo","r") as f:                                           #mit cat meminfo kann man sihc die datei ausgeben lassen und um den benutzten arbeitspeicher zu verwenden muss man memTotal -memAvailabel machen
        speicherwerte = []
        for i in f:
            speicherwerte.append(i.split()[1])
        gesamtarbeitsspeicher = int(speicherwerte[0])
        Arbeitsspeicher_Auslastung = int(speicherwerte[0])-int(speicherwerte[2])
        Swap_Speicher_verwendet = int(speicherwerte[14])-int(speicherwerte[15])   # an stelle 15 und 16 sind die swap total und swap free
        Swap_Speicher_frei = int(speicherwerte[15])


    #jetzt gehe ich mir einer schleife durch alle process ordner durch um mir daten wie sleeping tasks etc. zu holen

    #die idee ist das ich verschachtelte listen nahme die hauptliste hat dannn alle listen der wichtigen ertde der ienzehlnen processe

    gesamtprocessdaten = []



    #!!!!!!!
    #aufbau der process daten liste [processid,task zustand,processname,process status,
    #ElternID,Prio,Anzahl_threads,User_ID,Arbeitsspeicher%,CPU%]
    #!!!!!!!


    #for folder in os.listdir('/proc'):   #hole mir alle zahlen ordnernahmen mit listdir und is digit
    #    if folder.isdigit():
    #        alleordnernamen.append(folder)
    #hab ich nach oben verschoben weil cih das schon fuer die cpu berechnung brauche

    for processe in alleordnernamen:  #gehe alle ordner durch
        os.chdir("/proc")
        daten = []
        processe = str(processe)
        daten.append(processe) #die processid
        try: #weil ich mit dateiein oeffnen spiele sollte ich das in einem try machen falls ein process verschwindet
            os.chdir(processe)
            statpath = f"task/{processe}/stat"
            with open(statpath,"r") as f:  #mache ich um den task status zu bekommen fuer die task werte davor zombie etc.
                daten.append(f.readline().split(")")[-1].split()[0])  #aufgab der stat datei 2 (kthreadd) S 0 0 0 0 -1 2129984 0 0 0 0 0 2 0 0 20 0 1 0 4 0 0 18446744073709551615 0 0 0 0 0 0 0 2147483647 0 0 0 0 0 13 0 0 0 0 0 0 0 0 0 0 0 0 0

            cpuwert1 = 0  #muss fuer die cpu prozent wiede rmit 1 sec unterschied messen
            cpuwert2 = 0
            with open("stat","r") as f:
                werte = f.readline()
                name_teil, werte= werte.rsplit(")", 1)
                processname = name_teil.split("(", 1)[1]
                werte = werte.split()
                daten.append(processname) #Process NAME
                daten.append(werte[0])  #Status
                daten.append(werte[1])  #ElternPID
                daten.append(werte[15]) #Prio
                daten.append(werte[17]) #Anzahl threads
                total_cpu_time = int(werte[11])+int(werte[12])
                ticks_pro_sek = os.sysconf(os.sysconf_names['SC_CLK_TCK']) #brauche ich fuer die cpu percentage berechnung unten

                cpu_prozent = 0.0 #variable deklarieren falls was nicht klappt sagt er dann halt 0.0
                # Prüfen, ob wir für diesen Prozess vor 1 Sekunde schon Daten gesammelt haben
                if processe in prozess_cpu_referenz:
                    differenz_ticks = total_cpu_time - prozess_cpu_referenz[processe]
                    # Da exakt 1 Sekunde vergangen ist, entspricht die Tick-Differenz dem Verbrauch in dieser Sekunde
                    einzelkern_prozent = (differenz_ticks / ticks_pro_sek) * 100
                    cpu_prozent = einzelkern_prozent / os.cpu_count() #davor hat er nur die prozent auslastung pro kern berechnet deshalb musste ich das hier anpassen

                daten.append(cpu_prozent)  # cpu prozent wird an die Liste angehängt




            with open("status","r") as f:
                werte = []
                for line in f:
                    werte.append(line.split())

                RAM = 0

                for x in range(len(werte)):
                    if werte[x][0]== "Uid:":   #die datei kann ishc aendern wenn ich zum beispiel einen kthread hab gibt es keinen VmRSS eintrag deshalb muss ich das so machen und kann nicht mit distanz addressierung die daten aus der datei holen
                        daten.append(werte[x][1])
                    if werte[x][0]== "VmRSS:":
                        RAM = int(werte[x][1])/gesamtarbeitsspeicher

                daten.append(RAM) #machne processe haben keine VmRSS daten deshalb muss ich das vorher definieren falls kein eintrag in dem file ist


            # hier kuemmere ich mich um die zombie sleeping tasks

            if daten[1] in ['S', 'D']:
                Anzahl_sleeping_tasks += 1

            elif daten[1] == 'T':
                Anzahl_stopped_tasks += 1

            elif daten[1] == 'Z':
                Anzahl_zombie_tasks += 1

            gesamtprocessdaten.append(daten)
            os.chdir("..")

        except Exception as e:
            print(e)
            pass



    #hier kommen noch die anzahl user
    terminal_users = [f for f in os.listdir('/dev/pts') if f.isdigit()]
    Anzahl_User = len(terminal_users)


    gesamtprocessdaten.sort(key=lambda x: x[7], reverse=True) #sortiert die listen nach der cpu auslastung (groesste auslastung steht jetzt am anfang )

    #print("----------------------OS_DATEN---------------------------")
    #print("uptime: " +uptime)
    #print("Anzahl_User: "+ str(Anzahl_User))
    #print("Anzahl_Tasks: " + str(Anzahl_Tasks))
    #print("Anzahl_running_tasks: " + str(Anzahl_running_tasks))
    #print("Anzahl_stopped_tasks: " + str(Anzahl_stopped_tasks))
    #print("Anzahl_sleeping_tasks: " + str(Anzahl_sleeping_tasks))
    #print("Anzahl_zombie_tasks: " + str(Anzahl_zombie_tasks))
    #print("CPU_Auslastung: " + str(CPU_Auslastung))
    #print("Arbeitsspeicher_Auslastung: " + str(Arbeitsspeicher_Auslastung))
    #print("Swap_Speicher_frei: " + str(Swap_Speicher_frei))
    #print("Swap_Speicher_verwendet: " + str(Swap_Speicher_verwendet))


    #for x in gesamtprocessdaten:
    #    print(x)


    #-----------------------------------hier fängt die ausgabe an-----------------------------------#(wurde mit hilfe von ki beim formatieren gebaut)

    print("\033[H\033[2J", end="",
          flush=True)  # wenn ich einen live tracker machen will koennte ich hiermit das terminal immer leeren um dann neu darafu zu printen
    os.system('clear')
    terminal_columns, terminal_lines = shutil.get_terminal_size() #DAMIT HOLE ICH MIR DIE TERMINAL GROESSE



    header_lines = 8  #die hoehe von dem oberen ding dass soll ja auf jeden fall ausgegeben werden
    max_prozesse = max(1, terminal_lines - header_lines) #hier berechne ich wie viel ich auf meinem terminal dann ausgeben kann von den prozessen



    # 2. Werte für den Header aufbereiten
    now = datetime.datetime.now().strftime("%H:%M:%S")
    uptime_min = int(float(uptime) / 60)
    cpu_cores = os.cpu_count()


    # Hilfsfunktion für die [███░░░] Ladebalken                   #hab ich mir von ki schreiben lassen fuer cpu und memory
    def get_bar(percentage, width=40):
        filled = int((percentage / 100) * width)
        return '█' * filled + '░' * (width - filled)



    cpu_percent_display = min(100.0, max(0.0, float(CPU_Auslastung))) #ich formatiere die cpu auslastung schien (davor war einfach eine zu lange zahl z.b. 0.1512379857392)
    #max ist dann 100% und min ist 0.0 und
    # RAM und SWAP in MB umrechnen (/proc/meminfo liefert Kilobytes)
    total_mem_mb = gesamtarbeitsspeicher // 1024
    used_mem_mb = Arbeitsspeicher_Auslastung // 1024
    avail_mem_mb = total_mem_mb - used_mem_mb
    mem_percent_display = (used_mem_mb / total_mem_mb * 100) if total_mem_mb > 0 else 0.0

    total_swap_mb = (Swap_Speicher_frei + Swap_Speicher_verwendet) // 1024
    free_swap_mb = Swap_Speicher_frei // 1024
    used_swap_mb = Swap_Speicher_verwendet // 1024

    #Hier gebe ich das top sing aus
    print(f"● Betriebssysteme Praktikum   {now}   Läuft Seit {uptime_min}min   {Anzahl_User} User")
    print(
        f"Tasks: insgesamt: {Anzahl_Tasks}   {Anzahl_sleeping_tasks} Sleeping   {Anzahl_running_tasks} Running   {Anzahl_stopped_tasks} stopped   {Anzahl_zombie_tasks} zombies")
    print(f"CPU: {cpu_percent_display:5.2f}% [{get_bar(cpu_percent_display)}] {cpu_cores} Kerne")
    print(
        f"MEM: {mem_percent_display:5.2f}% [{get_bar(mem_percent_display)}] {avail_mem_mb}MB von {total_mem_mb}MB verfügbar")
    print(f"SWAP: {total_swap_mb:.1f}MB Total   {free_swap_mb:.1f}MB Frei   {used_swap_mb:.1f}MB genutzt")
    print()

    #Tabellenkopf ausgeben
    header = f"{'Pid':>8}|{'User':>8} |{'Prozessname':<15}|{'Prio':>4}|{'State':>5}|{'Parent':>8}|{'Thds':>4}|{'CPU':>5}|{'MEM':>5}"
    print(header)

    #Prozesse ausgeben (Limitiert auf max_prozesse durch Slicing)
    for process in gesamtprocessdaten[:max_prozesse]:
        pid = process[0]
        pname = str(process[2])[:15]  # Prozessname auf 15 Zeichen abeschnitten dass nichts schief gehen kann
        state = process[3]
        ppid = process[4]
        prio = process[5]
        thds = process[6]

        # --- HIER SIND DIE KORRIGIERTEN INDIZES ---
        cpu_p = process[7]  # CPU% wurde als 8. Element angehängt (Index 7)
        uid = process[8]  # User_ID (Uid) kam danach (Index 8)

        # RAM (VmRSS) kam als letztes in die Liste (Index 9)
        mem_val = process[9] if isinstance(process[9], (int, float)) else 0.0
        mem_p = mem_val * 100
        # ------------------------------------------

        # User-ID (UID) aus der status-Datei in einen echten Usernamen umwandeln
        try:
            uname = pwd.getpwuid(int(uid)).pw_name[:8]
        except Exception:
            uname = str(uid)[:8]  # Fallback auf die nackte ID, falls der User nicht existiert

        print(f"{pid:>8}|{uname:>8} |{pname:<15}|{prio:>4}|{state:>5}|{ppid:>8}|{thds:>4}|{cpu_p:>4.1f}%|{mem_p:>4.1f}%")


def print_tree(process_dict, pid, prefix="", is_last=True):
    #Zeichnet den Baum rekursiv mit den passenden Linien
    if pid not in process_dict:  #abbruchbedingung der rekursion
        return

    info = process_dict[pid]

    # Terminal-Breite mit shutil ermitteln
    term_width = shutil.get_terminal_size((80, 20)).columns

    # Aktuellen Prozess mit Linien zeichnen
    connector = "└── " if is_last else "├── "
    line = f"{prefix}{connector}{info['name']} ({pid})"

    # Abschneiden, falls die Zeile breiter als das Terminalfenster ist
    print(line[:term_width])

    # Prefix für die nächste Ebene (die Kinder) vorbereiten
    child_prefix = prefix + ("    " if is_last else "│   ") #wenn es das letzte kind ist macht er nichts sonst mach er einen weiteren strich bis er  fertig ist

    children = info['children']
    for i, child_pid in enumerate(children):  #der rekursive aufruf mit den children des oben gegebenen eltern trees
        child_is_last = (i == len(children) - 1)
        print_tree(process_dict, child_pid, child_prefix, child_is_last)

def processtree():
    os.chdir("/proc")  # change das directory so dass ich nicht immer den ganzen pfad eingeben muss

    alleordnernamen = []
    for folder in os.listdir('/proc'):  # hole mir alle zahlen ordnernahmen mit listdir und is digit
        if folder.isdigit():
            alleordnernamen.append(folder)

    gesamtprocessdaten = []
    #aufbau der inneren arrays [pid,name,elternid]

    for processe in alleordnernamen:  # gehe alle ordner durch
        os.chdir("/proc")
        daten = []
        processe = str(processe)
        daten.append(processe)  # die processid
        try:  # weil ich mit dateiein oeffnen spiele sollte ich das in einem try machen falls ein process verschwindet
            os.chdir(processe)
            with open("stat", "r") as f:
                werte = f.readline()
                name_teil, werte= werte.rsplit(")", 1)
                processname = name_teil.split("(", 1)[1]
                werte = werte.split()
                daten.append(processname)  # Process NAME
                try:
                    daten.append(werte[1])  # ElternPID
                except:
                    pass
            pathcildren = f"task/{processe}/children"
            try:
                with open(pathcildren, "r") as f:
                    werte = f.readline().split()
                    for x in werte:
                        daten.append(x)
            except:
                pass
            gesamtprocessdaten.append(daten)
            os.chdir("..")

        except Exception as e:
            print(e)
            pass

    gesamtprocessdaten = sorted(gesamtprocessdaten, key=lambda x: len(x), reverse=True) # sortiert die liste nach groesse die groesste steht ma anfang

    process_dict = {}

    # 1. Deine Liste in ein Dictionary umwandeln weil ich damit einfacher den aufruf mahcen kann
    for daten in gesamtprocessdaten:
        pid = daten[0]
        name = daten[1]
        ppid = daten[2] if len(daten) > 2 else None

        process_dict[pid] = {
            'name': name,
            'ppid': ppid,
            'children': []
        }


    # 2. Die Kinder ihren Eltern zuordnen (mithilfe der ElternPID)
    for pid, info in process_dict.items():
        ppid = info['ppid']
        if ppid in process_dict and ppid != pid:
            process_dict[ppid]['children'].append(pid)

    # 3. Den Baum ausgeben
    print("\n--- Prozessbaum ---")
    if '1' in process_dict:
        # Start bei init / systemd (PID 1)
        print(f"{process_dict['1']['name']} (1)")
        children = process_dict['1']['children']
        for i, child_pid in enumerate(children):
            is_last = (i == len(children) - 1)
            print_tree(process_dict, child_pid, "", is_last)
    else:
        print("Konnte PID 1 nicht finden. Gib alle Prozesse einzeln aus...")




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all", action="store_true", help="Shows standart output")
    parser.add_argument("-t", "--tree", action="store_true", help="Shows process tree")
    args = parser.parse_args()

    if not (args.all or args.tree):
        args.all = True

    if args.all:
        try:
            while True:

                standartausgabe()
                time.sleep(3)
        except KeyboardInterrupt:
            print("die ausgabe wurde beendet")
            pass
    if args.tree:
        try:
            while True:
                print("\033[H\033[2J\033[3J", end="", flush=True)
                processtree()
                time.sleep(3)
        except KeyboardInterrupt:
            print("die ausgabe wurde beendet")
            pass

main()
