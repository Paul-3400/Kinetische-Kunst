#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gcode_wascher.py - Version 2
Saueubert G-code-Dateien (z. B. von svg2gcode) fuer den Walldraw-Polargraphen
und macht sie direkt einsatzfaehig ("1.nc" fuer die TF-Karte).

Autor: Paul Simmen mit Vibe (GLM-5-latest-short), 30.10.2026

WARUM DIESES SKRIPT?
Die Firmware WallDraw.ino versteht pro Zeile nur die Woerter X, Y und Z:
  - Z > 0   -> Stift heben (z. B. "G01 Z5")
  - Z <= 0  -> Stift senken (z. B. "G01 Z-1")
Alles andere wird ignoriert. Daraus ergeben sich die Reinigungsschritte:

  1. Kommentare (";...") entfernen - Walldraw liest blind X/Y/Z. Ein
     Kommentar, der zufaellig die Buchstaben X oder Y enthaelt ("layer"!),
     wuerde als Bewegung fehlgelesen.
  2. Zeilennummern (N123) und Pruefsummen (*45) entfernen - das ist ein
     Streaming-Protokoll fuer 3D-Drucker, das Walldraw nicht braucht.
  3. Vorschub (F300) entfernen - wird ohnehin ignoriert.
  4. Bereits vorhandene Stift-Z-Zeilen entfernen und SAUBER NEU aufbauen:
     vor jedem Eilgang (G0) den Stift heben, vor dem ersten Strich danach
     senken, am Ende heben. Das Skript ist damit "idempotent": eine schon
     gewaschene Datei darf erneut gewaschen werden - das Ergebnis bleibt
     korrekt.
  5. Standardmaessig: die Zeichnung um die Home-Position (0|0) zentrieren,
     damit sie mittig unter der Gondel erscheint (abschaltbar).

NEU IN VERSION 2 (30.10.2026)
  - Interaktiver Dialog: einfach starten (Thonny-Run oder Doppelklick), das
    Skript fragt nach allem, was es braucht - Kommandozeile ist optional.
  - Zentrieren ist jetzt Standard (abschaltbar mit --kein-zentrieren).
  - Warnung, falls G2/G3-Bogenzeilen im G-code sind (Walldraw kann keine
    Boegen; in svg2gcode "Circular interpolation" ausschalten).
  - Robust beim Einlesen (UTF-8, BOM-tolerant, Latin-1-Rueckfall) und mit
    klaren deutschen Fehlermeldungen.

BEDIENUNG
  Interaktiv (empfohlen in Thonny):   python gcode_wascher.py
  Mit Argumenten:                    python gcode_wascher.py eingabe.gcode 1.nc
  Ohne Zentrierung:                  python gcode_wascher.py eingabe.gcode 1.nc --kein-zentrieren

Die fertige Datei dann auf die FAT32-TF-Karte kopieren und loszeichnen.
Schritt-fuer-Schritt-Anleitung: ANLEITUNG-gcode-wascher.md (im selben Ordner).
"""

import argparse
import math
import re
import sys

VERSION = "2.0"

# --- regulaere Ausdruecke -----------------------------------------------------
ZEILENNUMMER = re.compile(r"^N\d+\s*")
PRUEFSUMME = re.compile(r"\*\d+")
KOMMENTAR = re.compile(r";.*$")
VORSCHUB = re.compile(r"\s+F\d*\.?\d*\s*$")
EILGANG = re.compile(r"^G0*0\b")      # G0, G00
STRICH = re.compile(r"^G0*1\b")       # G1, G01
BOGEN = re.compile(r"^G0*[23]\b")     # G2/G02, G3/G03
XY = re.compile(r"X(-?\d+\.?\d*)\s+Y(-?\d+\.?\d*)", re.IGNORECASE)
Z_WORT = re.compile(r"\bZ-?\d+\.?\d*", re.IGNORECASE)
MEHRFACH_LEERZEICHEN = re.compile(r"\s{2,}")

STIFT_HEBEN = "G01 Z5"
STIFT_SENKEN = "G01 Z-1"


def saeubern(zeile):
    """Schritt 1-3: entfernt Kommentar, Zeilennummer, Pruefsumme, Vorschub."""
    z = KOMMENTAR.sub("", zeile)
    z = ZEILENNUMMER.sub("", z)
    z = PRUEFSUMME.sub("", z)
    z = VORSCHUB.sub("", z).strip()
    return z


def bbox(zeilen):
    """Liefert (xmin, xmax, ymin, ymax) aller X/Y-Koordinaten."""
    xs, ys = [], []
    for z in zeilen:
        m = XY.search(z)
        if m:
            xs.append(float(m.group(1)))
            ys.append(float(m.group(2)))
    if not xs:
        sys.exit("Fehler: keine X/Y-Koordinaten gefunden - "
                  "ist das wirklich eine G-code-Datei?")
    return min(xs), max(xs), min(ys), max(ys)


def waschen(eingabe_text):
    """Schritt 1-4 (Bereinigung ohne Stift-Logik).

    Liefert (zeilenliste, bbox, weglaenge, bogen_zeilen, entfernte_z_zeilen).
    """
    roh = [z.strip() for z in eingabe_text.splitlines() if z.strip()]

    sauber = []
    bogen = 0
    entfernte_z = 0
    for zeile in roh:
        z = saeubern(zeile)
        if not z:
            continue
        u = z.upper()
        if BOGEN.match(u):
            bogen += 1
            sauber.append(z)          # durchreichen, aber spaeter warnen
            continue
        if XY.search(z) is None and Z_WORT.search(z):
            # reine Stift-Zeile (z. B. "G01 Z5") - wird neu aufgebaut
            entfernte_z += 1
            continue
        if XY.search(z) and Z_WORT.search(z):
            # Bewegung mit X/Y UND Z: Z-Wort entfernen, Stift wird neu geregelt
            z = MEHRFACH_LEERZEICHEN.sub(" ", Z_WORT.sub("", z)).strip()
        sauber.append(z)

    xmin, xmax, ymin, ymax = bbox(sauber)

    laenge = 0.0
    letzter = None
    for z in sauber:
        m = XY.search(z)
        if not m:
            continue
        p = (float(m.group(1)), float(m.group(2)))
        if letzter is not None:
            laenge += math.hypot(p[0] - letzter[0], p[1] - letzter[1])
        letzter = p

    return sauber, (xmin, xmax, ymin, ymax), laenge, bogen, entfernte_z


def zentrieren_und_stift(sauber, zentrieren):
    """Schritt 4-5: verschiebt X/Y auf die Bildmitte und baut die
    Stift-Befehle auf. Liefert (zeilenliste, striche)."""
    xmin, xmax, ymin, ymax = bbox(sauber)
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0

    def verschieben(z):
        if not zentrieren:
            return z
        return XY.sub(lambda m: "X%.3f Y%.3f" % (float(m.group(1)) - cx,
                                                float(m.group(2)) - cy),
                      z, count=1)

    ausgabe = []
    stift_oben = True          # Walldraw startet mit gehobenem Stift
    striche = 0
    for z in sauber:
        u = z.upper()
        if EILGANG.match(u):
            if not stift_oben:
                ausgabe.append(STIFT_HEBEN)
                stift_oben = True
            ausgabe.append(verschieben(z))
        elif STRICH.match(u):
            if stift_oben:
                ausgabe.append(STIFT_SENKEN)
                stift_oben = False
                striche += 1
            ausgabe.append(verschieben(z))
        else:
            ausgabe.append(verschieben(z))   # G21, G90, G2/G3 ...
    if not stift_oben:
        ausgabe.append(STIFT_HEBEN)
    return ausgabe, striche


def frage(text, vorschlag=""):
    """Stellt eine Frage im Dialog; leere Eingabe = Vorschlagswert."""
    if vorschlag:
        antwort = input("%s [%s]: " % (text, vorschlag)).strip()
        return antwort or vorschlag
    return input("%s: " % text).strip()


def datei_lesen(pfad):
    """Liest eine Textdatei, toleriert BOM und Latin-1-Kodierung."""
    try:
        with open(pfad, encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        print("Hinweis: Datei ist nicht UTF-8-kodiert - lese als Latin-1.")
        with open(pfad, encoding="latin-1") as f:
            return f.read()
    except FileNotFoundError:
        sys.exit("Fehler: Datei nicht gefunden: %s\n"
                 "Tipp: Datei ins Terminal-Fenster ziehen (fuegt den Pfad ein), "
                 "oder die G-code-Datei in denselben Ordner wie das Skript legen "
                 "und nur den Dateinamen eintippen." % pfad)


def main():
    parser = argparse.ArgumentParser(
        description="gcode_wascher v%s - saeubert G-code fuer den "
                    "Walldraw-Polargraphen. Start ohne Argumente = interaktiver Dialog."
                    % VERSION)
    parser.add_argument("eingabe", nargs="?", default=None,
                        help="G-code-Datei (leer lassen = Dialog)")
    parser.add_argument("ausgabe", nargs="?", default=None,
                        help="Zieldatei (leer lassen = Dialog)")
    parser.add_argument("--zentrieren", dest="zentrieren", action="store_true",
                        default=None,
                        help="Zeichnung um Home (0|0) zentrieren (Standard)")
    parser.add_argument("--kein-zentrieren", dest="zentrieren", action="store_false",
                        help="Zeichnung NICHT zentrieren (Koordinaten unverändert)")
    args = parser.parse_args()

    print("=" * 62)
    print(" gcode_wascher v%s - Reinigung fuer den Walldraw-Polargraphen" % VERSION)
    print("=" * 62)

    eingabe = args.eingabe
    ausgabe = args.ausgabe
    zentrieren = args.zentrieren

    if eingabe is None:
        eingabe = frage("Pfad zur G-code-Datei (z. B. schneemann.gcode)")
    if ausgabe is None:
        ausgabe = frage("Zieldatei", vorschlag="1.nc")
    if zentrieren is None:
        antwort = frage("Zeichnung um Home (0|0) zentrieren? (j/n)",
                        vorschlag="j").lower()
        zentrieren = antwort.startswith("j")

    text = datei_lesen(eingabe)
    sauber, (xmin, xmax, ymin, ymax), laenge, bogen, entfernte_z = waschen(text)
    zeilen, striche = zentrieren_und_stift(sauber, zentrieren)

    with open(ausgabe, "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")

    print()
    print("Fertig! Statistik:")
    print("  Eingabe       : %s" % eingabe)
    print("  Ausgabe       : %s (%d Zeilen)" % (ausgabe, len(zeilen)))
    print("  Striche       : %d (dazwischen faehrt der Stift hoch)" % striche)
    if entfernte_z:
        print("  Alte Z-Zeilen : %d entfernt und sauber neu aufgebaut" % entfernte_z)
    print("  Zentriert     : %s" % ("ja - Bildmitte liegt auf Home (0|0)"
                                    if zentrieren else "nein - Koordinaten unveraendert"))
    print("  Zeichnung     : %.0f x %.0f mm" % (xmax - xmin, ymax - ymin))
    print("  Weglaenge     : %.1f m" % (laenge / 1000.0))
    print("  Zeit ca.      : %.0f min (bei 25 mm/s; real eher mehr)"
          % (laenge / 25.0 / 60.0))
    if bogen:
        print()
        print("  WARNUNG: %d G2/G3-Bogenzeilen gefunden!" % bogen)
        print("  Walldraw kann keine Boegen zeichnen. In der svg2gcode-Web-UI")
        print("  die Option 'Circular interpolation' ausschalten und neu")
        print("  konvertieren.")
    print()
    print("Naechster Schritt: %s auf die FAT32-TF-Karte kopieren - "
          "loszeichnen!" % ausgabe)


if __name__ == "__main__":
    main()
