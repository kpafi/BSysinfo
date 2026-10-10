# BSysInfo

Ein Klon von `top` für Linux in Python, entstanden als Aufgabe im
Betriebssysteme-Praktikum. Das Programm liest alle Daten direkt aus `/proc`
und braucht keine externen Bibliotheken.

## Aufruf

```bash
python3 BSysInfo.py        # Prozesstabelle (wie -a)
python3 BSysInfo.py -t     # Prozessbaum
```


## Anzeigen

- Laufzeit, Anzahl der Tasks, CPU-, Speicher- und Swap-Auslastung
- Je Prozess: PID, Benutzer, Name, Priorität, Zustand, Elternprozess, Threads,
  CPU- und Speicheranteil, sortiert nach CPU
- Mit `-t` den Prozessbaum ab PID 1

Gelesen werden `/proc/uptime`, `/proc/loadavg`, `/proc/stat`, `/proc/meminfo`
sowie `stat` und `status` in den Prozessordnern. Die CPU-Auslastung entsteht
aus zwei Messungen im Abstand von einer Sekunde.


## Entstehung

Das Auslesen und Auswerten der `/proc`-Dateien habe ich selbst programmiert.
Die Formatierung der Ausgabe ist größtenteils mit KI-Unterstützung entstanden.
