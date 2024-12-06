import PyPDF2
import difflib
import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import scrolledtext
import pyperclip
import argparse
import os, sys
from datetime import datetime

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Icon
import pikepdf

import io


FILE_BACKUP_NAME = 'compareText_last.json'
APP_NAME = "Compare PDFs or text files"
APP_VER = "V0.1"
APP_AUTHOR = "Gian Michele Pasinelli"
APP_EMAIL = "caludia@tiscali.it"
APP_TITLE = APP_NAME + " - " + APP_VER
URL_SATISPAY = None #"https://www.satispay.com/send?amount="
URL_PAYPAL = "https://www.paypal.me/gianmichelepasinelli/"




import json
import locale

def get_system_lang():
    DEFAULT_FALLBACK = 'en'
    # lang, _ = locale.getdefaultlocale()
    lang, _ = locale.getlocale()
    if lang is None:
        print("locale.getlocale() ha ritornato 'None'")
        return DEFAULT_FALLBACK
    if lang.startswith('It'):
        return 'it'
    elif lang.startswith('En'):
        return 'en'
    else:
        print(f"{lang=}")
        return DEFAULT_FALLBACK


def resource_path(relative_path):
    """Restituisce il percorso assoluto alla risorsa, compatibile con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # print("1", os.path.join(sys._MEIPASS, relative_path))
        return os.path.join(sys._MEIPASS, relative_path)
    # print("2", os.path.join(os.path.abspath("."), relative_path))
    return os.path.join(os.path.abspath("."), relative_path)

def load_translation(lang_code):
    translations = {}
    lang_file = os.path.join(resource_path('lang'), f'{lang_code}.txt')
    try:
        with open(lang_file, encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    translations[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"File di lingua non trovato: {lang_file}")
    return translations


def format_file_size(size_bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    if size_bytes > 150:
        return f"{size_bytes:.0f} {units[i]}"
    elif size_bytes > 15:
        return f"{size_bytes:.1f} {units[i]}"
    else:
        return f"{size_bytes:.2f} {units[i]}"


def save_state(file_path):
    """Salva lo stato attuale in un file JSON."""
    state = {
        'file1': entry_pdf1.get(),
        'file2': entry_pdf2.get()
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def load_state(file_path):
    """Carica lo stato da un file JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            entry_pdf1.delete(0, tk.END)
            entry_pdf1.insert(0, state.get('file1', ''))
            entry_pdf2.delete(0, tk.END)
            entry_pdf2.insert(0, state.get('file2', ''))
            # Se il file di stato esiste, abilita la checkbox
            save_state_var.set(1)
    except FileNotFoundError:
        print(f"Nessun file di stato {FILE_BACKUP_NAME} trovato.")
        save_state_var.set(0)  # Disabilita la checkbox se il file non esiste

def extract_text_from_pdf(pdf_path):
    """Estrae il testo da un file PDF."""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_text_file(file_path):
    """Legge il contenuto di un file di testo."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()

def compare_texts(text1, text2, label_text1, label_text2):
    """Confronta due testi e restituisce le differenze a livello di carattere e il grado di somiglianza."""
    diff = difflib.unified_diff(text1.splitlines(), text2.splitlines(), lineterm='', fromfile=label_text1, tofile=label_text2)
    # diff = difflib.ndiff(text1, text2)
    differences = '\n'.join(diff)

    # Calcolo del grado di somiglianza
    seq_matcher = difflib.SequenceMatcher(None, text1, text2)
    similarity = seq_matcher.ratio() * 100  # Percentuale di somiglianza

    return differences, similarity

def show_differences():
    pdf1 = entry_pdf1.get()
    pdf2 = entry_pdf2.get()

    # Estrai il testo dal primo PDF o file di testo
    if pdf1.endswith('.pdf'):
        text1 = extract_text_from_pdf(pdf1)
        label_text1 = "PDF 1"
    else:
        text1 = read_text_file(pdf1)
        label_text1 = f"{T['text_file']} 1"

    # Estrai il testo dal secondo PDF o dagli appunti se non fornito
    if pdf2:  # Se è stato fornito un percorso PDF o file
        if pdf2.endswith('.pdf'):
            text2 = extract_text_from_pdf(pdf2)
            label_text2 = "PDF 2"
        else:
            text2 = read_text_file(pdf2)
            label_text2 = f"{T['text_file']} 2"
    else:  # Altrimenti prendi il contenuto degli appunti
        global clipboard_content
        clipboard_content = text2 = pyperclip.paste()
        label_text2 = "Clipboard"
        label_text1 = label_text1[:-2]

    # Confronta i testi
    differences, similarity = compare_texts(text1, text2, label_text1, label_text2)

    # Mostra i risultati nella finestra di testo
    result_text.delete(1.0, tk.END)  # Pulisci il campo di testo
    result_text.insert(tk.END, f"{T['similarity']}: {similarity:.2f}%\n", 'similarity')
    result_text.insert(tk.END, f"\n{T['difference']}:\n", 'header')

    for line in differences.splitlines():
        if line.startswith('+'):
            result_text.insert(tk.END, line + '\n', 'added')    # Aggiunto (linea nuova)
        elif line.startswith('-'):
            result_text.insert(tk.END, line + '\n', 'removed')  # Rimosso (linea vecchia)
        # elif line.startswith('?'):
        #     result_text.insert(tk.END, line + '\n', 'pointer')  # ? (posizione punti diversi)
        else:
            result_text.insert(tk.END, line + '\n')  # Linea non modificata


def update_text():
    pdf1 = entry_pdf1.get()
    pdf2 = entry_pdf2.get()

    # Estrai il testo dal primo PDF o file di testo
    if pdf1.endswith('.pdf'):
        text1 = extract_text_from_pdf(pdf1)
        label_text1 = "PDF 1"
    else:
        text1 = read_text_file(pdf1)
        label_text1 = f"{T['text_file']} 1"

    # Estrai il testo dal secondo PDF o dagli appunti se non fornito
    if pdf2:  # Se è stato fornito un percorso PDF o file
        if pdf2.endswith('.pdf'):
            text2 = extract_text_from_pdf(pdf2)
            label_text2 = "PDF 2"
        else:
            text2 = read_text_file(pdf2)
            label_text2 = f"{T['text_file']} 2"
    else:  # Altrimenti prendi il contenuto degli appunti
        global clipboard_content
        if clipboard_content != None:
            text2 = clipboard_content
        else:
            clipboard_content = text2 = pyperclip.paste()
        label_text2 = "Clipboard"
        label_text1 = label_text1[:-2]

    # Confronta i testi
    differences, similarity = compare_texts(text1, text2, label_text1, label_text2)

    # Mostra i risultati nella finestra di testo
    result_text.delete(1.0, tk.END)  # Pulisci il campo di testo
    result_text.insert(tk.END, f"{T['similarity']}: {similarity:.2f}%\n", 'similarity')
    result_text.insert(tk.END, f"\n{T['difference']}:\n", 'header')

    for line in differences.splitlines():
        if line.startswith('+'):
            result_text.insert(tk.END, line + '\n', 'added')    # Aggiunto (linea nuova)
        elif line.startswith('-'):
            result_text.insert(tk.END, line + '\n', 'removed')  # Rimosso (linea vecchia)
        # elif line.startswith('?'):
        #     result_text.insert(tk.END, line + '\n', 'pointer')  # ? (posizione punti diversi)
        else:
            result_text.insert(tk.END, line + '\n')  # Linea non modificata


def on_drop_file_1(event):
    global something_change
    file_path = event.data.strip('{}')  # Rimuove eventuali caratteri aggiuntivi
    entry_pdf1.insert(0, file_path)
    something_change = True

def on_drop_file_2(event):
    global something_change
    file_path = event.data.strip('{}')  # Rimuove eventuali caratteri aggiuntivi
    entry_pdf2.insert(0, file_path)
    something_change = True


def create_image(width, height, color1, color2):
    """Create an image with two colors."""
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    return image

def on_quit(icon, item):
    icon.stop()
    root.quit()

def on_minimize():
    global window_geometry, was_maximized
    print("on_minimize event")
    # Store current geometry before hiding the window
    if root.state() == 'zoomed':  # If maximized
        was_maximized = True
    else:
        was_maximized = False
        window_geometry = root.geometry()
    root.withdraw()  # Hide the Tkinter window

def on_delete_window():
    """Gestisce l'evento di chiusura della finestra."""
    # icon.stop()
    # Salva lo stato solo se la checkbox è selezionata
    if save_state_var.get():
        save_state(FILE_BACKUP_NAME)
    root.quit()

def on_restore(icon, item):
    root.deiconify()  # Show the Tkinter window again
    # Restore the geometry of the window
    if was_maximized:
        root.state('zoomed')  # Restore as maximized
    elif window_geometry:
        root.geometry(window_geometry)  # Restore previous geometry


def configure_handler(event):
    global something_change

    # print(event)
    if something_change:
        something_change    =   False
        show_differences    ()


def setup(icon):
    icon.visible = True

def run_tray_icon():
    global icon

    # Create a system tray icon
    icon_image = create_image(64, 64, 'black', 'white')
    icon = Icon("Text Comparator", icon_image, "Text Comparator", menu=pystray.Menu(
        MenuItem("Restore", on_restore),
        MenuItem("Quit", on_quit)
    ))

    # Run the system tray icon
    icon.run(setup)




def center_window(window, width=None, height=None):
    """Center the window on the screen."""
    # Get the width and height of the screen
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    if width == None:       width   =   root.winfo_width()
    if height == None:      height  =   root.winfo_height()

    # Calculate x and y coordinates for the center of the screen
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Set the geometry of the window
    window.geometry(f"{width}x{height}+{x}+{y}")


def rotate_pdf(pdf_path, direction):
    """Ruota il PDF a sinistra o a destra di 90°."""
    if not pdf_path.endswith('.pdf'):
        log_message("Errore: Il file selezionato non è un PDF.", 'error')
        return

    try:
        # Crea il backup del file originale
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = pdf_path.replace(".pdf", f"_old_{timestamp}.pdf")
        os.rename(pdf_path, backup_path)

        # Apri il PDF originale
        with open(backup_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()

            # Ruota ogni pagina
            for page in reader.pages:
                if direction == "left":
                    page.rotate(-90)  # Ruota a sinistra
                elif direction == "right":
                    page.rotate(90)  # Ruota a destra
                writer.add_page(page)

            # Salva il nuovo PDF con il nome originale
            with open(pdf_path, "wb") as output_file:
                writer.write(output_file)

        log_message(f"PDF ruotato con successo ({direction}) e salvato come: {pdf_path}", 'success')
        log_message(f"Backup creato: {backup_path}", 'info')

    except Exception as e:
        log_message(f"Errore durante la rotazione del PDF: {e}", 'error')

def rotate_left():
    """Ruota il primo PDF a sinistra di 90°."""
    pdf_path = entry_pdf1.get()
    log_message(f"Avvio della rotazione a sinistra per il file: {pdf_path}", 'info')
    rotate_pdf(pdf_path, "left")

def rotate_right():
    """Ruota il primo PDF a destra di 90°."""
    pdf_path = entry_pdf1.get()
    log_message(f"Avvio della rotazione a destra per il file: {pdf_path}", 'info')
    rotate_pdf(pdf_path, "right")


def log_message(message, tag=None):
    """Scrive un messaggio nel widget result_text."""
    result_text.insert(tk.END, message + '\n', tag)
    result_text.see(tk.END)  # Scorri automaticamente verso il basso

def open_pdf(file_path):
    """Apre il file PDF con il lettore predefinito."""
    if os.path.isfile(file_path) and file_path.endswith('.pdf'):
        os.startfile(file_path)  # Apre il file con il programma predefinito
    else:
        log_message(f"Errore: Il file '{file_path}' non esiste o non è un PDF.", 'error')

def optimize_pdf(pdf_path, target_size_kb):
    """Riduce la dimensione del PDF a una dimensione specificata in kB utilizzando pikepdf."""
    try:
        target_size_bytes = target_size_kb * 1024

        # Apri il PDF con pikepdf
        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            # Ottimizza il PDF rimuovendo oggetti inutilizzati
            pdf.save(pdf_path)

        # Controlla la dimensione del PDF dopo l'ottimizzazione
        current_size = os.path.getsize(pdf_path)
        if current_size <= target_size_bytes:
            log_message(f"Il PDF è stato ottimizzato ed è ora più piccolo di {target_size_kb} kB.", 'success')
        else:
            log_message(f"Il PDF è stato ottimizzato ma è {current_size/target_size_bytes:.2f} volte più grande del target di {target_size_kb} kB.", 'info')
    except Exception as e:
        log_message(f"Errore durante la riduzione del PDF: {e}", 'error')


def process_image_for_handwritten_notes(pil_img):
    import cv2
    import numpy as np

    # Converti PIL Image in array OpenCV (BGR)
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Converti in scala di grigi
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Applica sogliatura adattiva per binarizzare e rimuovere sfondo variabile
    bin_img = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 9)

    # Rimuovi piccoli rumori con morfologia (apertura)
    kernel = np.ones((2,2), np.uint8)
    clean_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel)

    # Inverti l'immagine per tornare a bianco sfondo e nero testo
    final_img = cv2.bitwise_not(clean_img)

    # Converti di nuovo in PIL Image
    pil_processed = Image.fromarray(final_img)

    return pil_processed


def enhance_handwritten_notes(pil_img):
    import cv2
    import numpy as np

    # Converti PIL Image in array OpenCV in scala di grigi
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

    # Applica filtro Gaussiano per ridurre rumore
    blurred = cv2.GaussianBlur(img, (3,3), 0)

    # Soglia adattiva con metodo Mean per mantenere griglia e testo
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10)

    # Morfologia per alleggerire la griglia (linee sottili)
    kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (1,3))
    grid_light = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_line, iterations=1)

    # Morfologia per esaltare il testo (linee più spesse)
    kernel_text = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    text_enhanced = cv2.morphologyEx(grid_light, cv2.MORPH_CLOSE, kernel_text, iterations=1)

    # Combina l’immagine originale con quella elaborata per mantenere dettagli
    combined = cv2.bitwise_or(thresh, text_enhanced)

    # Inverti per avere sfondo bianco e testo nero
    final_img = cv2.bitwise_not(combined)

    # Converti di nuovo in PIL Image
    pil_result = Image.fromarray(final_img)

    return pil_result

def optimize_pdf_handwritten(input_pdf_path, output_pdf_path, zoom=2):
    import fitz

    doc = fitz.open(input_pdf_path)
    new_doc = fitz.open()

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Renderizza pagina ad alta risoluzione
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Applica miglioramento per appunti su griglia
        optimized_img = enhance_handwritten_notes(img)

        # Salva immagine in buffer PNG
        img_buffer = io.BytesIO()
        optimized_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Crea pagina PDF nuova con dimensioni immagine
        rect = fitz.Rect(0, 0, optimized_img.width, optimized_img.height)
        new_page = new_doc.new_page(width=rect.width, height=rect.height)

        # Inserisci immagine nella pagina
        new_page.insert_image(rect, stream=img_buffer.getvalue())

    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()



def compress_images_in_pdf(pdf_path, output_path, target_size_bytes, initial_quality=75, min_quality=1, step=5):
    """
    Comprimi le immagini nel PDF iterativamente riducendo la qualità JPEG
    fino a raggiungere target_size_bytes o qualità minima.
    """
    import fitz
    import tempfile

    quality = initial_quality
    tmp_file_path = ""
    log_message(f"Dimensione di partenza: {get_pdf_size(pdf_path)}")
    log_message(f"Dimensione target: {target_size_bytes}")

    while True:
        try:
            with fitz.open(pdf_path) as pdf:
                for page in pdf:
                    for img in page.get_images(full=True):
                        xref = img[0]
                        base_image = pdf.extract_image(xref)
                        image_bytes = base_image["image"]
                        # image_ext = base_image["ext"]

                        pil_img = Image.open(io.BytesIO(image_bytes))
                        # log_message(f"Formato immagine '{xref}.{image_ext}': {pil_img.format}", 'info')
                        pil_img = pil_img.convert("RGB")

                        # Comprimi l'immagine
                        buffer = io.BytesIO()
                        pil_img.save(buffer, format="JPEG", quality=quality)  # Riduci la qualità

                        # Sostituisci il flusso dell'immagine
                        page.replace_image(xref, stream=buffer.getvalue())

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    tmp_file_path = tmp_file.name
                print(f"salvataggio {tmp_file_path}")
                pdf.save(tmp_file_path)

            current_size = os.path.getsize(tmp_file_path)
            # log_message(f"Dimensione PDF dopo compressione con qualità {quality}: {current_size} bytes")
            log_message(f"Dimensione PDF dopo compressione con qualità {quality}: {format_file_size(current_size)} bytes ({current_size/target_size_bytes:.2f})")

            if current_size <= target_size_bytes or quality <= min_quality:
                # log_message(f"Compressione completata con qualità {quality}. Dimensione finale: {current_size} bytes", 'success')
                log_message(f"Compressione completata con qualità {quality}. Dimensione finale: {format_file_size(current_size)} bytes", 'success')
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(tmp_file_path, output_path)
                break
            else:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                # Riduci la qualità e ripeti usando il PDF appena salvato
                quality = max(min_quality, quality - step)
                if quality <= 0:
                    break

        except Exception as e:
            log_message(f"Errore durante la compressione: {e}", 'error')
            break


def get_pdf_size(pdf_path):
    """Restituisce la dimensione del PDF """
    return format_file_size(os.path.getsize(pdf_path))


def main1():
    global root, window_geometry, was_maximized
    global entry_pdf1, entry_pdf2, result_text
    global uscita, something_change
    global clipboard_content, save_state_var

    # Variabili globali
    window_geometry = None
    was_maximized = None
    something_change = False
    clipboard_content = None
    uscita = False

    # Configurazione della finestra principale
    root = TkinterDnD.Tk()
    root.title("Confronto Testuale tra PDF o file di testo V2 11/3/2025")

    # Variabile per la checkbox
    save_state_var = tk.IntVar(value=0)

    # Configura la griglia
    root.grid_rowconfigure(4, weight=1)

    # Input per i file PDF
    tk.Label(root, text="File 1:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_pdf1 = tk.Entry(root)
    entry_pdf1.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
    entry_pdf1.drop_target_register(DND_FILES)
    entry_pdf1.dnd_bind('<<Drop>>', on_drop_file_1)

    tk.Label(root, text=f"File 2 ({T['notes_for_empty']}):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    entry_pdf2 = tk.Entry(root)
    entry_pdf2.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
    entry_pdf2.drop_target_register(DND_FILES)
    entry_pdf2.dnd_bind('<<Drop>>', on_drop_file_2)

    # Checkbox per abilitare/disabilitare il salvataggio dello stato
    save_state_checkbox = tk.Checkbutton(root, text=T['enable_save_state'], variable=save_state_var)
    save_state_checkbox.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)

    # Pulsante per avviare il confronto
    compare_button = tk.Button(root, text=T['compare'], command=show_differences)
    compare_button.grid(row=3, column=0, padx=5, pady=5)

    # Pulsante per aggiornare il confronto
    update_button = tk.Button(root, text=T['update'], command=update_text)
    update_button.grid(row=3, column=1, padx=5, pady=5)

    # Pulsanti per ruotare il primo PDF
    rotate_left_button = tk.Button(root, text=T['turn_left'], command=rotate_left)
    rotate_left_button.grid(row=5, column=0, padx=5, pady=5)

    rotate_right_button = tk.Button(root, text=T['turn_right'], command=rotate_right)
    rotate_right_button.grid(row=5, column=1, padx=5, pady=5)

    # Pulsante per aprire il primo PDF
    open_pdf1_button = tk.Button(root, text=T['open'], command=lambda: open_pdf(entry_pdf1.get()))
    open_pdf1_button.grid(row=0, column=2, padx=5, pady=5)

    # Pulsante per aprire il secondo PDF
    open_pdf2_button = tk.Button(root, text=T['open'], command=lambda: open_pdf(entry_pdf2.get()))
    open_pdf2_button.grid(row=1, column=2, padx=5, pady=5)

    # Area di testo per visualizzare i risultati
    result_text = scrolledtext.ScrolledText(root)
    result_text.grid(row=4, columnspan=2, sticky='nsew', padx=5, pady=5)

    # Configura i tag per la colorazione del testo
    result_text.tag_config('similarity', foreground='black')
    result_text.tag_config('header', foreground='blue')
    result_text.tag_config('added', foreground='green')
    result_text.tag_config('removed', foreground='red')

    # Campo di input per la dimensione target
    tk.Label(root, text=f"{T['target_size']} (kB):").grid(row=6, column=0, sticky='w', padx=5, pady=5)
    entry_target_size = tk.Entry(root)
    entry_target_size.setvar("100")
    entry_target_size.grid(row=6, column=1, sticky='ew', padx=5, pady=5)

    # Pulsante per ridurre il PDF
    reduce_button1 = tk.Button(root, text=T['optimise_pdf'], command=lambda: optimize_pdf(entry_pdf1.get(), int(entry_target_size.get())))
    reduce_button1.grid(row=6, column=2, padx=5, pady=5)
    reduce_button2 = tk.Button(
        root,
        text={T['reduce_pdf']},
        command=lambda: compress_images_in_pdf(
            entry_pdf1.get(),
            entry_pdf1.get().replace(".pdf", "_compressed.pdf"),
            int(entry_target_size.get())*1024
        )
    )
    reduce_button2.grid(row=6, column=3, padx=5, pady=5)
    reduce_button3 = tk.Button(
        root,
        text={T['optimise_note']},
        command=lambda: optimize_pdf_handwritten(
            entry_pdf1.get(),
            entry_pdf1.get().replace(".pdf", "_notes.pdf"),
        )
    )
    reduce_button3.grid(row=6, column=4, padx=5, pady=5)

    # Configurazione delle colonne
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=3)

    # Carica lo stato all'avvio
    load_state(FILE_BACKUP_NAME)

    # Bind degli eventi
    root.protocol("WM_DELETE_WINDOW", on_delete_window)
    root.bind("<Configure>", configure_handler)

    # Avvia l'interfaccia grafica
    root.mainloop()

    # while not uscita:
    #     # Avvio dell'interfaccia grafica
    #     root.mainloop()
    #     # Run the system tray icon in a separate thread
    #     icon.run(setup)



def update_target_size_from_file():

    def round_to_significant_figures(x, sig=2):
        import math
        if x == 0:
            return 0
        else:
            return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

    global entry_target_size
    filepath = entry_pdf1.get()
    if os.path.isfile(filepath):
        size_bytes = os.path.getsize(filepath)
        log_message(f"{T['pdf_size']}: {format_file_size(size_bytes)}", 'info')
        size_kb = size_bytes / 1024
        target = size_kb / 4
        target_rounded = round_to_significant_figures(target, 2)
        # Imposta il valore nel campo entry (cancellando il precedente)
        entry_target_size.delete(0, tk.END)
        entry_target_size.insert(0, str(target_rounded))
    else:
        # Se il file non esiste, svuota o imposta un valore di default
        entry_target_size.delete(0, tk.END)
        entry_target_size.insert(0, "100")  # ad esempio


def donate_satispay():
    global amount_var
    import webbrowser
    amount = amount_var.get()
    # Sostituisci con il tuo link Satispay personale (esempio generico):
    url = f"{URL_SATISPAY}{amount}"
    webbrowser.open(url)

def donate_paypal():
    global amount_var
    import webbrowser
    amount = amount_var.get()
    # Sostituisci con il tuo link PayPal personale (esempio generico):
    url = f"{URL_PAYPAL}{amount}"
    webbrowser.open(url)

def populate_info_tab(info_frame):
    global amount_var, paypal_icon

    from PIL import Image, ImageTk

    # Titolo programma
    lbl_title = tk.Label(info_frame, text=APP_TITLE, font=("Helvetica", 16, "bold"))
    lbl_title.pack(pady=(20, 5))

    # Autore e contatti
    lbl_author = tk.Label(info_frame, text=f"{T['author_label']}: {APP_AUTHOR}", font=("Helvetica", 12))
    lbl_author.pack(pady=2)
    lbl_email = tk.Label(info_frame, text=f"Email: {APP_EMAIL}", font=("Helvetica", 10))
    lbl_email.pack(pady=2)

    # Donazioni
    lbl_donate = tk.Label(info_frame, text=f"{T['support']}:", font=("Helvetica", 12, "bold"))
    lbl_donate.pack(pady=(20, 5))

    # Quantità da donare
    frame_amount = tk.Frame(info_frame)
    frame_amount.pack(pady=5)
    tk.Label(frame_amount, text=f"{T['amount']}").pack(side=tk.LEFT)
    amount_var = tk.StringVar(value="5")
    tk.Entry(frame_amount, textvariable=amount_var, width=6).pack(side=tk.LEFT, padx=5)

    # Frame per i pulsanti di donazione
    frame_buttons = tk.Frame(info_frame)
    frame_buttons.pack(pady=10)

    # Pulsante satispay
    if URL_SATISPAY:
        try:
            satispay_img = Image.open(resource_path("Inc/satispay-logo.png")).resize((96, 64))
            satispay_icon = ImageTk.PhotoImage(satispay_img)
            btn_satispay = tk.Button(
                frame_buttons,
                image=satispay_icon,
                command=donate_satispay,
                bg="#cdcdcd",
                height=64,
                width=96
            )
            btn_satispay.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"{T['loading_satispay_icon']}: {e}")
            tk.Button(frame_buttons, text="PayPal", command=donate_satispay).pack(side=tk.LEFT, padx=10)

    # Pulsante PayPal
    if URL_PAYPAL:
        try:
            paypal_img = Image.open(resource_path("Inc/paypal-logo.png")).resize((96, 64))
            paypal_icon = ImageTk.PhotoImage(paypal_img)
            btn_paypal = tk.Button(
                frame_buttons,
                image=paypal_icon,
                command=donate_paypal,
                bg="#cdcdcd",
                height=64,
                width=96
            )
            btn_paypal.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"{T['loading_paypal_icon']}: {e}")
            tk.Button(frame_buttons, text="PayPal", command=donate_paypal).pack(side=tk.LEFT, padx=10)

    # Info privacy
    lbl_privacy = tk.Label(info_frame, text=T['donations'], font=("Helvetica", 10, "italic"))
    lbl_privacy.pack(pady=(20, 2))


def main(args):
    global root, window_geometry, was_maximized
    global entry_pdf1, entry_pdf2, result_text
    global uscita, something_change
    global clipboard_content, save_state_var
    global entry_target_size

    # Variabili globali
    window_geometry = None
    was_maximized = None
    something_change = False
    clipboard_content = None
    uscita = False

    root = TkinterDnD.Tk()
    root.title(f"{APP_NAME} - {APP_VER}")

    # Crea il Notebook (contenitore di schede)
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Scheda principale (già esistente)
    main_frame = tk.Frame(notebook)
    notebook.add(main_frame, text=T['compare'])

    # Frame superiore per input file e checkbox
    frame_top = tk.Frame(main_frame)
    frame_top.grid(row=0, column=0, columnspan=4, sticky='ew', pady=5)
    frame_top.columnconfigure(1, weight=1)

    tk.Label(frame_top, text="File 1:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entry_pdf1 = tk.Entry(frame_top)
    entry_pdf1.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
    entry_pdf1.drop_target_register(DND_FILES)
    entry_pdf1.bind("<FocusOut>", lambda e: update_target_size_from_file())
    entry_pdf1.dnd_bind('<<Drop>>', on_drop_file_1, update_target_size_from_file)
    open_pdf1_button = tk.Button(frame_top, text=T['open'], command=lambda: open_pdf(entry_pdf1.get()))
    open_pdf1_button.grid(row=0, column=2, padx=5, pady=5)

    tk.Label(frame_top, text=f"File 2 ({T['notes_for_empty']}):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    entry_pdf2 = tk.Entry(frame_top)
    entry_pdf2.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
    entry_pdf2.drop_target_register(DND_FILES)
    entry_pdf2.dnd_bind('<<Drop>>', on_drop_file_2)
    open_pdf2_button = tk.Button(frame_top, text=T['open'], command=lambda: open_pdf(entry_pdf2.get()))
    open_pdf2_button.grid(row=1, column=2, padx=5, pady=5)

    if args.file1:
        entry_pdf1.insert(0, args.file1)  # Inserisci il primo file nella Entry
    if args.file2:
        entry_pdf2.insert(0, args.file2)  # Inserisci il secondo file nella Entry

    save_state_var = tk.IntVar(value=0)
    save_state_checkbox = tk.Checkbutton(frame_top, text=T['enable_save_state'], variable=save_state_var)
    # save_state_checkbox.grid(row=0, column=2, padx=10, pady=5, sticky='e')
    save_state_checkbox.grid(row=2, column=0, columnspan=3, sticky='w', padx=5, pady=5)

    # Frame per i pulsanti Confronta e Aggiorna
    frame_azioni = tk.LabelFrame(main_frame, text=T['actions'], padx=5, pady=5)
    frame_azioni.grid(row=1, column=0, sticky='w', padx=5, pady=5)
    # frame_azioni.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
    compare_button = tk.Button(frame_azioni, text=T['compare'], command=show_differences)
    compare_button.pack(side=tk.LEFT, padx=5)
    update_button = tk.Button(frame_azioni, text=T['update'], command=update_text)
    update_button.pack(side=tk.LEFT, padx=5)
    # Frame strumenti sopra result_text
    frame_strumenti = tk.Frame(main_frame)
    frame_strumenti.grid(row=2, column=0, columnspan=4, sticky='ew', pady=5)
    frame_strumenti.columnconfigure(0, weight=1)
    frame_strumenti.columnconfigure(1, weight=3)

    # Frame rotazione
    frame_rotazione = tk.LabelFrame(main_frame, text=T['rotation_frame'], padx=5, pady=5)
    frame_rotazione.grid(row=1, column=1, sticky='w', padx=5, pady=5)
    # frame_rotazione.grid(row=0, column=0, sticky='w')
    rotate_left_button = tk.Button(frame_rotazione, text=T['turn_left'], command=rotate_left)
    rotate_left_button.pack(side=tk.LEFT, padx=5)
    rotate_right_button = tk.Button(frame_rotazione, text=T['turn_right'], command=rotate_right)
    rotate_right_button.pack(side=tk.LEFT, padx=5)

    # Frame ottimizzazione
    frame_ottimizza = tk.LabelFrame(main_frame, text=T['optimize_frame'], padx=5, pady=5)
    frame_ottimizza.grid(row=1, column=2, sticky='e', padx=5, pady=5)
    # frame_ottimizza.grid(row=0, column=1, sticky='e')
    tk.Label(frame_ottimizza, text=f"{T['target_size']} (kB):").pack(side=tk.LEFT, padx=5)
    entry_target_size = tk.Entry(frame_ottimizza, width=8)
    entry_target_size.pack(side=tk.LEFT, padx=5)
    reduce_button1 = tk.Button(frame_ottimizza, text=T['optimise_pdf'], command=lambda: optimize_pdf(entry_pdf1.get(), int(entry_target_size.get())))
    reduce_button1.pack(side=tk.LEFT, padx=2)
    reduce_button2 = tk.Button(frame_ottimizza, text=T['reduce_pdf'], command=lambda: compress_images_in_pdf(entry_pdf1.get(), entry_pdf1.get().replace(".pdf", "_compressed.pdf"), int(entry_target_size.get())*1024))
    reduce_button2.pack(side=tk.LEFT, padx=2)
    reduce_button3 = tk.Button(frame_ottimizza, text=T['optimise_note'], command=lambda: optimize_pdf_handwritten(entry_pdf1.get(), entry_pdf1.get().replace(".pdf", "_notes.pdf")))
    reduce_button3.pack(side=tk.LEFT, padx=2)

    # Area di testo per i risultati (si espande su tutta la finestra)
    result_text = scrolledtext.ScrolledText(main_frame)
    result_text.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

    # Configura i tag per la colorazione del testo
    result_text.tag_config('similarity', foreground='black')
    result_text.tag_config('header', foreground='blue')
    result_text.tag_config('added', foreground='green')
    result_text.tag_config('removed', foreground='red')

    # Configurazione delle colonne e righe per espansione
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)
    root.grid_columnconfigure(3, weight=1)
    root.grid_rowconfigure(3, weight=1)  # Solo la riga di result_text si espande

    # Carica lo stato all'avvio
    load_state(FILE_BACKUP_NAME)


    # Nuova scheda Info
    info_frame = tk.Frame(notebook)
    notebook.add(info_frame, text='Info')
    populate_info_tab(info_frame)

    # Bind degli eventi
    root.protocol("WM_DELETE_WINDOW", on_delete_window)
    root.bind("<Configure>", configure_handler)

    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lang', choices=['it', 'en', 'fr'], help='Interface language')
    parser.add_argument('file1', nargs='?', help="Percorso del primo file (PDF o testo).")
    parser.add_argument('file2', nargs='?', help="Percorso del secondo file (PDF o testo).")

    args, unknown = parser.parse_known_args()

    if args.lang:
        LANG = args.lang
    else:
        LANG = get_system_lang()

    T = load_translation(LANG)
    main(args)
