"""Skrivi TTS reader: local text/selection input and a separate Windows tray app."""
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import winsound

from PySide6.QtCore import QMimeData,QObject,QTimer,Qt,Signal,QSignalBlocker
from PySide6.QtGui import QAction,QActionGroup,QKeySequence,QShortcut
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QDialog,QDoubleSpinBox,
 QFileDialog,QFormLayout,QFrame,QHBoxLayout,QLabel,QMenu,QMessageBox,QProgressBar,
 QPushButton,QTabWidget,QTextEdit,QTreeWidget,QTreeWidgetItem,QVBoxLayout,QWidget,QSystemTrayIcon)
from core import DATA,ROOT,VERSION,KOKORO_VOICES,Library,catalog,defaults,read_json,write_json
from client import Client
from reader_core import load_preferences,choose_language,model_for_language
from branding import speech_icon
from theme import application_stylesheet
from windows_reader import Hotkeys,HOTKEYS,user32,modifiers_released,copy_selection,set_startup,WavePlayer

SAMPLE='The rain had stopped by the time we reached the station. Sarah looked at the empty platform and smiled. We had missed the last train, but neither of us was in a hurry to go home.'
LANGUAGES={'auto':'Automatic','no':'Norwegian Bokmål','en':'English'}

class Events(QObject):
    status=Signal(str)
    failure=Signal(str)
    finished=Signal(object)
    selection=Signal(str,object)
    models=Signal()
    library_done=Signal()


def label(text,role=None):
    widget=QLabel(text);widget.setWordWrap(True)
    if role:widget.setProperty('uiRole',role)
    return widget

def card(parent):
    frame=QFrame(parent);frame.setProperty('uiRole','card')
    layout=QVBoxLayout(frame);layout.setContentsMargins(18,16,18,17);layout.setSpacing(10)
    return frame,layout

class Reader(QDialog):
    def __init__(self,app,preview=False):
        super().__init__()
        self.app=app;self.preview=preview
        self.setWindowTitle('Skrivi TTS');self.setWindowIcon(speech_icon())
        self.resize(820,730);self.setMinimumSize(720,630)
        self.library=Library();self.models=catalog();self.preferences=load_preferences()
        self.client=Client();self.cancel=threading.Event();self.busy=False;self.capturing=False
        self.player=WavePlayer();self.capture_generation=0
        self.worker=None;self.library_busy=False;self.library_cancel=threading.Event();self.exiting=False
        self.last_audio=None;self.last_result=None
        self.temp=tempfile.TemporaryDirectory(prefix='skrivi-tts-reader-')
        self.events=Events()
        self.events.status.connect(self.set_status);self.events.failure.connect(self.show_error)
        self.events.finished.connect(self.completed);self.events.selection.connect(self.selection_received)
        self.events.models.connect(self.refresh_models);self.events.library_done.connect(self.library_finished)
        self.build();self.build_tray()
        self.hotkeys=Hotkeys(self.hotkey_pressed)
        if not preview:
            app.installNativeEventFilter(self.hotkeys)
            try:self.hotkeys.register(self.preferences['hotkey'])
            except Exception as error:QTimer.singleShot(0,lambda e=str(error):self.show_error(e))
        self.restore_preferences();self.refresh_models();self.update_route()
        self.tray.show() if not preview else None
        QShortcut(QKeySequence('Ctrl+Return'),self,activated=self.read_editor)
        QShortcut(QKeySequence('Escape'),self,activated=self.stop)
        if not preview:QTimer.singleShot(100,self.adopt_bundled)

    def build(self):
        outer=QVBoxLayout(self);outer.setContentsMargins(24,22,24,18);outer.setSpacing(14)
        header=QHBoxLayout();brand=QVBoxLayout()
        brand.addWidget(label('SKRIVI  /  TEXT TO SPEECH','eyebrow'))
        brand.addWidget(label('Read aloud','windowTitle'))
        brand.addWidget(label('A familiar voice for the words in front of you.','secondary'))
        header.addLayout(brand,1)
        self.badge=label('On this device','statusBadge');header.addWidget(self.badge,0,Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)
        self.tabs=QTabWidget();outer.addWidget(self.tabs,1)
        read=QWidget();voices=QWidget();settings=QWidget()
        for widget,name in ((read,'Read'),(voices,'Voices && models'),(settings,'Settings')):
            widget.setObjectName('settingsPage');self.tabs.addTab(widget,name)
        layout=QVBoxLayout(read);layout.setContentsMargins(0,16,0,0);layout.setSpacing(12)
        box,contents=card(read);layout.addWidget(box)
        row=QHBoxLayout();row.addWidget(label('Reading language','sectionTitle'));row.addStretch()
        self.language=QComboBox()
        for key,name in LANGUAGES.items():self.language.addItem(name,key)
        self.language.setAccessibleName('Reading language');row.addWidget(self.language)
        contents.addLayout(row)
        self.route_label=label('','secondary');contents.addWidget(self.route_label)
        self.language.currentIndexChanged.connect(self.language_changed)
        self.text=QTextEdit();self.text.setAcceptRichText(False)
        self.text.setPlaceholderText('Paste or type something to read…')
        self.text.setAccessibleName('Text to read');self.text.setMinimumHeight(200)
        self.text.textChanged.connect(self.update_route);layout.addWidget(self.text,1)
        buttons=QHBoxLayout()
        self.read_button=QPushButton('Read aloud');self.read_button.setProperty('uiRole','primary');self.read_button.clicked.connect(self.read_editor)
        self.stop_button=QPushButton('Stop');self.stop_button.clicked.connect(self.stop);self.stop_button.setEnabled(False)
        self.sample_button=QPushButton('Try a sample');self.sample_button.clicked.connect(self.sample)
        self.save_button=QPushButton('Save audio…');self.save_button.clicked.connect(self.save_audio);self.save_button.setEnabled(False)
        for button in (self.read_button,self.stop_button,self.sample_button):buttons.addWidget(button)
        buttons.addStretch();buttons.addWidget(self.save_button);layout.addLayout(buttons)
        self.shortcut_hint=label('','secondary');layout.addWidget(self.shortcut_hint)
        layout.addWidget(label('Closing this window keeps Skrivi TTS in the tray. Text is not saved.','secondary'))
        layout=QVBoxLayout(voices);layout.setContentsMargins(0,16,0,0);layout.setSpacing(12)
        box,contents=card(voices);layout.addWidget(box)
        contents.addWidget(label('Your everyday voices','sectionTitle'))
        form=QFormLayout();contents.addLayout(form)
        form.addRow('Norwegian Bokmål',label('Piper Talesyntese · male'))
        self.voice=QComboBox()
        for key,name in KOKORO_VOICES.items():self.voice.addItem(name,key)
        form.addRow('English',self.voice)
        self.speed=QDoubleSpinBox();self.speed.setRange(.5,2);self.speed.setSingleStep(.1);self.speed.setDecimals(2);self.speed.setSuffix(' ×');self.speed.setValue(1)
        form.addRow('Reading speed',self.speed)
        contents.addWidget(label('Both models are included. English voices share one download.','secondary'))
        self.voice.currentIndexChanged.connect(self.save_preferences);self.speed.valueChanged.connect(self.save_preferences)
        self.model_table=QTreeWidget();self.model_table.setColumnCount(3);self.model_table.setHeaderLabels(['Model','Size','Availability']);self.model_table.setRootIsDecorated(False)
        self.model_table.setColumnWidth(0,325);self.model_table.setColumnWidth(1,85);layout.addWidget(self.model_table,1)
        row=QHBoxLayout();self.download_button=QPushButton('Download / verify');self.download_button.clicked.connect(lambda:self.model_action(False))
        self.import_button=QPushButton('Import existing…');self.import_button.clicked.connect(lambda:self.model_action(True))
        self.cancel_download=QPushButton('Cancel download');self.cancel_download.setEnabled(False);self.cancel_download.clicked.connect(self.library_cancel.set)
        for widget in (self.download_button,self.import_button,self.cancel_download):row.addWidget(widget)
        layout.addLayout(row)
        self.download_status=label('Optional models are downloaded once and kept through updates.','secondary');layout.addWidget(self.download_status)
        layout=QVBoxLayout(settings);layout.setContentsMargins(0,16,0,0);layout.setSpacing(12)
        box,contents=card(settings);layout.addWidget(box)
        contents.addWidget(label('Read from any application','sectionTitle'))
        form=QFormLayout();contents.addLayout(form)
        self.shortcut=QComboBox();self.shortcut.addItems(HOTKEYS);form.addRow('Selected-text shortcut',self.shortcut)
        self.shortcut.currentTextChanged.connect(self.change_shortcut)
        self.fallback=QComboBox();self.fallback.addItem('Norwegian Bokmål','no');self.fallback.addItem('English','en');form.addRow('When detection is uncertain',self.fallback)
        self.fallback.currentIndexChanged.connect(self.save_preferences)
        contents.addWidget(label('Select text, then press the shortcut to read immediately. Press it again to stop. Automatic uses one voice for the whole selection.','secondary'))
        self.startup=QCheckBox('Start quietly in the tray when I sign in');self.startup.toggled.connect(self.change_startup);contents.addWidget(self.startup)
        box,contents=card(settings);layout.addWidget(box)
        contents.addWidget(label('Additional models','sectionTitle'))
        self.override=QComboBox();self.override.addItem('Recommended voice for each language','')
        for model in self.models:
            if model['id'] not in ('kokoro-v1.0-onnx','piper-talesyntese'):self.override.addItem(model['name'],model['id'])
        contents.addWidget(self.override);self.override.currentIndexChanged.connect(self.save_preferences)
        contents.addWidget(label('Optional models are for comparison. Reading speed applies to Kokoro and Piper.','secondary'))
        layout.addStretch()
        layout.addWidget(label('Skrivi TTS '+VERSION+' · Local speech, separate from Skrivi dictation.','secondary'))
        links=QHBoxLayout();source=QPushButton('Project & updates');source.clicked.connect(lambda:os.startfile('https://github.com/workavoidance/Skrivi-TTS/releases'))
        library=QPushButton('Open model folder');library.clicked.connect(lambda:os.startfile(DATA/'models'))
        links.addWidget(source);links.addWidget(library);links.addStretch();layout.addLayout(links)
        self.status_label=label('Ready.','secondary');outer.addWidget(self.status_label)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setMaximumHeight(4);self.progress.setTextVisible(False);self.progress.hide();outer.addWidget(self.progress)

    def build_tray(self):
        self.tray=QSystemTrayIcon(speech_icon(),self);self.tray.setToolTip('Skrivi TTS · Read aloud')
        self.menu=QMenu();self.menu.addAction('Skrivi TTS').setEnabled(False)
        self.tray_status=self.menu.addAction('Ready');self.tray_status.setEnabled(False)
        self.menu.addSeparator();self.menu.addAction('Open reader',self.open_reader)
        self.tray_read=self.menu.addAction('Read selected text',self.capture_selection)
        self.tray_stop=self.menu.addAction('Stop reading',self.stop);self.tray_stop.setEnabled(False)
        language=self.menu.addMenu('Reading language');group=QActionGroup(self.menu);group.setExclusive(True);self.language_actions={}
        for key,name in LANGUAGES.items():
            action=language.addAction(name);action.setCheckable(True);group.addAction(action)
            action.triggered.connect(lambda checked,k=key:self.set_language(k));self.language_actions[key]=action
        self.menu.addAction('Voices & models',lambda:self.open_reader(1))
        self.menu.addAction('Settings',lambda:self.open_reader(2));self.menu.addSeparator();self.menu.addAction('Quit Skrivi TTS',self.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda reason:self.open_reader() if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None)

    def restore_preferences(self):
        pairs=((self.language,self.preferences['language']),(self.voice,self.preferences['english_voice']),
               (self.fallback,self.preferences['fallback']),(self.override,self.preferences['model_override']))
        for widget,value in pairs:
            with QSignalBlocker(widget):widget.setCurrentIndex(max(0,widget.findData(value)))
        with QSignalBlocker(self.speed):self.speed.setValue(self.preferences['speed'])
        with QSignalBlocker(self.shortcut):self.shortcut.setCurrentText(self.preferences['hotkey'])
        with QSignalBlocker(self.startup):self.startup.setChecked(self.preferences['startup'])
        self.language_actions[self.preferences['language']].setChecked(True);self.update_hint()

    def save_preferences(self,*_):
        if not hasattr(self,'override'):return
        self.preferences.update(language=self.language.currentData(),english_voice=self.voice.currentData(),
            fallback=self.fallback.currentData(),speed=self.speed.value(),model_override=self.override.currentData())
        if not self.preview:write_json(DATA/'reader-settings.json',self.preferences)
        self.update_route()

    def language_changed(self,*_):
        if not hasattr(self,'language_actions'):return
        key=self.language.currentData();self.language_actions[key].setChecked(True);self.save_preferences()

    def set_language(self,key):self.language.setCurrentIndex(self.language.findData(key))

    def change_shortcut(self,value):
        if not hasattr(self,'hotkeys'):return
        try:
            if not self.preview:self.hotkeys.register(value)
            self.preferences['hotkey']=value;self.save_preferences();self.update_hint()
        except Exception as error:
            with QSignalBlocker(self.shortcut):self.shortcut.setCurrentText(self.preferences['hotkey'])
            self.show_error(str(error))

    def update_hint(self):
        self.shortcut_hint.setText('Selected text: '+self.preferences['hotkey']+' · Here: Ctrl + Enter · Stop: press the shortcut again')

    def change_startup(self,checked):
        try:
            if not self.preview:set_startup(checked)
            self.preferences['startup']=checked;self.save_preferences()
        except Exception as error:
            with QSignalBlocker(self.startup):self.startup.setChecked(not checked)
            self.show_error(str(error))

    def update_route(self):
        if not hasattr(self,'text'):return
        language,uncertain=choose_language(self.text.toPlainText(),self.preferences['language'],self.preferences['fallback'])
        voice=KOKORO_VOICES[self.preferences['english_voice']].split(' — ')[0] if language=='en' else 'Talesyntese'
        override=self.preferences.get('model_override')
        if override:voice=next((m['name'] for m in self.models if m['id']==override),voice)
        hint=' · short or uncertain text uses your fallback' if uncertain else ''
        self.route_label.setText(LANGUAGES[language]+' · '+voice+hint)

    def sample(self):
        if self.text.toPlainText().strip():return
        self.text.setPlainText(SAMPLE)

    def read_editor(self):self.start_reading(self.text.toPlainText(),'Text box')

    def start_reading(self,text,source):
        if self.busy or self.exiting:return
        text=text.strip()
        if not text:self.show_error('Select some text, or type it into the reader first.');return
        if len(text)>30000:self.show_error('Please select a shorter passage (up to 30,000 characters).');return
        language,uncertain=choose_language(text,self.preferences['language'],self.preferences['fallback'])
        mid=self.preferences.get('model_override') or model_for_language(language)
        model=next(m for m in self.models if m['id']==mid)
        if not self.library.ready(model):self.show_error('This model is not ready. Open Voices & models to download or verify it.');return
        settings=defaults(model['engine'])
        if model['engine']=='kokoro':settings.update(voice=self.preferences['english_voice'],speed=self.preferences['speed'])
        if model['engine']=='piper':settings['speed']=self.preferences['speed']
        if model['engine']=='chatterbox':settings['language']=language
        self.busy=True;self.cancel=threading.Event();cancel=self.cancel
        self.read_button.setEnabled(False);self.stop_button.setEnabled(True);self.tray_stop.setEnabled(True);self.progress.show()
        self.set_status('Preparing '+LANGUAGES[language]+' · '+model['name']+'…')
        target=Path(self.temp.name)/(uuid.uuid4().hex+'.wav')
        def work():
            result=None
            try:
                result=self.client.generate(dict(model=model,assets=str(self.library.path(model)),settings=settings,
                    text=text,output=str(target),voices=str(DATA/'voices'),vox_runtime=str(DATA/'runtimes/vox-0.8.32')),cancel)
                if cancel.is_set():raise InterruptedError()
                self.events.status.emit('Reading '+LANGUAGES[language]+' · '+model['name'])
                if not cancel.is_set():self.player.play(target,cancel)
                if not cancel.is_set():result.update(source=source,output=str(target))
                else:result=None
            except InterruptedError:pass
            except Exception as error:
                if not cancel.is_set():self.events.failure.emit(str(error))
            finally:
                self.events.finished.emit(result if not cancel.is_set() else None)
        self.worker=threading.Thread(target=work,daemon=True);self.worker.start()

    def completed(self,result):
        self.busy=False;self.progress.hide();self.read_button.setEnabled(True);self.stop_button.setEnabled(False);self.tray_stop.setEnabled(False)
        if result:
            if self.last_audio and Path(self.last_audio).exists():Path(self.last_audio).unlink(missing_ok=True)
            self.last_result=result;self.last_audio=result['output'];self.save_button.setEnabled(True)
            self.set_status('Finished · %.1f seconds of audio · generated in %.2f seconds'%(result['audio_seconds'],result['generation_seconds']))
        elif self.cancel.is_set():self.set_status('Stopped.')
        if self.exiting:self.finish_quit()

    def stop(self):
        self.cancel.set();self.player.stop();self.capture_generation+=1;self.capturing=False
        if self.busy:self.set_status('Stopping…')

    def set_status(self,text):
        self.status_label.setText(text);self.tray_status.setText(text);self.tray.setToolTip('Skrivi TTS · '+text)

    def show_error(self,text):
        self.set_status(text)
        if not self.isVisible() and not self.preview:self.tray.showMessage('Skrivi TTS',text,QSystemTrayIcon.MessageIcon.Warning,6000)

    def open_reader(self,index=0):
        if isinstance(index,int):self.tabs.setCurrentIndex(index)
        self.showNormal();self.raise_();self.activateWindow()

    def closeEvent(self,event):
        if self.preview:event.accept();return
        event.ignore();self.hide()

    def hotkey_pressed(self):
        if self.busy or self.capturing:self.stop()
        else:
            if self.isActiveWindow():self.read_editor()
            else:self.capture_selection()

    def capture_selection(self):
        if self.busy or self.capturing or self.exiting:return
        self.capturing=True;self.capture_generation+=1;epoch=self.capture_generation;self.set_status('Reading selected text…')
        foreground=user32.GetForegroundWindow()
        def capture():
            text=''
            try:
                result=subprocess.run([str(ROOT/'native/Selection.exe')],capture_output=True,
                    text=True,encoding='utf-8',timeout=2,creationflags=subprocess.CREATE_NO_WINDOW)
                text=result.stdout.strip()
            except Exception:pass
            self.events.selection.emit(text,(foreground,epoch))
        threading.Thread(target=capture,daemon=True).start()

    def selection_received(self,text,context):
        foreground,epoch=context
        if self.exiting or epoch!=self.capture_generation:return
        if user32.GetForegroundWindow()!=foreground:
            self.capturing=False;self.show_error("Selection changed. Try the shortcut again.");return
        if text:
            self.capturing=False;self.start_reading(text,'Selection');return
        # Clipboard fallback is local, preserves MIME formats, and never reads stale text.
        deadline=time.monotonic()+1.2
        def copy_when_released():
            if self.exiting or epoch!=self.capture_generation:return
            if user32.GetForegroundWindow()!=foreground:
                self.capturing=False;self.show_error('Selection changed. Select the text and press the shortcut again.');return
            if not modifiers_released():
                if time.monotonic()<deadline:QTimer.singleShot(40,copy_when_released);return
                self.capturing=False;self.show_error('Release the shortcut keys, then try again.');return
            clipboard=self.app.clipboard();old=clipboard.mimeData();saved=QMimeData()
            for fmt in old.formats():saved.setData(fmt,old.data(fmt))
            sequence=user32.GetClipboardSequenceNumber()
            try:copy_selection()
            except Exception as error:self.capturing=False;self.show_error(str(error));return
            expires=time.monotonic()+1.2
            def collect():
                current=user32.GetClipboardSequenceNumber()
                if current==sequence and time.monotonic()<expires:QTimer.singleShot(40,collect);return
                copied=clipboard.text() if current!=sequence else ''
                if current!=sequence and user32.GetClipboardSequenceNumber()==current:clipboard.setMimeData(saved)
                self.capturing=False
                if self.exiting or epoch!=self.capture_generation:return
                if copied.strip():self.start_reading(copied,'Selection')
                else:self.show_error('No selected text was available. Try copying it into the reader. Images are not supported yet.')
            QTimer.singleShot(60,collect)
        QTimer.singleShot(60,copy_when_released)

    def refresh_models(self):
        selected=self.model_table.currentItem();selected=selected.data(0,Qt.ItemDataRole.UserRole) if selected else None
        self.model_table.clear()
        for model in self.models:
            ready=self.library.ready(model)
            item=QTreeWidgetItem([model['name'],str(round(sum(f['bytes'] for f in model['files'])/1e6))+' MB','Ready' if ready else 'Not installed'])
            item.setData(0,Qt.ItemDataRole.UserRole,model['id']);self.model_table.addTopLevelItem(item)
            if model['id']==selected:self.model_table.setCurrentItem(item)
        if not self.model_table.currentItem():self.model_table.setCurrentItem(self.model_table.topLevelItem(0))

    def adopt_bundled(self):
        if self.library_busy:return
        self.library_busy=True
        def work():
            try:
                for model in self.models:
                    if model['id'] in ('kokoro-v1.0-onnx','piper-talesyntese') and not self.library.ready(model):
                        path=DATA/'models'/model['id']
                        if all((path/f['path']).exists() for f in model['files']):self.library.register(model,path)
                self.events.models.emit()
            except Exception as error:self.events.failure.emit(str(error))
            finally:self.events.library_done.emit()
        threading.Thread(target=work,daemon=True).start()

    def model_action(self,importing):
        if self.library_busy or self.busy:return
        selected=self.model_table.currentItem()
        if not selected:return
        model=next(m for m in self.models if m['id']==selected.data(0,Qt.ItemDataRole.UserRole))
        source=QFileDialog.getExistingDirectory(self,'Import existing model') if importing else None
        if importing and not source:return
        self.library_busy=True;self.library_cancel.clear();self.download_button.setEnabled(False);self.import_button.setEnabled(False);self.cancel_download.setEnabled(True)
        def work():
            try:
                self.library.install(model,lambda value:self.events.status.emit(value),self.library_cancel,source)
                self.events.models.emit();self.events.status.emit('Model ready. It will be reused by future updates.')
            except InterruptedError:self.events.status.emit('Download cancelled.')
            except Exception as error:self.events.failure.emit(str(error))
            finally:self.events.library_done.emit()
        threading.Thread(target=work,daemon=True).start()

    def library_finished(self):
        self.library_busy=False;self.download_button.setEnabled(True);self.import_button.setEnabled(True);self.cancel_download.setEnabled(False)

    def save_audio(self):
        if not self.last_audio:return
        name,_=QFileDialog.getSaveFileName(self,'Save audio','Skrivi reading.wav','WAV audio (*.wav)')
        if name:shutil.copyfile(self.last_audio,name)

    def quit(self):
        self.exiting=True;self.library_cancel.set();self.stop();self.hide();self.tray.hide();self.hotkeys.close()
        if not self.busy:self.finish_quit()

    def finish_quit(self):
        if self.library_busy:QTimer.singleShot(100,self.finish_quit);return
        self.client.stop()
        temporary=Path(self.temp.name).resolve()
        if temporary.parent!=Path(tempfile.gettempdir()).resolve() or not temporary.name.startswith('skrivi-tts-reader-'):
            raise RuntimeError('Unexpected temporary audio directory')
        self.temp.cleanup();self.app.quit()


def main():
    if '--check-startup' in sys.argv:
        app=QApplication([])
        widget=QTextEdit();widget.setPlainText('A packaged reader startup check.')
        assert not speech_icon().isNull()
        assert choose_language('The rain had stopped by the time we reached the station.')[0]=='en'
        return
    if '--register-bundled' in sys.argv:
        library=Library()
        for model in catalog():
            if model['id'] in ('kokoro-v1.0-onnx','piper-talesyntese'):library.register(model,DATA/'models'/model['id'])
        return
    # A second launch asks the existing reader to show itself rather than taking its hotkey.
    from PySide6.QtNetwork import QLocalServer,QLocalSocket
    app=QApplication(sys.argv);app.setApplicationName('Skrivi TTS');app.setOrganizationName('Skrivi')
    app.setQuitOnLastWindowClosed(False);app.setWindowIcon(speech_icon())
    socket=QLocalSocket();socket.connectToServer('SkriviTTS-reader-v1')
    if socket.waitForConnected(200):
        socket.write(b'open');socket.flush();socket.waitForBytesWritten(200);return
    server=QLocalServer();server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not server.listen('SkriviTTS-reader-v1'):raise RuntimeError('Skrivi TTS is already starting.')
    app.setStyleSheet(application_stylesheet(app.palette()))
    app.paletteChanged.connect(lambda palette:app.setStyleSheet(application_stylesheet(palette)))
    window=Reader(app)
    def activate():
        connection=server.nextPendingConnection()
        if connection:connection.disconnectFromServer();connection.deleteLater()
        window.open_reader()
    server.newConnection.connect(activate)
    if '--tray' not in sys.argv:window.show()
    app.aboutToQuit.connect(window.hotkeys.close)
    sys.exit(app.exec())

if __name__=='__main__':main()
