# Avvio, import delle dipendenze necessarie

import json,datetime
from dotenv import load_dotenv
from os import getenv
from discord_webhook import DiscordWebhook, DiscordEmbed
import classeviva
# Caricamento delle variabili private dal file .env, se esiste.
load_dotenv()
USERNAME= getenv('USERNAME')
PASSWORD= getenv('PASSWORD')
DISCORD_WEBHOOK_URL= getenv('DISCORD_WEBHOOK_URL')

# Definisci date di oggi e domani, per i compiti

oggi = datetime.date.today()
domani = oggi + datetime.timedelta(days=1)
if oggi.weekday() == 5: # Se è sabato il bot elencherà i compiti per la prossima settimana.
    dopodomani = domani + datetime.timedelta(days=7)
    target = 'la prossima settimana'
else:
    dopodomani = domani + datetime.timedelta(days=1)
    target = 'domani'

# Funzione per troncare il titolo a 255 caratteri e restituire una descrizione

def smart_truncate(content, length, suffix='...'):
    if len(content) <= length: # Se il titolo del compito ha meno di 255 caratteri, non ritornare una descrizione
        return content,''
    else: # Se il titolo ha più di 255 caratteri, ritorna titolo del compito tagliato all'ultima parola prima di arrivare a 255 caratteri, con la continuazione del compito come descrizione
        title = ' '.join(content[:length+1].split(' ')[0:-1])
        description = content[len(title):]
        return title + suffix, suffix + description

# Accesso a classeviva

registro = classeviva.Session()
registro.login(USERNAME,PASSWORD)

# Estrazione dei compiti

compiti = registro.agenda(domani,dopodomani)
compiti_json = json.loads(json.dumps(compiti))
compiti_list = compiti_json['agenda']

# Ordina cronologicamente ogni compito e nota dall'ora di inizio dell'evento

compiti_list = sorted(compiti_list, key=lambda x:datetime.datetime.fromisoformat(x['evtDatetimeBegin']).timestamp())

# Ora, minuti e secondi in cui sono stati estratti i compiti
ora_compiti = datetime.datetime.now()
ora_compiti_str = ora_compiti.strftime('%H:%M')

# Crea webhook
messaggio = f'✏️ Compiti ed annotazioni per {target} ({domani.strftime("%d/%m")}-{dopodomani.strftime("%d/%m")})'
webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, username=messaggio, rate_limit_retry=True)
for numero_nota,nota in enumerate(compiti_list,start=1):
    compito_ora = datetime.datetime.fromisoformat(nota['evtDatetimeBegin']).timestamp()
    compito_color = "0000ff" if nota['evtCode'] == "AGNT" else "ff00ff"
    title,description = smart_truncate(nota['notes'],250)
    embed = DiscordEmbed(
        title=title,
        description=description,
        color=compito_color
    )
    embed.set_image(url='https://raw.githubusercontent.com/bortox/discord-classeviva-domani-webhook/main/line.png')
    embed.set_timestamp(compito_ora)
    embed.set_author(name=nota['authorName'].title())
    embed.set_footer(text=nota['classDesc'])
    webhook.add_embed(embed)
    if numero_nota % 10 == 0:  # Ogni 10 embed (se il resto della divisione tra numero nota e 10 è zero) , massimo consentito da Discord, viene inviato lo webhook. Meglio inviare uno webhook con 10 embed che 10 webhook con 1 embed l'uno, col rischio di avere un rate limiting di 5 minuti.
        response = webhook.execute(remove_embeds=True)
response = webhook.execute(remove_embeds=True) # Invia gli embed rimanenti, se ce ne sono.
print('All done! Homeworks updated!')
