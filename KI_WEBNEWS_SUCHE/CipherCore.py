import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import threading
import time
import json
import re  # Import für reguläre Ausdrücke
from duckduckgo_search import DDGS  # Import der DDGS-Klasse
import sys

# Funktion zum Öffnen eines Links im Browser
def open_link(link):
    webbrowser.open(link)

# Funktion zur DuckDuckGo-Suche
def duckduckgo_search(query, language):
    ddgs = DDGS()
    region = 'wt-wt' if language == 'all' else 'de-de'
    results = ddgs.text(query, region=region, safesearch='moderate', max_results=10)

    if not results:
        return [{'title': "Keine Ergebnisse", 'link': '', 'snippet': "Es wurden keine passenden Ergebnisse gefunden."}]

    return results

# Funktion zur Codestral-Analyse
def codestral_analysis(snippet):
    data = {
        "model": "codestral-latest",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein Artikelnanalyst, der Artikel in Deutsche zusammenfasst und analysiert."
                )
            },
            {
                "role": "user",
                "content": f"Fasse folgende Nachricht in Deutsch zusammen und zeige den Webseiten Link an: {snippet}"
            }
        ],
        "max_tokens": 600,
        "temperature": 0.6
    }

    try:
        response = requests.post(
            "https://codestral.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},  # Verwenden Sie den gespeicherten API-Key
            json=data
        )
        if response.status_code == 200:
            response_json = response.json()
            if "choices" in response_json and response_json["choices"]:
                return response_json["choices"][0]["message"]["content"]
            else:
                return "Keine Zusammenfassung verfügbar."
        else:
            return f"Fehler bei der Anfrage: HTTP {response.status_code}"
    except Exception as e:
        return f"Fehler bei der Anfrage: {str(e)}"

def codestral_analysis_thread(snippet, summary_label, wait_label, title_label, link_button):
    try:
        summary = codestral_analysis(snippet)
        summary_label.config(text="Zusammenfassung: " + summary)

        # Extrahiere den Link aus der KI-Antwort
        link = extract_link_from_summary(summary)
        if link:
            title_label.bind("<Button-1>", lambda e, link=link: open_link(link))
            link_button.config(command=lambda link=link: open_link(link))
    except Exception as e:
        summary_label.config(text=f"Fehler bei der Analyse: {str(e)}")
    finally:
        wait_label.config(text="")

# Aktualisierte Funktion zur Extraktion des Links
def extract_link_from_summary(summary):
    # Verwende einen regulären Ausdruck, um den Link zu extrahieren und vermeide das Anhängen von Klammern
    link_match = re.search(r'(https?://[^\s\)]+)', summary)
    if link_match:
        return link_match.group(0)  # Gibt die gefundene URL ohne die abschließende Klammer zurück
    return None

# Funktion zur Suche von Nachrichten
def search_news():
    query = search_entry.get()
    language = language_var.get()
    if query:
        print(f"Suche nach: {query}")
        news_results = duckduckgo_search(query, language)  # DuckDuckGo Suche mit Sprachauswahl
        print(f"Gefundene Ergebnisse: {len(news_results)}")
        show_news_in_gui(news_results, 0, query)

# Funktion zur Anzeige von Nachrichten in der GUI
def show_news_in_gui(articles, page, query):
    for widget in inner_frame.winfo_children():
        widget.destroy()

    for article in articles:
        frame = ttk.Frame(inner_frame)
        frame.grid(sticky="ew", padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)

        # Überprüfe, ob 'FirstURL' oder eine ähnliche URL verfügbar ist
        article_url = article.get('href', '')

        title_label = tk.Label(frame, text=article['title'], font=current_font, fg="blue", cursor="hand2", wraplength=600)
        title_label.grid(row=0, column=1, sticky="nw")

        # Nutze die direkte URL des Artikels, wenn sie verfügbar ist
        if article_url:
            title_label.bind("<Button-1>", lambda e, link=article_url: open_link(link))

        snippet_label = tk.Label(frame, text=article['body'], font=current_font, wraplength=600, justify="left")
        snippet_label.grid(row=1, column=1, sticky="nw")

        summary_label = tk.Label(frame, text="Zusammenfassung: wird geladen...", font=(current_font[0], current_font[1], "bold"), fg="blue", wraplength=600, justify="left")
        summary_label.grid(row=2, column=1, sticky="nw")

        wait_label = tk.Label(frame, text="Bitte warten, Anfrage wird bearbeitet...", font=current_font)
        wait_label.grid(row=3, column=1, sticky="nw")

        # Button "Zum Artikel" zur Verwendung des Hauptlinks des Artikels
        link_button = tk.Button(frame, text="Zum Artikel", font=current_font, fg="blue", command=lambda link=article_url: open_link(link))
        link_button.grid(row=4, column=1, sticky="nw", pady=5)

        # Codestral-Analyse für den Artikelinhalt
        threading.Thread(target=codestral_analysis_thread, args=(article['body'], summary_label, wait_label, title_label, link_button)).start()

        # Button zum Kopieren des Snippets in die Zwischenablage
        copy_button = tk.Button(frame, text="Snippet kopieren", command=lambda snippet=article['body']: root.clipboard_append(snippet))
        copy_button.grid(row=5, column=1, sticky="nw", pady=5)

    pagination_frame = ttk.Frame(inner_frame)
    pagination_frame.grid(sticky="ew", pady=10)

    for i in range(5):
        page_button = tk.Button(pagination_frame, text=str(i + 1), command=lambda p=i: load_page(query, p), font=current_font)
        page_button.pack(side="left", padx=5)

# Funktion zum Laden der nächsten Seite
def load_page(query, page):
    language = language_var.get()
    threading.Thread(target=load_page_thread, args=(query, page, language)).start()

# Funktion zum Laden der nächsten Seite in einem separaten Thread
def load_page_thread(query, page, language):
    news_results = duckduckgo_search(query, language)
    show_news_in_gui(news_results, page, query)
    time.sleep(15)

# Funktion zum Anzeigen der Hilfe
def show_help():
    help_window = tk.Toplevel(root)
    help_window.title("Hilfe")
    help_window.geometry("400x300")
    help_window.configure(bg="#f0f0f0")

    bg_image_help = tk.PhotoImage(file=resource_path("gui.png"))  # Ersetzen Sie "background.png" durch den Pfad zu Ihrem Hintergrundbild
    bg_label_help = tk.Label(help_window, image=bg_image_help)
    bg_label_help.place(x=0, y=0, relwidth=1, relheight=1)

    help_label = tk.Label(help_window, text="Dies ist eine kurze Anleitung zur Nutzung der KI-gestützten Websuche.\n\n1. Geben Sie Ihre Suchanfrage in das Eingabefeld ein.\n2. Wählen Sie die gewünschte Sprache aus.\n3. Drücken Sie 'Enter'.\n4. Die Ergebnisse werden angezeigt und können durch Klicken auf die Titel geöffnet werden.\n5. Zusammenfassungen der Artikel werden automatisch generiert.", font=("Arial", 14), justify="left", bg="#f0f0f0", wraplength=380)
    help_label.pack(padx=10, pady=10)

    help_window.bg_image_help = bg_image_help  # Referenz speichern, um das Bild vor dem Garbage Collector zu schützen

# Funktion zum Anzeigen der Info
def show_info():
    info_window = tk.Toplevel(root)
    info_window.title("Info")
    info_window.geometry("400x250")
    info_window.configure(bg="#f0f0f0")

    bg_image_info = tk.PhotoImage(file=resource_path("gui.png"))  # Ersetzen Sie "background.png" durch den Pfad zu Ihrem Hintergrundbild
    bg_label_info = tk.Label(info_window, image=bg_image_info)
    bg_label_info.place(x=0, y=0, relwidth=1, relheight=1)

    info_label = tk.Label(info_window, text="Es handelt sich um eine KI-gestützte Websuche.\n\nProgrammiert von Ralf Krümmel von CipherCore.\n\nDie KI Codestral von Mistral wird genutzt. Die API ist aktuell kostenlos zu erhalten.\n\nhttps://chat.mistral.ai/", font=("Arial", 14), justify="left", bg="#f0f0f0", wraplength=380)
    info_label.pack(padx=10, pady=10)

    info_window.bg_image_info = bg_image_info  # Referenz speichern, um das Bild vor dem Garbage Collector zu schützen

# Funktion zum Anzeigen des Supports
def show_support():
    support_window = tk.Toplevel(root)
    support_window.title("Support")
    support_window.geometry("400x200")
    support_window.configure(bg="#f0f0f0")

    bg_image_support = tk.PhotoImage(file=resource_path("gui.png"))  # Ersetzen Sie "background.png" durch den Pfad zu Ihrem Hintergrundbild
    bg_label_support = tk.Label(support_window, image=bg_image_support)
    bg_label_support.place(x=0, y=0, relwidth=1, relheight=1)

    support_label = tk.Label(support_window, text="CipherCore steht Ihnen gerne für weitere Fragen zur Verfügung.\n\nKontakt: CipherCore@nextgeninnovators.de", font=("Arial", 14), justify="left", bg="#f0f0f0", wraplength=380)
    support_label.pack(padx=10, pady=10)

    support_window.bg_image_support = bg_image_support  # Referenz speichern, um das Bild vor dem Garbage Collector zu schützen

# Funktion zum Eingeben und Speichern des API-Keys
def set_api_key():
    global api_key
    api_key = simpledialog.askstring("API-Key eingeben", "Geben Sie den Codestral API-Key ein:", show='*')
    if api_key:
        with open('api_key.json', 'w') as f:
            json.dump({'api_key': api_key}, f)
        messagebox.showinfo("Erfolg", "API-Key wurde gespeichert.")
    else:
        messagebox.showwarning("Fehler", "API-Key wurde nicht eingegeben.")

# Funktion zum Ermitteln des Pfads zur Ressource
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# GUI Setup
root = tk.Tk()
root.title("CipherCore, durchsuche das WEB")
root.geometry("800x800")
root.resizable(False, False)

# Menü hinzufügen
menu = tk.Menu(root)
root.config(menu=menu)

help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Hilfe", menu=help_menu)
help_menu.add_command(label="Hilfe", command=show_help)
help_menu.add_command(label="Info", command=show_info)
help_menu.add_command(label="Support", command=show_support)
help_menu.add_command(label="API-Key eingeben", command=set_api_key)

# Hintergrundfarbe und Hintergrundbild setzen
root.configure(bg="#f0f0f0")
bg_image = tk.PhotoImage(file=resource_path("gui.png"))  # Ersetzen Sie "background.png" durch den Pfad zu Ihrem Hintergrundbild
bg_label = tk.Label(root, image=bg_image)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# Rahmen um die GUI
frame_border = tk.Frame(root, bg="black", bd=2)
frame_border.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

# Innerer Rahmen für die GUI-Elemente
inner_frame_border = tk.Frame(frame_border, bg="#ffffff")
inner_frame_border.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

search_frame = ttk.Frame(inner_frame_border)
search_frame.pack(pady=10, padx=10, fill="x")

search_entry = tk.Entry(search_frame, width=60, font=("Arial", 14))
search_entry.pack(side="left", padx=10, fill="x", expand=True)
search_entry.bind("<Return>", lambda event: search_news())

search_button = tk.Button(search_frame, text="Suchen", command=lambda: search_news(), font=("Arial", 12))
search_button.pack(side="left", padx=5)

# Hinzufügen eines Optionsfeldes für die Sprachwahl
language_var = tk.StringVar(value='de')
language_frame = ttk.Frame(inner_frame_border)
language_frame.pack(pady=5, padx=10, fill="x")

de_radio = tk.Radiobutton(language_frame, text="Nur deutsche Ergebnisse", variable=language_var, value='de')
de_radio.pack(side="left", padx=10)

all_radio = tk.Radiobutton(language_frame, text="Weltweite Ergebnisse", variable=language_var, value='all')
all_radio.pack(side="left", padx=10)

canvas = tk.Canvas(inner_frame_border)
canvas.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(inner_frame_border, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)
inner_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=inner_frame, anchor="nw")

# Funktion zur Konfiguration des Scrollbereichs
def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

inner_frame.bind("<Configure>", on_configure)

# Funktion zur Handhabung des Mausrads
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

# Binden des Mausrads an die Canvas
canvas.bind_all("<MouseWheel>", on_mousewheel)

# Lade die gespeicherte Schriftgröße und den API-Key
try:
    with open('font_size.json', 'r') as f:
        font_data = json.load(f)
        current_font = ("Arial", font_data.get('font_size', 14))
except FileNotFoundError:
    current_font = ("Arial", 14)

try:
    with open('api_key.json', 'r') as f:
        api_data = json.load(f)
        api_key = api_data.get('api_key', '')
except FileNotFoundError:
    api_key = ''

root.mainloop()
