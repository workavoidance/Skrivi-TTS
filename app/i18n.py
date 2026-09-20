"""Small English/Bokmal UI catalogue; speech language remains independent."""
import ctypes
LANGUAGE='en'
NB={
'Read aloud':'Les høyt','Read':'Les','Voices && models':'Stemmer og modeller','Voices & models':'Stemmer og modeller','Settings':'Innstillinger',
'On this device':'På denne enheten','Reading language':'Lesespråk','Automatic':'Automatisk','English':'Engelsk','Norwegian Bokmål':'Norsk bokmål',
'Your everyday voices':'Dine stemmer','Reading speed':'Lesehastighet','Stop':'Stopp','Try a sample':'Prøv en eksempeltekst','Save audio…':'Lagre lyd…',
'Read screen region':'Les et skjermområde','Read selected text':'Les merket tekst','Open reader':'Åpne leseren','Stop reading':'Stopp opplesing','Quit Skrivi TTS':'Avslutt Skrivi TTS',
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
'A familiar voice for the words in front of you.':'En kjent stemme for ordene foran deg.','SKRIVI  /  TEXT TO SPEECH':'SKRIVI  /  TEKST TIL TALE',
'Paste or type something to read…':'Lim inn eller skriv noe som skal leses…','Text to read':'Tekst som skal leses',
'Closing this window keeps Skrivi TTS in the tray. Text is not saved.':'Lukker du vinduet, fortsetter Skrivi TTS i systemstatusfeltet. Teksten lagres ikke.',
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
