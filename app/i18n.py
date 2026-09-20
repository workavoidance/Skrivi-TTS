"""Small English/Bokmal UI catalogue; speech language remains independent."""
import ctypes
LANGUAGE='en'
NB={
'Local reading. Part of the Skrivi family.':'Lokal opplesing. En del av Skrivi-familien.',
'Read aloud':'Les høyt','Read':'Les','Voices && models':'Stemmer og modeller','Voices & models':'Stemmer og modeller','Settings':'Innstillinger',
'On this device':'På denne enheten','Reading language':'Lesespråk','Automatic':'Automatisk','English':'Engelsk','Norwegian Bokmål':'Norsk bokmål',
'Your everyday voices':'Dine stemmer','Reading speed':'Lesehastighet','Stop':'Stopp','Try a sample':'Prøv en eksempeltekst','Save audio…':'Lagre lyd…',
'Read screen region':'Les et skjermområde','Read selected text':'Les merket tekst','Open reader':'Åpne leseren','Stop reading':'Stopp opplesing','Quit Skrivi Lytt':'Avslutt Skrivi Lytt',
'Read from any application':'Les fra alle programmer','Selected-text shortcut':'Hurtigtast for merket tekst','When detection is uncertain':'Når språket er usikkert',
'Start quietly in the tray when I sign in':'Start i systemstatusfeltet når jeg logger på','Image layout':'Bildeoppsett','Paragraph / single column':'Avsnitt / én spalte',
'Automatic page layout (columns)':'Automatisk sideoppsett (spalter)','For columns, select the main text without shared headings or footers.':'For spalter: merk hovedteksten uten felles overskrift eller bunntekst.',
'Both models are included. English voices share one download.':'Begge modellene følger med. Engelske stemmer deler samme modell.',
'Two local models, kept through updates.':'To lokale modeller som beholdes ved oppdateringer.','Download / verify':'Last ned / kontroller','Import existing…':'Importer eksisterende…','Cancel download':'Avbryt nedlasting',
'Model':'Modell','Size':'Størrelse','Availability':'Tilgjengelighet','Ready':'Klar','Ready.':'Klar.','Not installed':'Ikke installert',
'Project & updates':'Prosjekt og oppdateringer','Open model folder':'Åpne modellmappen','Check for updates':'Se etter oppdateringer',
'Interface language':'Grensesnittspråk','Automatic (Windows display language)':'Automatisk (Windows-visningsspråk)','Application':'Program',
'Getting selected text…':'Henter merket tekst…','Select a screen region…':'Velg et skjermområde…','Drag around the text to read.':'Dra rundt teksten som skal leses.',
'Recognising text…':'Gjenkjenner tekst…','Starting voice…':'Starter stemmen…','Getting the local voice engine ready.':'Gjør den lokale talemotoren klar.',
'Loading voice…':'Laster stemmen…','Kept ready for your next reading.':'Holdes klar til neste opplesing.','Preparing speech…':'Forbereder tale…','Reading aloud':'Leser høyt',
'Esc · Cancel':'Esc · Avbryt','Esc · Stop':'Esc · Stopp','Dismiss':'Lukk','Could not read':'Kunne ikke lese','Stopping…':'Stopper…','Stopped.':'Stoppet.',
'A familiar voice for the words in front of you.':'En kjent stemme for ordene foran deg.','SKRIVI LYTT  /  TEXT TO SPEECH':'SKRIVI LYTT  /  TEKST TIL TALE',
'Paste or type something to read…':'Lim inn eller skriv noe som skal leses…','Text to read':'Tekst som skal leses',
'Closing this window keeps Skrivi Lytt in the tray. Text is not saved.':'Lukker du vinduet, fortsetter Skrivi Lytt i systemstatusfeltet. Teksten lagres ikke.',
'Select text, then press the shortcut to read immediately. Press it again to stop. Automatic uses one voice for the whole selection.':'Merk tekst og trykk hurtigtasten for å lese med en gang. Trykk igjen for å stoppe. Automatisk bruker én stemme for hele teksten.',
'Checking for updates…':'Ser etter oppdateringer…','No newer stable release is available.':'Ingen nyere stabil versjon er tilgjengelig.',
'Drag around one paragraph or column. Escape cancels.':'Dra rundt ett avsnitt eller en spalte. Escape avbryter.'}
def configure(choice):
 global LANGUAGE
 if choice=='auto':
  locale=ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3ff
  LANGUAGE='nb' if locale==0x14 else 'en'
 else:LANGUAGE=choice if choice in ('en','nb') else 'en'
def tr(text):return NB.get(text,text) if LANGUAGE=='nb' else text

def translate_widgets(root):
 from PySide6.QtCore import QSignalBlocker,Qt
 from PySide6.QtWidgets import QLabel,QAbstractButton,QComboBox,QTabWidget
 from PySide6.QtGui import QAction
 for obj in root.findChildren(QLabel)+root.findChildren(QAbstractButton)+root.findChildren(QAction):
  source=obj.property('sourceText')
  if source is None:source=obj.text();obj.setProperty('sourceText',source)
  obj.setText(tr(source))
 for box in root.findChildren(QComboBox):
  with QSignalBlocker(box):
   for i in range(box.count()):
    source=box.itemData(i,Qt.ItemDataRole.UserRole+1)
    if source is None:source=box.itemText(i);box.setItemData(i,source,Qt.ItemDataRole.UserRole+1)
    box.setItemText(i,tr(source))
 for tabs in root.findChildren(QTabWidget):
  for i in range(tabs.count()):
   key='sourceTab'+str(i);source=tabs.property(key)
   if source is None:source=tabs.tabText(i);tabs.setProperty(key,source)
   tabs.setTabText(i,tr(source))


NB.update({
    "Shortcuts": "Hurtigtaster",
    "General": "Generelt",
    "Models": "Modeller",
    "Privacy": "Personvern",
    "About": "Om",
    "Changes are saved automatically": "Endringer lagres automatisk",
    "Open Skrivi Snakk": "Åpne Skrivi Snakk",
    "Open Skrivi Lytt": "Åpne Skrivi Lytt",
    "Quit Skrivi Snakk": "Avslutt Skrivi Snakk",
    "Help": "Hjelp",
    "Give feedback": "Gi tilbakemelding",
    "Check for updates": "Se etter oppdateringer",
    "Release notes and download": "Versjonsnotater og nedlasting",
    "Checking for updates…": "Ser etter oppdateringer …",
    "Could not check for updates. Check your connection and try again.": "Kunne ikke se etter oppdateringer. Kontroller nettilkoblingen og prøv igjen.",
    "Version {version} is available.": "Versjon {version} er tilgjengelig.",
    "You have the latest test release.": "Du har den nyeste testutgaven.",
    "Installed version: {version} · Test release": "Installert versjon: {version} · Testutgave",
    "Keyboard shortcut": "Hurtigtast",
    "Try dictation here…": "Prøv diktering her …",
    "Clear": "Tøm",
    "Close": "Lukk",
    "Try dictation here: click the box, hold your shortcut, speak, then release. Esc cancels. You can also dictate directly into another app.": "Prøv diktering her: Klikk i feltet, hold hurtigtasten, snakk og slipp. Esc avbryter. Du kan også diktere direkte i et annet program.",
    "Practice text is not saved and is cleared when this window closes. Closing the window keeps Skrivi Snakk in the tray.": "Øvingsteksten lagres ikke og tømmes når du lukker vinduet. Skrivi Snakk fortsetter å kjøre i systemstatusfeltet.",
    "Esc · Cancel": "Esc · Avbryt",
    "Esc · Stop": "Esc · Stopp",
    "Dismiss": "Lukk",
    "Retry": "Prøv igjen",
    "Details": "Detaljer",
    "English voice": "Engelsk stemme",
    "Show activity indicator": "Vis aktivitetsindikator",
    "Change shortcut…": "Endre hurtigtast …",
    "Press a key or combination…": "Trykk en tast eller kombinasjon …",
    "Use Ctrl or Alt with a letter, Space or F6–F12.": "Bruk Ctrl eller Alt sammen med en bokstav, mellomrom eller F6–F12.",
    "Screen-region shortcut": "Hurtigtast for skjermområde",
    "Restore default": "Gjenopprett standard",
    "Esc cancels active work. Keep Right Ctrl or Left Ctrl + Windows for Skrivi Snakk. Avoid Ctrl + Alt as its dictation shortcut when using Lytt.": "Esc avbryter aktivt arbeid. Bruk høyre Ctrl eller venstre Ctrl + Windows til Skrivi Snakk. Unngå Ctrl + Alt til diktering når du bruker Lytt.",
    "Download model": "Last ned modell",
    "Locate existing files…": "Finn eksisterende filer …",
    "Verify files": "Kontroller filer",
    "Files verified.": "Filene er kontrollert.",
    "Advanced model details": "Avanserte modelldetaljer",
    "Your words stay yours.": "Ordene dine forblir dine.",
    "Reading and screen recognition happen on this PC. No account, telemetry or cloud speech service.": "Opplesing og tekstgjenkjenning skjer på denne PC-en. Ingen konto, telemetri eller skytjeneste.",
    "Selection and screen capture": "Merket tekst og skjermbilder",
    "Reading selected text may briefly use and restore the clipboard. Screen-region images are processed in memory and are not saved.": "Opplesing av merket tekst kan bruke utklippstavlen kortvarig og gjenoppretter den. Bilder av skjermområder behandles i minnet og lagres ikke.",
    "Audio and saved files": "Lyd og lagrede filer",
    "Temporary speech audio is removed on normal exit. Save audio creates a file only when you choose to save it. Other apps may save or sync your text.": "Midlertidig talelyd fjernes ved normal avslutning. Lagre lyd oppretter bare en fil når du velger det. Andre programmer kan lagre eller synkronisere teksten din.",
    "Read full privacy details": "Les mer om personvern",
    "Release notes": "Versjonsnotater",
    "Source code": "Kildekode",
    "Third-party licences": "Tredjepartslisenser",
    "Explore Skrivi Snakk": "Utforsk Skrivi Snakk",
    "Settings could not be saved. Previous settings remain active.": "Innstillingene kunne ikke lagres. Tidligere innstillinger gjelder fortsatt.",
    "Choose different shortcuts for selected text and screen regions.": "Velg forskjellige hurtigtaster for merket tekst og skjermområder.",
    "Finished.": "Ferdig.",
    "Stopped.": "Stoppet.",
    "Stopping…": "Stopper …",
    "Open Skrivi Lytt for details and recovery.": "Åpne Skrivi Lytt for detaljer og hjelp.",
    "Closing this window keeps Skrivi Lytt in the tray. Text is not saved.": "Lukking av vinduet lar Skrivi Lytt kjøre i systemstatusfeltet. Teksten lagres ikke.",
    "Text to read": "Tekst som skal leses",
    "Reading progress": "Opplesingsstatus",
    "Model verification failed. Locate existing files or download the model again.": "Kontroll av modellen mislyktes. Finn eksisterende filer eller last ned modellen på nytt.",
    "That shortcut is already in use. Choose another in Settings.": "Hurtigtasten er allerede i bruk. Velg en annen i Innstillinger."
})

NB['Short or uncertain text uses your fallback.']='Kort eller usikker tekst bruker reservespråket ditt.'

NB.update({'Choose how Skrivi Lytt reads, looks and starts.':'Velg hvordan Skrivi Lytt leser, ser ut og starter.', 'Reading':'Opplesing', 'This model is not ready. Open Settings → Models to download or verify it.':'Modellen er ikke klar. Åpne Innstillinger → Modeller for å laste ned eller kontrollere den.'})
