from flask import Flask, render_template, request, Response
import sqlite3
import csv
from io import StringIO
import os
from mailersend import MailerSendClient, EmailBuilder

app = Flask(__name__)

# --- CONFIGURAZIONE MAILERSEND ---
MAILERSEND_API_KEY = os.environ.get('MAILERSEND_API_KEY')
EMAIL_MITTENTE = os.environ.get('EMAIL_MITTENTE')
EMAIL_DESTINATARIO = os.environ.get('EMAIL_DESTINATARIO')

def invia_email_notifica(dati_dict):
    """Invia un'email di notifica istantanea tramite API MailerSend."""
    if not MAILERSEND_API_KEY or not EMAIL_MITTENTE or not EMAIL_DESTINATARIO:
        print("Configurazione MailerSend incompleta. Email non inviata.")
        return

    body = "È stata inviata una nuova risposta al questionario.\n\n"
    body += "=== RIEPILOGO DETTAGLIATO ===\n\n"
    for chiave, valore in dati_dict.items():
        if valore:
            body += f"• {chiave}: {valore}\n"

    try:
        ms = MailerSendClient(api_key=MAILERSEND_API_KEY)
        
        email = (EmailBuilder()
            .from_email(EMAIL_MITTENTE, "Questionario Coaching")
            .to_many([{"email": EMAIL_DESTINATARIO, "name": "Admin"}])
            .subject("Nuova risposta ricevuta al Questionario Coaching!")
            .text(body)
            .build())

        response = ms.emails.send(email)
        print("Email inviata con successo tramite MailerSend!")
    except Exception as e:
        print(f"Errore durante l'invio dell'email via MailerSend: {e}")

def init_db():
    """Inizializza il database SQLite locale."""
    conn = sqlite3.connect('risultati.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risposte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            d1_eta TEXT, d2_genere TEXT, d3_paese TEXT, d4_sessioni TEXT,
            d5_tempo TEXT, d6_struttura TEXT, d7_setting TEXT, d8_limiti TEXT,
            d9_obiettivi TEXT, d10_concordati TEXT,
            d11_imp_0 INTEGER, d11_sod_0 INTEGER, d11_imp_1 INTEGER, d11_sod_1 INTEGER,
            d11_imp_2 INTEGER, d11_sod_2 INTEGER, d11_imp_3 INTEGER, d11_sod_3 INTEGER,
            d11_imp_4 INTEGER, d11_sod_4 INTEGER, d11_imp_5 INTEGER, d11_sod_5 INTEGER,
            d11_imp_6 INTEGER, d11_sod_6 INTEGER, d11_imp_7 INTEGER, d11_sod_7 INTEGER,
            d11_imp_8 INTEGER, d11_sod_8 INTEGER, d11_imp_9 INTEGER, d11_sod_9 INTEGER,
            d11_imp_10 INTEGER, d11_sod_10 INTEGER, d11_imp_11 INTEGER, d11_sod_11 INTEGER,
            df_a TEXT, df_b TEXT, df_c TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    init_db()

    data = (
        request.form.get('d1_eta'), request.form.get('d2_genere'), request.form.get('d3_paese'),
        request.form.get('d4_sessioni'), request.form.get('d5_tempo'), request.form.get('d6_struttura'),
        request.form.get('d7_setting'), request.form.get('d8_limiti'), request.form.get('d9_obiettivi'),
        request.form.get('d10_concordati'),
        request.form.get('d11_imp_0'), request.form.get('d11_sod_0'),
        request.form.get('d11_imp_1'), request.form.get('d11_sod_1'),
        request.form.get('d11_imp_2'), request.form.get('d11_sod_2'),
        request.form.get('d11_imp_3'), request.form.get('d11_sod_3'),
        request.form.get('d11_imp_4'), request.form.get('d11_sod_4'),
        request.form.get('d11_imp_5'), request.form.get('d11_sod_5'),
        request.form.get('d11_imp_6'), request.form.get('d11_sod_6'),
        request.form.get('d11_imp_7'), request.form.get('d11_sod_7'),
        request.form.get('d11_imp_8'), request.form.get('d11_sod_8'),
        request.form.get('d11_imp_9'), request.form.get('d11_sod_9'),
        request.form.get('d11_imp_10'), request.form.get('d11_sod_10'),
        request.form.get('d11_imp_11'), request.form.get('d11_sod_11'),
        request.form.get('df_a'), request.form.get('df_b'), request.form.get('df_c')
    )

    conn = sqlite3.connect('risultati.db')
    cursor = conn.cursor()
    placeholders = ', '.join(['?'] * len(data))
    
    query = f'''
        INSERT INTO risposte (
            d1_eta, d2_genere, d3_paese, d4_sessioni, d5_tempo, d6_struttura, d7_setting, d8_limiti, d9_obiettivi, d10_concordati,
            d11_imp_0, d11_sod_0, d11_imp_1, d11_sod_1, d11_imp_2, d11_sod_2, d11_imp_3, d11_sod_3, d11_imp_4, d11_sod_4,
            d11_imp_5, d11_sod_5, d11_imp_6, d11_sod_6, d11_imp_7, d11_sod_7, d11_imp_8, d11_sod_8, d11_imp_9, d11_sod_9,
            d11_imp_10, d11_sod_10, d11_imp_11, d11_sod_11, df_a, df_b, df_c
        ) VALUES ({placeholders})
    '''
    cursor.execute(query, data)
    conn.commit()
    conn.close()

    # Invia l'email tramite MailerSend
    invia_email_notifica(request.form.to_dict())

    return "<h2 style='text-align:center; color:#0b3c5d; font-family:sans-serif; margin-top:50px;'>Grazie! Le tue risposte sono state inviate con successo.</h2>"

@app.route('/download')
def download():
    init_db()
    conn = sqlite3.connect('risultati.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM risposte")
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    conn.close()
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=risposte_coaching.csv"}
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)