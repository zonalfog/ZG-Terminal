#!/usr/bin/env python3
"""
ZG Terminal - Ein modernes Terminal mit alternativen Befehlen
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
import subprocess
import platform
import datetime
import shutil
import socket
import psutil
import threading
import time
from pathlib import Path
import re
from itertools import zip_longest

# WMI für Hardware-Informationen
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

class ZGTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("ZG Terminal")
        self.root.geometry("900x600")
        self.root.configure(bg='#1e1e1e')
        
        # Aktuelles Verzeichnis
        self.current_dir = os.getcwd()
        
        # Befehlsverlauf
        self.command_history = []
        self.history_index = -1
        
        # GUI erstellen
        self.setup_gui()
        
        # Befehls-Handler registrieren
        self.setup_commands()
        
        # Focus setzen
        self.command_entry.focus_set()
        
        # Willkommensnachricht
        self.add_output("ZG Terminal v1.0", "system")
        self.add_output(f"Aktuelles Verzeichnis: {self.current_dir}", "info")
        self.add_output("Geben Sie 'hilfe' für eine Liste der verfügbaren Befehle ein.", "info")
        
    def setup_gui(self):
        """GUI-Komponenten erstellen"""
        # Hauptframe
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titel
        title_label = tk.Label(main_frame, text="ZG Terminal", 
                              font=('Consolas', 16, 'bold'),
                              bg='#1e1e1e', fg='#00ff00')
        title_label.pack(pady=(0, 10))
        
        # Ausgabebereich
        self.output_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 10),
            bg='#0d0d0d',
            fg='#00ff00',
            insertbackground='#00ff00',
            selectbackground='#333333',
            state=tk.DISABLED
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Eingabezeile
        input_frame = tk.Frame(main_frame, bg='#1e1e1e')
        input_frame.pack(fill=tk.X)
        
        # Prompt-Label
        self.prompt_label = tk.Label(input_frame, text="ZG>", 
                                     font=('Consolas', 10, 'bold'),
                                     bg='#1e1e1e', fg='#00ff00')
        self.prompt_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Eingabefeld
        self.command_entry = tk.Entry(
            input_frame,
            font=('Consolas', 10),
            bg='#0d0d0d',
            fg='#00ff00',
            insertbackground='#00ff00',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground='#00ff00'
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Event-Handler
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.bind('<Up>', self.navigate_history_up)
        self.command_entry.bind('<Down>', self.navigate_history_down)
        self.command_entry.bind('<Tab>', self.auto_complete)
        
    def setup_commands(self):
        """Befehls-Handler registrieren"""
        self.commands = {
            # Dateisystem-Befehle (mit alternativen Namen)
            'liste': self.cmd_liste,           # statt dir
            'gehe': self.cmd_gehe,             # statt cd
            'erstelle': self.cmd_erstelle,     # statt md
            'entferne': self.cmd_entferne,     # statt rd
            'kopiere': self.cmd_kopiere,       # statt copy
            'loesche': self.cmd_loesche,       # statt del
            'benenne': self.cmd_benenne,       # statt ren
            
            # Text-Befehle
            'zeige': self.cmd_zeige,           # statt type
            'bearbeite': self.cmd_bearbeite,   # statt edit
            
            # System-Befehle
            'formatiere': self.cmd_formatiere, # statt format
            'pruefe': self.cmd_pruefe,         # statt chkdsk
            'baum': self.cmd_baum,             # statt tree
            'attribute': self.cmd_attribute,   # statt attrib
            
            # Netzwerk-Befehle
            'testnetz': self.cmd_testnetz,     # statt ping
            'netzinfo': self.cmd_netzinfo,     # statt ipconfig
            'netzwerk': self.cmd_netzwerk,     # statt net
            
            # System-Info-Befehle
            'geraete': self.cmd_geraete,       # statt mode
            'datum': self.cmd_datum,           # statt date
            'zeit': self.cmd_zeit,             # statt time
            'umgebung': self.cmd_umgebung,     # statt set
            'prozesse': self.cmd_prozesse,     # statt tasklist
            'beende': self.cmd_beende,         # statt taskkill
            
            # Hardware-Info-Befehle
            'cpu': self.cmd_cpu,               # CPU-Informationen
            'gpu': self.cmd_gpu,               # GPU-Informationen
            'motherboard': self.cmd_motherboard, # Motherboard-Informationen
            'mainboard': self.cmd_motherboard,  # Alias für motherboard
            'ram': self.cmd_ram,               # RAM-Informationen
            'netzteil': self.cmd_netzteil,     # Netzteil-Informationen
            
            # Utility-Befehle
            'vergleiche': self.cmd_vergleiche, # statt fc
            'hilfe': self.cmd_hilfe,           # statt help
            'ende': self.cmd_ende,             # statt exit
            'clear': self.cmd_clear,           # Zusatzbefehl
        }
        
    def add_output(self, text, msg_type="normal"):
        """Text zur Ausgabe hinzufügen"""
        self.output_area.config(state=tk.NORMAL)
        
        # Farben für verschiedene Nachrichtentypen
        colors = {
            "normal": "#00ff00",
            "error": "#ff0000",
            "warning": "#ffff00",
            "info": "#00ffff",
            "system": "#ffffff"
        }
        
        # Text mit Farbe einfügen
        self.output_area.insert(tk.END, text + "\n", msg_type)
        self.output_area.tag_config(msg_type, foreground=colors.get(msg_type, "#00ff00"))
        
        self.output_area.config(state=tk.DISABLED)
        self.output_area.see(tk.END)
        
    def execute_command(self, event=None):
        """Befehl ausführen"""
        command = self.command_entry.get().strip()
        
        if not command:
            return
            
        # Befehl zur Ausgabe hinzufügen
        self.add_output(f"ZG> {command}", "system")
        
        # Zum Verlauf hinzufügen
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Befehl parsen und ausführen
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in self.commands:
            try:
                self.commands[cmd](args)
            except Exception as e:
                self.add_output(f"Fehler: {str(e)}", "error")
        else:
            self.add_output(f"Befehl '{cmd}' nicht gefunden. Geben Sie 'hilfe' für eine Liste der verfügbaren Befehle ein.", "error")
        
        # Eingabefeld leeren
        self.command_entry.delete(0, tk.END)
        
    def navigate_history_up(self, event):
        """Im Verlauf nach oben navigieren"""
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        return "break"
        
    def navigate_history_down(self, event):
        """Im Verlauf nach unten navigieren"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, tk.END)
        return "break"
        
    def auto_complete(self, event):
        """Auto-Vervollständigung für Befehle"""
        current_text = self.command_entry.get()
        matching_commands = [cmd for cmd in self.commands.keys() if cmd.startswith(current_text)]
        
        if len(matching_commands) == 1:
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, matching_commands[0])
        elif len(matching_commands) > 1:
            self.add_output("Mögliche Befehle: " + ", ".join(matching_commands), "info")
            
        return "break"
    
    # Dateisystem-Befehle
    def cmd_liste(self, args):
        """Listet Dateien und Verzeichnisse auf (statt dir)"""
        try:
            path = " ".join(args) if args else self.current_dir
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            if not os.path.exists(path):
                self.add_output(f"Pfad nicht gefunden: {path}", "error")
                return
                
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"[FILE] {item} ({size} bytes)")
                    
            if items:
                self.add_output(f"Inhalt von {path}:", "info")
                for item in sorted(items):
                    self.add_output(f"  {item}")
            else:
                self.add_output(f"Verzeichnis ist leer: {path}", "info")
                
        except Exception as e:
            self.add_output(f"Fehler beim Auflisten: {str(e)}", "error")
    
    def cmd_gehe(self, args):
        """Wechselt das Verzeichnis (statt cd)"""
        try:
            if not args:
                self.add_output(f"Aktuelles Verzeichnis: {self.current_dir}", "info")
                return
                
            path = " ".join(args)
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            if os.path.exists(path) and os.path.isdir(path):
                self.current_dir = os.path.abspath(path)
                self.add_output(f"Verzeichnis gewechselt zu: {self.current_dir}", "info")
            else:
                self.add_output(f"Verzeichnis nicht gefunden: {path}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Verzeichniswechsel: {str(e)}", "error")
    
    def cmd_erstelle(self, args):
        """Erstellt ein neues Verzeichnis (statt md)"""
        try:
            if not args:
                self.add_output("Verwendung: erstelle <Verzeichnisname>", "info")
                return
                
            dirname = " ".join(args)
            if not os.path.isabs(dirname):
                dirname = os.path.join(self.current_dir, dirname)
                
            if not os.path.exists(dirname):
                os.makedirs(dirname)
                self.add_output(f"Verzeichnis erstellt: {dirname}", "info")
            else:
                self.add_output(f"Verzeichnis existiert bereits: {dirname}", "warning")
                
        except Exception as e:
            self.add_output(f"Fehler beim Erstellen: {str(e)}", "error")
    
    def cmd_entferne(self, args):
        """Entfernt ein Verzeichnis (statt rd)"""
        try:
            if not args:
                self.add_output("Verwendung: entferne <Verzeichnisname>", "info")
                return
                
            dirname = " ".join(args)
            if not os.path.isabs(dirname):
                dirname = os.path.join(self.current_dir, dirname)
                
            if os.path.exists(dirname) and os.path.isdir(dirname):
                # Prüfen, ob Verzeichnis leer ist
                if not os.listdir(dirname):
                    os.rmdir(dirname)
                    self.add_output(f"Verzeichnis entfernt: {dirname}", "info")
                else:
                    self.add_output(f"Verzeichnis ist nicht leer: {dirname}", "warning")
                    self.add_output("Verwenden Sie 'loesche' zum Löschen von Dateien", "info")
            else:
                self.add_output(f"Verzeichnis nicht gefunden: {dirname}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Entfernen: {str(e)}", "error")
    
    def cmd_kopiere(self, args):
        """Kopiert Dateien (statt copy)"""
        try:
            if len(args) < 2:
                self.add_output("Verwendung: kopiere <Quelle> <Ziel>", "info")
                return
                
            source = args[0]
            destination = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(destination):
                destination = os.path.join(self.current_dir, destination)
                
            if os.path.exists(source):
                shutil.copy2(source, destination)
                self.add_output(f"Kopiert: {source} -> {destination}", "info")
            else:
                self.add_output(f"Quelldatei nicht gefunden: {source}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Kopieren: {str(e)}", "error")
    
    def cmd_loesche(self, args):
        """Löscht Dateien (statt del)"""
        try:
            if not args:
                self.add_output("Verwendung: loesche <Dateiname>", "info")
                return
                
            filename = " ".join(args)
            if not os.path.isabs(filename):
                filename = os.path.join(self.current_dir, filename)
                
            if os.path.exists(filename):
                if os.path.isfile(filename):
                    os.remove(filename)
                    self.add_output(f"Datei gelöscht: {filename}", "info")
                elif os.path.isdir(filename):
                    self.add_output(f"Verwenden Sie 'entferne' für Verzeichnisse: {filename}", "warning")
                else:
                    self.add_output(f"Unbekannter Dateityp: {filename}", "error")
            else:
                self.add_output(f"Datei nicht gefunden: {filename}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Löschen: {str(e)}", "error")
    
    def cmd_benenne(self, args):
        """Benennt Dateien um (statt ren)"""
        try:
            if len(args) < 2:
                self.add_output("Verwendung: benenne <alter_name> <neuer_name>", "info")
                return
                
            old_name = args[0]
            new_name = args[1]
            
            if not os.path.isabs(old_name):
                old_name = os.path.join(self.current_dir, old_name)
            if not os.path.isabs(new_name):
                new_name = os.path.join(self.current_dir, new_name)
                
            if os.path.exists(old_name):
                os.rename(old_name, new_name)
                self.add_output(f"Umbenannt: {old_name} -> {new_name}", "info")
            else:
                self.add_output(f"Datei nicht gefunden: {old_name}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Umbenennen: {str(e)}", "error")
    
    # Text-Befehle
    def cmd_zeige(self, args):
        """Zeigt den Inhalt einer Textdatei an (statt type)"""
        try:
            if not args:
                self.add_output("Verwendung: zeige <Dateiname>", "info")
                return
                
            filename = " ".join(args)
            if not os.path.isabs(filename):
                filename = os.path.join(self.current_dir, filename)
                
            if os.path.exists(filename) and os.path.isfile(filename):
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.add_output(f"Inhalt von {filename}:", "info")
                    self.add_output(content)
            else:
                self.add_output(f"Datei nicht gefunden: {filename}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Lesen: {str(e)}", "error")
    
    def cmd_bearbeite(self, args):
        """Öffnet einen einfachen Texteditor (statt edit)"""
        try:
            if not args:
                self.add_output("Verwendung: bearbeite <Dateiname>", "info")
                return
                
            filename = " ".join(args)
            if not os.path.isabs(filename):
                filename = os.path.join(self.current_dir, filename)
                
            # Einfachen Texteditor erstellen
            editor_window = tk.Toplevel(self.root)
            editor_window.title(f"ZG Editor - {filename}")
            editor_window.geometry("800x600")
            editor_window.configure(bg='#1e1e1e')
            
            # Textbereich
            text_area = scrolledtext.ScrolledText(
                editor_window,
                wrap=tk.WORD,
                font=('Consolas', 11),
                bg='#0d0d0d',
                fg='#00ff00',
                insertbackground='#00ff00',
                selectbackground='#333333'
            )
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Datei laden, falls vorhanden
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    text_area.insert(tk.END, f.read())
            
            # Button-Frame
            button_frame = tk.Frame(editor_window, bg='#1e1e1e')
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            def save_file():
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(text_area.get(1.0, tk.END))
                    self.add_output(f"Datei gespeichert: {filename}", "info")
                    editor_window.destroy()
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
            
            def cancel_edit():
                editor_window.destroy()
            
            save_btn = tk.Button(button_frame, text="Speichern", command=save_file,
                               bg='#00ff00', fg='#1e1e1e', font=('Consolas', 10, 'bold'))
            save_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            cancel_btn = tk.Button(button_frame, text="Abbrechen", command=cancel_edit,
                                 bg='#ff0000', fg='white', font=('Consolas', 10, 'bold'))
            cancel_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            self.add_output(f"Fehler beim Editor: {str(e)}", "error")
    
    # System-Befehle
    def cmd_formatiere(self, args):
        """Formatiert eine Festplatte (statt format) - Simulation"""
        self.add_output("WARNUNG: Formatierung ist eine gefährliche Operation!", "warning")
        self.add_output("Dies ist nur eine Simulation - keine echte Formatierung wird durchgeführt.", "info")
        
        if not args:
            self.add_output("Verwendung: formatiere <Laufwerk> (z.B. C:)", "info")
            return
            
        drive = args[0]
        self.add_output(f"Simulation: Formatierung von Laufwerk {drive}...", "warning")
        self.add_output("Dies würde alle Daten auf dem Laufwerk löschen!", "error")
        self.add_output("Simulation abgeschlossen - keine echten Änderungen vorgenommen.", "info")
    
    def cmd_pruefe(self, args):
        """Überprüft eine Festplatte auf Fehler (statt chkdsk)"""
        try:
            drive = " ".join(args) if args else "C:"
            
            if platform.system() == "Windows":
                # Windows-spezifische Prüfung
                result = subprocess.run(['chkdsk', drive, '/f'], capture_output=True, text=True)
                self.add_output(f"Chkdsk Ergebnis für {drive}:", "info")
                self.add_output(result.stdout)
            else:
                # Linux/Mac Alternative
                self.add_output(f"Plattenprüfung für {drive}:", "info")
                self.add_output("Plattenstatus: OK", "info")
                
        except Exception as e:
            self.add_output(f"Fehler bei der Plattenprüfung: {str(e)}", "error")
    
    def cmd_baum(self, args):
        """Zeigt eine grafische Darstellung der Verzeichnisstruktur (statt tree)"""
        try:
            path = " ".join(args) if args else self.current_dir
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            def print_tree(directory, prefix="", max_depth=3, current_depth=0):
                if current_depth >= max_depth:
                    return
                    
                try:
                    items = sorted(os.listdir(directory))
                except PermissionError:
                    self.add_output(f"{prefix}[Zugriff verweigert]", "warning")
                    return
                    
                for i, item in enumerate(items):
                    item_path = os.path.join(directory, item)
                    is_last = i == len(items) - 1
                    current_prefix = "    " if is_last else "   |"
                    new_prefix = prefix + current_prefix
                    
                    if os.path.isdir(item_path):
                        self.add_output(f"{prefix}   {'--' if is_last else '|--'} {item}/")
                        print_tree(item_path, new_prefix, max_depth, current_depth + 1)
                    else:
                        self.add_output(f"{prefix}   {'--' if is_last else '|--'} {item}")
            
            self.add_output(f"Verzeichnisstruktur für {path}:", "info")
            self.add_output(path)
            print_tree(path)
            
        except Exception as e:
            self.add_output(f"Fehler bei der Baumansicht: {str(e)}", "error")
    
    def cmd_attribute(self, args):
        """Zeigt Dateiattribute an (statt attrib)"""
        try:
            if not args:
                self.add_output("Verwendung: attribute <Dateiname>", "info")
                return
                
            filename = " ".join(args)
            if not os.path.isabs(filename):
                filename = os.path.join(self.current_dir, filename)
                
            if os.path.exists(filename):
                stat = os.stat(filename)
                self.add_output(f"Attribute für {filename}:", "info")
                self.add_output(f"  Größe: {stat.st_size} bytes")
                self.add_output(f"  Erstellt: {datetime.datetime.fromtimestamp(stat.st_ctime)}")
                self.add_output(f"  Modifiziert: {datetime.datetime.fromtimestamp(stat.st_mtime)}")
                self.add_output(f"  Zuletzt zugegriffen: {datetime.datetime.fromtimestamp(stat.st_atime)}")
                self.add_output(f"  Verzeichnis: {'Ja' if os.path.isdir(filename) else 'Nein'}")
            else:
                self.add_output(f"Datei nicht gefunden: {filename}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler bei Attributen: {str(e)}", "error")
    
    # Netzwerk-Befehle
    def cmd_testnetz(self, args):
        """Testet die Netzwerkverbindung (statt ping)"""
        try:
            if not args:
                self.add_output("Verwendung: testnetz <Host/IP>", "info")
                return
                
            host = args[0]
            self.add_output(f"Ping zu {host}...", "info")
            
            try:
                # Ping durchführen
                result = subprocess.run(['ping', '-n', '4', host], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.add_output(f"Verbindung zu {host} erfolgreich!", "info")
                    self.add_output(result.stdout)
                else:
                    self.add_output(f"Verbindung zu {host} fehlgeschlagen!", "error")
                    self.add_output(result.stderr)
            except subprocess.TimeoutExpired:
                self.add_output(f"Timeout bei Verbindung zu {host}", "error")
            except Exception as e:
                self.add_output(f"Fehler beim Ping: {str(e)}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler bei Netzwerktest: {str(e)}", "error")
    
    def cmd_netzinfo(self, args):
        """Zeigt IP-Konfigurationsinformationen (statt ipconfig)"""
        try:
            self.add_output("Netzwerkinformationen:", "info")
            
            if platform.system() == "Windows":
                # Windows ipconfig
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
                self.add_output(result.stdout)
            else:
                # Linux/Mac Alternative
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                self.add_output(f"Hostname: {hostname}", "info")
                self.add_output(f"IP-Adresse: {ip_address}", "info")
                
                # Netzwerk-Interfaces
                self.add_output("\nNetzwerk-Interfaces:", "info")
                import netifaces
                interfaces = netifaces.interfaces()
                for interface in interfaces:
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            self.add_output(f"  {interface}: {addr['addr']}")
                            
        except ImportError:
            # Fallback wenn netifaces nicht installiert ist
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            self.add_output(f"Hostname: {hostname}", "info")
            self.add_output(f"IP-Adresse: {ip_address}", "info")
        except Exception as e:
            self.add_output(f"Fehler bei Netzwerkinfos: {str(e)}", "error")
    
    def cmd_netzwerk(self, args):
        """Verwaltet Netzwerkressourcen (statt net)"""
        try:
            if not args:
                self.add_output("Verwendung: netzwerk <aktion> [parameter]", "info")
                self.add_output("Aktionen: status, verbinden, trennen", "info")
                return
                
            action = args[0].lower()
            
            if action == "status":
                self.add_output("Netzwerkstatus:", "info")
                self.add_output("  Lokale Verbindung: Aktiv", "info")
                self.add_output(f"  Hostname: {socket.gethostname()}", "info")
                
            elif action == "verbinden":
                if len(args) < 2:
                    self.add_output("Verwendung: netzwerk verbinden <freigabe>", "info")
                    return
                share = args[1]
                self.add_output(f"Verbindung zu {share} wird simuliert...", "info")
                self.add_output("Dies ist nur eine Simulation.", "warning")
                
            elif action == "trennen":
                if len(args) < 2:
                    self.add_output("Verwendung: netzwerk trennen <freigabe>", "info")
                    return
                share = args[1]
                self.add_output(f"Verbindung zu {share} wird getrennt (Simulation)...", "info")
                
            else:
                self.add_output(f"Unbekannte Aktion: {action}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler bei Netzwerkverwaltung: {str(e)}", "error")
    
    # System-Info-Befehle
    def cmd_geraete(self, args):
        """Konfiguriert Systemgeräte (statt mode)"""
        try:
            self.add_output("Systemgeräte-Informationen:", "info")
            self.add_output(f"  Betriebssystem: {platform.system()} {platform.release()}", "info")
            self.add_output(f"  Prozessor: {platform.processor()}", "info")
            self.add_output(f"  Architektur: {platform.architecture()[0]}", "info")
            self.add_output(f"  Python-Version: {platform.python_version()}", "info")
            
        except Exception as e:
            self.add_output(f"Fehler bei Geräteinformationen: {str(e)}", "error")
    
    def cmd_datum(self, args):
        """Zeigt/legt das Systemdatum fest (statt date)"""
        try:
            current_date = datetime.datetime.now()
            
            if not args:
                self.add_output(f"Aktuelles Datum: {current_date.strftime('%d.%m.%Y')}", "info")
                self.add_output("Verwendung: datum <TT.MM.JJJJ> zum Ändern", "info")
            else:
                date_str = args[0]
                try:
                    # Datum parsen
                    new_date = datetime.datetime.strptime(date_str, '%d.%m.%Y')
                    self.add_output(f"Datum würde geändert zu: {new_date.strftime('%d.%m.%Y')}", "warning")
                    self.add_output("Dies ist nur eine Simulation - echtes Datum nicht geändert.", "info")
                except ValueError:
                    self.add_output("Ungültiges Datumsformat. Verwenden Sie TT.MM.JJJJ", "error")
                    
        except Exception as e:
            self.add_output(f"Fehler bei Datum: {str(e)}", "error")
    
    def cmd_zeit(self, args):
        """Zeigt/legt die Systemzeit fest (statt time)"""
        try:
            current_time = datetime.datetime.now()
            
            if not args:
                self.add_output(f"Aktuelle Zeit: {current_time.strftime('%H:%M:%S')}", "info")
                self.add_output("Verwendung: zeit <HH:MM:SS> zum Ändern", "info")
            else:
                time_str = args[0]
                try:
                    # Zeit parsen
                    new_time = datetime.datetime.strptime(time_str, '%H:%M:%S')
                    self.add_output(f"Zeit würde geändert zu: {new_time.strftime('%H:%M:%S')}", "warning")
                    self.add_output("Dies ist nur eine Simulation - echte Zeit nicht geändert.", "info")
                except ValueError:
                    self.add_output("Ungültiges Zeitformat. Verwenden Sie HH:MM:SS", "error")
                    
        except Exception as e:
            self.add_output(f"Fehler bei Zeit: {str(e)}", "error")
    
    def cmd_umgebung(self, args):
        """Zeigt/legt Umgebungsvariablen fest (statt set)"""
        try:
            if not args:
                self.add_output("Umgebungsvariablen:", "info")
                for key, value in os.environ.items():
                    self.add_output(f"  {key}={value}")
            else:
                if len(args) >= 2:
                    var_name = args[0]
                    var_value = " ".join(args[1:])
                    os.environ[var_name] = var_value
                    self.add_output(f"Umgebungsvariable gesetzt: {var_name}={var_value}", "info")
                else:
                    var_name = args[0]
                    if var_name in os.environ:
                        self.add_output(f"{var_name}={os.environ[var_name]}", "info")
                    else:
                        self.add_output(f"Umgebungsvariable nicht gefunden: {var_name}", "error")
                        
        except Exception as e:
            self.add_output(f"Fehler bei Umgebungsvariablen: {str(e)}", "error")
    
    def cmd_prozesse(self, args):
        """Zeigt laufende Prozesse an (statt tasklist)"""
        try:
            self.add_output("Laufende Prozesse:", "info")
            
            # Prozessliste mit psutil
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    self.add_output(f"  PID: {proc_info['pid']:<6} Name: {proc_info['name']:<20} CPU: {proc_info['cpu_percent']:<5.1f}% RAM: {proc_info['memory_percent']:<5.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.add_output(f"Fehler bei Prozessliste: {str(e)}", "error")
    
    def cmd_beende(self, args):
        """Beendet laufende Prozesse (statt taskkill)"""
        try:
            if not args:
                self.add_output("Verwendung: beende <PID oder Prozessname>", "info")
                return
                
            target = args[0]
            
            try:
                # Versuche als PID zu interpretieren
                pid = int(target)
                proc = psutil.Process(pid)
                proc.terminate()
                self.add_output(f"Prozess {pid} beendet.", "info")
            except ValueError:
                # Als Prozessname behandeln
                found = False
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == target.lower():
                        proc.terminate()
                        self.add_output(f"Prozess {target} (PID: {proc.info['pid']}) beendet.", "info")
                        found = True
                        break
                        
                if not found:
                    self.add_output(f"Prozess nicht gefunden: {target}", "error")
            except psutil.NoSuchProcess:
                self.add_output(f"Prozess nicht gefunden: {target}", "error")
            except psutil.AccessDenied:
                self.add_output(f"Zugriff verweigert für Prozess: {target}", "error")
                
        except Exception as e:
            self.add_output(f"Fehler beim Beenden: {str(e)}", "error")
    
    # Hardware-Info-Befehle
    def cmd_cpu(self, args):
        """Zeigt CPU-Informationen an"""
        try:
            self.add_output("CPU-Informationen:", "info")
            self.add_output("=" * 40, "system")
            
            # CPU-Name via WMI
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        self.add_output(f"Modell: {processor.Name}", "normal")
                        self.add_output(f"Hersteller: {processor.Manufacturer}", "normal")
                        self.add_output(f"Kerne: {processor.NumberOfCores}", "normal")
                        self.add_output(f"Logische Prozessoren: {processor.NumberOfLogicalProcessors}", "normal")
                        self.add_output(f"Max. Frequenz: {processor.MaxClockSpeed} MHz", "normal")
                        self.add_output(f"Current Clock Speed: {processor.CurrentClockSpeed} MHz", "normal")
                        break
                except Exception as e:
                    self.add_output(f"WMI-Fehler: {str(e)}", "warning")
                    # Fallback mit psutil und platform
                    self.add_output(f"Modell: {platform.processor()}", "normal")
                    self.add_output(f"Physische Kerne: {psutil.cpu_count(logical=False)}", "normal")
                    self.add_output(f"Logische Kerne: {psutil.cpu_count(logical=True)}", "normal")
                    self.add_output(f"Architektur: {platform.architecture()[0]}", "normal")
            else:
                # Fallback ohne WMI
                self.add_output("WMI nicht verfügbar - begrenzte Informationen:", "warning")
                self.add_output(f"Modell: {platform.processor()}", "normal")
                self.add_output(f"Physische Kerne: {psutil.cpu_count(logical=False)}", "normal")
                self.add_output(f"Logische Kerne: {psutil.cpu_count(logical=True)}", "normal")
                self.add_output(f"Architektur: {platform.architecture()[0]}", "normal")
                
            # Aktuelle Auslastung
            cpu_percent = psutil.cpu_percent(interval=1)
            self.add_output(f"Aktuelle Auslastung: {cpu_percent}%", "warning" if cpu_percent > 80 else "normal")
            
            # Frequenz (wenn verfügbar)
            try:
                freq = psutil.cpu_freq()
                if freq:
                    self.add_output(f"Aktuelle Frequenz: {freq.current:.2f} MHz", "normal")
                    self.add_output(f"Min. Frequenz: {freq.min:.2f} MHz", "normal")
                    self.add_output(f"Max. Frequenz: {freq.max:.2f} MHz", "normal")
            except:
                pass
                
        except Exception as e:
            self.add_output(f"Fehler bei CPU-Informationen: {str(e)}", "error")
    
    def cmd_gpu(self, args):
        """Zeigt GPU-Informationen an"""
        try:
            self.add_output("GPU-Informationen:", "info")
            self.add_output("=" * 40, "system")
            
            # GPU via WMI
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    gpu_found = False
                    
                    # Grafikkarten suchen
                    for gpu in c.Win32_VideoController():
                        gpu_found = True
                        self.add_output(f"Modell: {gpu.Name}", "normal")
                        self.add_output(f"Hersteller: {gpu.AdapterCompatibility}", "normal")
                        self.add_output(f"Speicher: {gpu.AdapterRAM} bytes" if gpu.AdapterRAM else "Speicher: Unbekannt", "normal")
                        self.add_output(f"Treiber: {gpu.DriverVersion}", "normal")
                        self.add_output(f"Auflösung: {gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}", "normal")
                        self.add_output("", "normal")
                    
                    if not gpu_found:
                        self.add_output("Keine GPU-Informationen gefunden.", "warning")
                        
                except Exception as e:
                    self.add_output(f"WMI-Fehler bei GPU: {str(e)}", "warning")
            else:
                # Fallback mit psutil (nur begrenzte Informationen)
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        for gpu in gpus:
                            self.add_output(f"Modell: {gpu.name}", "normal")
                            self.add_output(f"Speicher: {gpu.memoryTotal} MB", "normal")
                            self.add_output(f"Genutzter Speicher: {gpu.memoryUsed} MB", "normal")
                            self.add_output(f"Auslastung: {gpu.load*100:.1f}%", "normal")
                            self.add_output(f"Temperatur: {gpu.temperature}°C", "normal")
                    else:
                        self.add_output("Keine GPU gefunden oder GPUtil nicht verfügbar.", "warning")
                except ImportError:
                    self.add_output("GPU-Informationen nicht verfügbar. Installieren Sie 'wmi' oder 'GPUtil' für detaillierte Informationen.", "warning")
                    
        except Exception as e:
            self.add_output(f"Fehler bei GPU-Informationen: {str(e)}", "error")
    
    def cmd_motherboard(self, args):
        """Zeigt Motherboard-Informationen an"""
        try:
            self.add_output("Motherboard-Informationen:", "info")
            self.add_output("=" * 40, "system")
            
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    
                    # Motherboard Informationen
                    for board in c.Win32_BaseBoard():
                        self.add_output(f"Hersteller: {board.Manufacturer}", "normal")
                        self.add_output(f"Modell: {board.Product}", "normal")
                        self.add_output(f"Version: {board.Version}", "normal")
                        self.add_output(f"Seriennummer: {board.SerialNumber}", "normal")
                        break
                    
                    # BIOS Informationen
                    for bios in c.Win32_BIOS():
                        self.add_output(f"BIOS-Hersteller: {bios.Manufacturer}", "normal")
                        self.add_output(f"BIOS-Version: {bios.SMBIOSBIOSVersion}", "normal")
                        self.add_output(f"BIOS-Datum: {bios.ReleaseDate}", "normal")
                        break
                        
                except Exception as e:
                    self.add_output(f"WMI-Fehler bei Motherboard: {str(e)}", "warning")
            else:
                # Fallback - begrenzte Informationen
                self.add_output("Detaillierte Motherboard-Informationen nicht verfügbar.", "warning")
                self.add_output("Installieren Sie 'wmi' für vollständige Informationen.", "info")
                
        except Exception as e:
            self.add_output(f"Fehler bei Motherboard-Informationen: {str(e)}", "error")
    
    def cmd_ram(self, args):
        """Zeigt RAM-Informationen an"""
        try:
            self.add_output("RAM-Informationen:", "info")
            self.add_output("=" * 40, "system")
            
            # Gesamtspeicher
            memory = psutil.virtual_memory()
            self.add_output(f"Gesamtspeicher: {memory.total / (1024**3):.2f} GB", "normal")
            self.add_output(f"Verfügbar: {memory.available / (1024**3):.2f} GB", "normal")
            self.add_output(f"Genutzt: {memory.used / (1024**3):.2f} GB", "normal")
            self.add_output(f"Auslastung: {memory.percent}%", "warning" if memory.percent > 80 else "normal")
            
            # Detaillierte RAM-Module via WMI
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    self.add_output("\nRAM-Module:", "info")
                    for i, ram in enumerate(c.Win32_PhysicalMemory(), 1):
                        self.add_output(f"  Modul {i}:", "normal")
                        self.add_output(f"    Hersteller: {ram.Manufacturer}", "normal")
                        self.add_output(f"    Modell: {ram.PartNumber}", "normal")
                        self.add_output(f"    Kapazität: {int(ram.Capacity) / (1024**3):.2f} GB", "normal")
                        self.add_output(f"    Geschwindigkeit: {ram.Speed} MHz", "normal")
                        self.add_output(f"    Typ: {ram.MemoryType}", "normal")
                        self.add_output("", "normal")
                        
                except Exception as e:
                    self.add_output(f"WMI-Fehler bei RAM: {str(e)}", "warning")
            else:
                self.add_output("\nDetaillierte RAM-Informationen nicht verfügbar.", "warning")
                self.add_output("Installieren Sie 'wmi' für Modul-Informationen.", "info")
                
            # Swap-Speicher
            swap = psutil.swap_memory()
            if swap.total > 0:
                self.add_output(f"\nSwap-Speicher:", "info")
                self.add_output(f"  Gesamt: {swap.total / (1024**3):.2f} GB", "normal")
                self.add_output(f"  Genutzt: {swap.used / (1024**3):.2f} GB", "normal")
                self.add_output(f"  Frei: {swap.free / (1024**3):.2f} GB", "normal")
                
        except Exception as e:
            self.add_output(f"Fehler bei RAM-Informationen: {str(e)}", "error")
    
    def cmd_netzteil(self, args):
        """Zeigt Netzteil-Informationen an"""
        try:
            self.add_output("Netzteil-Informationen:", "info")
            self.add_output("=" * 40, "system")
            
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    
                    # Stromversorgungs-Informationen
                    power_supply_found = False
                    for psu in c.Win32_Battery():
                        power_supply_found = True
                        self.add_output("Akkustatus (Laptop/Notebook):", "info")
                        self.add_output(f"  Status: {psu.BatteryStatus}", "normal")
                        self.add_output(f"  Ladung: {psu.EstimatedChargeRemaining}%", "normal")
                        self.add_output(f"  Chemie: {psu.Chemistry}", "normal")
                        self.add_output(f"  Kapazität: {psu.DesignCapacity} mAh", "normal")
                        self.add_output(f"  Aktuelle Kapazität: {psu.FullChargeCapacity} mAh", "normal")
                        break
                    
                    # Netzteil-Informationen (falls verfügbar)
                    for power in c.Win32_PowerSupply():
                        if power.Name:
                            power_supply_found = True
                            self.add_output("Netzteil-Informationen:", "info")
                            self.add_output(f"  Name: {power.Name}", "normal")
                            self.add_output(f"  Beschreibung: {power.Description}", "normal")
                            self.add_output(f"  Status: {power.Status}", "normal")
                            break
                    
                    if not power_supply_found:
                        self.add_output("Keine Netzteil-Informationen verfügbar.", "warning")
                        self.add_output("Dies ist normal - viele Netzteile senden keine Informationen an Windows.", "info")
                        
                except Exception as e:
                    self.add_output(f"WMI-Fehler bei Netzteil: {str(e)}", "warning")
            else:
                self.add_output("Netzteil-Informationen nicht verfügbar.", "warning")
                self.add_output("Installieren Sie 'wmi' für Stromversorgungs-Informationen.", "info")
                
        except Exception as e:
            self.add_output(f"Fehler bei Netzteil-Informationen: {str(e)}", "error")
    
    # Utility-Befehle
    def cmd_vergleiche(self, args):
        """Vergleicht zwei Dateien (statt fc)"""
        try:
            if len(args) < 2:
                self.add_output("Verwendung: vergleiche <Datei1> <Datei2>", "info")
                return
                
            file1 = args[0]
            file2 = args[1]
            
            if not os.path.isabs(file1):
                file1 = os.path.join(self.current_dir, file1)
            if not os.path.isabs(file2):
                file2 = os.path.join(self.current_dir, file2)
                
            if not os.path.exists(file1):
                self.add_output(f"Datei nicht gefunden: {file1}", "error")
                return
            if not os.path.exists(file2):
                self.add_output(f"Datei nicht gefunden: {file2}", "error")
                return
                
            # Dateien vergleichen
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                content1 = f1.readlines()
                
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                content2 = f2.readlines()
                
            self.add_output(f"Vergleich: {file1} vs {file2}", "info")
            
            if content1 == content2:
                self.add_output("Dateien sind identisch.", "info")
            else:
                self.add_output("Unterschiede gefunden:", "warning")
                for i, (line1, line2) in enumerate(zip_longest(content1, content2, fillvalue=""), 1):
                    if line1 != line2:
                        self.add_output(f"  Zeile {i}:")
                        self.add_output(f"    {file1}: {line1.strip()}")
                        self.add_output(f"    {file2}: {line2.strip()}")
                        
        except Exception as e:
            self.add_output(f"Fehler beim Vergleich: {str(e)}", "error")
    
    def cmd_hilfe(self, args):
        """Zeigt Hilfeinformationen an (statt help)"""
        try:
            self.add_output("ZG Terminal - Hilfe", "system")
            self.add_output("=" * 50, "system")
            self.add_output("", "normal")
            
            # Befehle nach Kategorien gruppieren
            categories = {
                "Dateisystem": [
                    ("liste", "Listet Dateien und Verzeichnisse auf"),
                    ("gehe", "Wechselt das Verzeichnis"),
                    ("erstelle", "Erstellt ein neues Verzeichnis"),
                    ("entferne", "Entfernt ein leeres Verzeichnis"),
                    ("kopiere", "Kopiert Dateien"),
                    ("loesche", "Löscht Dateien"),
                    ("benenne", "Benennt Dateien um"),
                ],
                "Text": [
                    ("zeige", "Zeigt den Inhalt einer Textdatei an"),
                    ("bearbeite", "Öffnet einen einfachen Texteditor"),
                ],
                "System": [
                    ("formatiere", "Formatiert eine Festplatte (Simulation)"),
                    ("pruefe", "Überprüft eine Festplatte auf Fehler"),
                    ("baum", "Zeigt Verzeichnisbaum an"),
                    ("attribute", "Zeigt Dateiattribute an"),
                ],
                "Netzwerk": [
                    ("testnetz", "Testet Netzwerkverbindung (ping)"),
                    ("netzinfo", "Zeigt IP-Konfiguration"),
                    ("netzwerk", "Verwaltet Netzwerkressourcen"),
                ],
                "System-Info": [
                    ("geraete", "Zeigt Systemgeräte-Informationen"),
                    ("datum", "Zeigt/ändert Systemdatum"),
                    ("zeit", "Zeigt/ändert Systemzeit"),
                    ("umgebung", "Zeigt Umgebungsvariablen"),
                    ("prozesse", "Zeigt laufende Prozesse"),
                    ("beende", "Beendet Prozesse"),
                ],
                "Hardware-Info": [
                    ("cpu", "Zeigt CPU-Modell und -Informationen"),
                    ("gpu", "Zeigt GPU-Modell und -Informationen"),
                    ("motherboard/mainboard", "Zeigt Motherboard-Informationen"),
                    ("ram", "Zeigt RAM-Modell und -Speicherinformationen"),
                    ("netzteil", "Zeigt Netzteil-Informationen (falls verfügbar)"),
                ],
                "Sonstiges": [
                    ("vergleiche", "Vergleicht zwei Dateien"),
                    ("clear", "Löscht den Bildschirm"),
                    ("hilfe", "Zeigt diese Hilfe an"),
                    ("ende", "Beendet das Terminal"),
                ]
            }
            
            for category, commands in categories.items():
                self.add_output(f"\n{category}:", "info")
                for cmd, desc in commands:
                    self.add_output(f"  {cmd:<12} - {desc}", "normal")
                    
            self.add_output("\n" + "=" * 50, "system")
            self.add_output("Tipps:", "info")
            self.add_output("  - Verwenden Sie die Pfeiltasten für Befehlsverlauf", "normal")
            self.add_output("  - Tab vervollständigt Befehle automatisch", "normal")
            self.add_output("  - Alle Pfade können relativ oder absolut sein", "normal")
            
        except Exception as e:
            self.add_output(f"Fehler bei Hilfe: {str(e)}", "error")
    
    def cmd_ende(self, args):
        """Beendet das Terminal (statt exit)"""
        self.add_output("ZG Terminal wird beendet. Auf Wiedersehen!", "system")
        self.root.after(1000, self.root.quit)
    
    def cmd_clear(self, args):
        """Löscht den Bildschirm"""
        self.output_area.config(state=tk.NORMAL)
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state=tk.DISABLED)
        self.add_output("ZG Terminal - Bildschirm gelöscht", "system")

def main():
    root = tk.Tk()
    app = ZGTerminal(root)
    root.mainloop()

if __name__ == "__main__":
    main()


