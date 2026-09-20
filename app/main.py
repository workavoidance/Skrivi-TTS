"""Skrivi Lytt reader: local text/selection input and a separate Windows tray app."""
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
from PySide6.QtGui import QAction,QActionGroup,QKeySequence,QShortcut,QCursor
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QDialog,QDoubleSpinBox,
 QFileDialog,QFormLayout,QFrame,QHBoxLayout,QLabel,QMenu,QMessageBox,QProgressBar,
 QPushButton,QTabWidget,QTextEdit,QTreeWidget,QTreeWidgetItem,QVBoxLayout,QWidget,QSystemTrayIcon)
from core import STORE_BUILD,runtime_executable,ocr_assets,DATA,ROOT,VERSION,KOKORO_VOICES,Library,catalog,defaults,read_json,write_json
from client import Client
from reader_core import load_preferences,choose_language,model_for_language
from screen_region import RegionOverlay
from activity_pill import ActivityPill
from i18n import tr,configure,translate_widgets
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
    ocr=Signal(int,str,str)
    stage=Signal(int,str)
    update_result=Signal(str)
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
        self.setWindowTitle('Skrivi Lytt');self.setWindowIcon(speech_icon())
        self.resize(820,730);self.setMinimumSize(720,630)
        self.library=Library();self.models=[m for m in catalog() if m['id'] in ('piper-talesyntese','kokoro-v1.0-onnx')];self.preferences=load_preferences()
        self.client=Client();self.cancel=threading.Event();self.busy=False;self.capturing=False
        self.player=WavePlayer();self.capture_generation=0
        self.region_overlay=None;self.ocr_cancel=threading.Event()
        self.worker=None;self.library_busy=False;self.library_cancel=threading.Event();self.exiting=False
        self.last_audio=None;self.last_result=None
        self.temp=tempfile.TemporaryDirectory(prefix='skrivi-tts-reader-')
        self.events=Events()
        self.events.status.connect(self.set_status);self.events.failure.connect(self.show_error)
        self.events.finished.connect(self.completed);self.events.selection.connect(self.selection_received)
        self.events.models.connect(self.refresh_models);self.events.library_done.connect(self.library_finished)
        self.events.ocr.connect(self.ocr_received)
        self.events.stage.connect(self.show_stage)
        self.events.update_result.connect(self.update_received)
        self.update_busy=False;self.activity_failed=False
        self.pill=ActivityPill();self.pill.cancelled.connect(self.stop)
        self.activity_screen=None
        self.escape_hotkeys=Hotkeys(self.stop,0x5313)
        if not preview:app.installNativeEventFilter(self.escape_hotkeys)
        self.build();self.build_tray()
        self.hotkeys=Hotkeys(self.hotkey_pressed)
        if not preview:
            app.installNativeEventFilter(self.hotkeys)
            try:self.hotkeys.register(self.preferences['hotkey'])
            except Exception as error:QTimer.singleShot(0,lambda e=str(error):self.show_error(e))
        self.region_hotkeys=Hotkeys(self.region_hotkey_pressed,0x5312)
        if not preview:
            app.installNativeEventFilter(self.region_hotkeys)
            try:self.region_hotkeys.register('Ctrl+Alt+Shift+Space')
            except Exception:QTimer.singleShot(0,lambda:self.show_error('Screen-region shortcut unavailable. Use Read screen region in the tray.'))
        self.restore_preferences();self.refresh_models();self.update_route();self.change_ui_language()
        if STORE_BUILD:
            self.startup.setEnabled(False);self.download_button.hide();self.import_button.hide();self.cancel_download.hide()
        self.tray.show() if not preview else None
        QShortcut(QKeySequence('Ctrl+Return'),self,activated=self.read_editor)
        QShortcut(QKeySequence('Escape'),self,activated=self.stop)
        if not preview:QTimer.singleShot(100,self.adopt_bundled)

    def build(self):
        outer=QVBoxLayout(self);outer.setContentsMargins(24,22,24,18);outer.setSpacing(14)
        header=QHBoxLayout();brand=QVBoxLayout()
        brand.addWidget(label('SKRIVI LYTT  /  TEXT TO SPEECH','eyebrow'))
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
        self.region_button=QPushButton('Read screen region');self.region_button.clicked.connect(self.capture_region);layout.addWidget(self.region_button)
        self.shortcut_hint=label('','secondary');layout.addWidget(self.shortcut_hint)
        layout.addWidget(label('Closing this window keeps Skrivi Lytt in the tray. Text is not saved.','secondary'))
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
        self.download_status=label('Two local models, kept through updates.','secondary');layout.addWidget(self.download_status)
        layout=QVBoxLayout(settings);layout.setContentsMargins(0,16,0,0);layout.setSpacing(12)
        box,contents=card(settings);layout.addWidget(box)
        contents.addWidget(label('Read from any application','sectionTitle'))
        form=QFormLayout();contents.addLayout(form)
        self.shortcut=QComboBox();self.shortcut.addItems([key for key in HOTKEYS if key!='Ctrl+Alt+Shift+Space']);form.addRow('Selected-text shortcut',self.shortcut)
        self.shortcut.currentTextChanged.connect(self.change_shortcut)
        self.fallback=QComboBox();self.fallback.addItem('Norwegian Bokmål','no');self.fallback.addItem('English','en');form.addRow('When detection is uncertain',self.fallback)
        self.fallback.currentIndexChanged.connect(self.save_preferences)
        contents.addWidget(label('Select text, then press the shortcut to read immediately. Press it again to stop. Automatic uses one voice for the whole selection.','secondary'))
        self.ui_language=QComboBox()
        for text,key in [('Automatic (Windows display language)','auto'),('English','en'),('Norsk bokmål','nb')]:self.ui_language.addItem(text,key)
        form.addRow('Interface language',self.ui_language);self.ui_language.currentIndexChanged.connect(self.change_ui_language)
        self.startup=QCheckBox('Start quietly in the tray when I sign in');self.startup.toggled.connect(self.change_startup);contents.addWidget(self.startup)
        if STORE_BUILD:
            manage=QPushButton('Manage startup in Windows Settings');manage.clicked.connect(lambda:os.startfile('ms-settings:startupapps'));contents.addWidget(manage)
        self.layout_mode=QComboBox();self.layout_mode.addItem('Paragraph / single column',6);self.layout_mode.addItem('Automatic page layout (columns)',3)
        form.addRow('Image layout',self.layout_mode);self.layout_mode.currentIndexChanged.connect(self.save_preferences)
        contents.addWidget(label('For columns, select the main text without shared headings or footers.','secondary'))
        layout.addStretch()
        layout.addWidget(label('Skrivi Lytt '+VERSION,'secondary'))
        layout.addWidget(label('Local reading. Part of the Skrivi family.','secondary'))
        links=QHBoxLayout();source=QPushButton('Project & updates');source.clicked.connect(lambda:os.startfile('https://github.com/workavoidance/Skrivi-TTS/releases'))
        library=QPushButton('Open model folder');library.clicked.connect(lambda:os.startfile(DATA/'models'))
        self.update_button=QPushButton('Check for updates');self.update_button.clicked.connect(self.check_updates)
        links.addWidget(self.update_button);links.addWidget(source);links.addWidget(library);links.addStretch();layout.addLayout(links)
        self.status_label=label('Ready.','secondary');outer.addWidget(self.status_label)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setMaximumHeight(4);self.progress.setTextVisible(False);self.progress.hide();outer.addWidget(self.progress)

    def build_tray(self):
        self.tray=QSystemTrayIcon(speech_icon(),self);self.tray.setToolTip('Skrivi Lytt · Read aloud')
        self.menu=QMenu();self.menu.addAction('Skrivi Lytt').setEnabled(False)
        self.tray_status=self.menu.addAction('Ready');self.tray_status.setEnabled(False)
        self.menu.addSeparator();self.menu.addAction('Open reader',self.open_reader)
        self.tray_read=self.menu.addAction('Read selected text',self.capture_selection)
        self.menu.addAction('Read screen region · Ctrl+Alt+Shift+Space',self.capture_region)
        self.tray_stop=self.menu.addAction('Stop reading',self.stop);self.tray_stop.setEnabled(False)
        language=self.menu.addMenu('Reading language');group=QActionGroup(self.menu);group.setExclusive(True);self.language_actions={}
        for key,name in LANGUAGES.items():
            action=language.addAction(name);action.setCheckable(True);group.addAction(action)
            action.triggered.connect(lambda checked,k=key:self.set_language(k));self.language_actions[key]=action
        self.menu.addAction('Voices & models',lambda:self.open_reader(1))
        self.menu.addAction('Check for updates',self.check_updates)
        self.menu.addAction('Settings',lambda:self.open_reader(2));self.menu.addSeparator();self.menu.addAction('Quit Skrivi Lytt',self.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda reason:self.open_reader() if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None)

    def restore_preferences(self):
        pairs=((self.language,self.preferences['language']),(self.voice,self.preferences['english_voice']),
               (self.fallback,self.preferences['fallback']),(self.layout_mode,self.preferences.get('ocr_layout',6)),(self.ui_language,self.preferences.get('ui_language','auto')))
        for widget,value in pairs:
            with QSignalBlocker(widget):widget.setCurrentIndex(max(0,widget.findData(value)))
        with QSignalBlocker(self.speed):self.speed.setValue(self.preferences['speed'])
        with QSignalBlocker(self.shortcut):self.shortcut.setCurrentText(self.preferences['hotkey'])
        with QSignalBlocker(self.startup):self.startup.setChecked(self.preferences['startup'])
        self.language_actions[self.preferences['language']].setChecked(True);self.update_hint()

    def save_preferences(self,*_):
        if not hasattr(self,'layout_mode'):return
        self.preferences.update(language=self.language.currentData(),english_voice=self.voice.currentData(),
            fallback=self.fallback.currentData(),speed=self.speed.value(),ocr_layout=self.layout_mode.currentData())
        if not self.preview:write_json(DATA/'reader-settings.json',self.preferences)
        self.update_route()

    def language_changed(self,*_):
        if not hasattr(self,'language_actions'):return
        key=self.language.currentData();self.language_actions[key].setChecked(True);self.save_preferences()

    def set_language(self,key):self.language.setCurrentIndex(self.language.findData(key))

    def change_ui_language(self,*_):
        if not hasattr(self,'ui_language') or not hasattr(self,'tray'):return
        choice=self.ui_language.currentData();self.preferences['ui_language']=choice;configure(choice)
        translate_widgets(self);translate_widgets(self.menu)
        self.text.setPlaceholderText(tr('Paste or type something to read…'));self.update_route();self.update_hint();self.refresh_models()
        if not self.preview:write_json(DATA/'reader-settings.json',self.preferences)

    def check_updates(self):
        if self.update_busy:return
        from core import STORE_BUILD
        if STORE_BUILD:os.startfile('ms-windows-store://downloadsandupdates');return
        self.update_busy=True;self.update_button.setEnabled(False);self.set_status(tr('Checking for updates…'))
        def work():
            try:
                from updates import latest
                version,newer=latest(VERSION)
                message=('Version '+version+' is available. Open Project & updates to download it.') if newer else tr('No newer stable release is available.')
            except Exception:message='Could not check for updates. Check your connection and try again.'
            self.events.update_result.emit(message)
        threading.Thread(target=work,daemon=True).start()

    def update_received(self,message):
        self.update_busy=False;self.update_button.setEnabled(True);self.set_status(message)
        if not self.isVisible():self.tray.showMessage('Skrivi Lytt',message)

    def change_shortcut(self,value):
        if not hasattr(self,'hotkeys'):return
        try:
            if not self.preview:self.hotkeys.register(value)
            self.preferences['hotkey']=value;self.save_preferences();self.update_hint()
        except Exception as error:
            with QSignalBlocker(self.shortcut):self.shortcut.setCurrentText(self.preferences['hotkey'])
            self.show_error(str(error))

    def update_hint(self):
        self.shortcut_hint.setText('Selected text: '+self.preferences['hotkey']+' · Screen region: Ctrl+Alt+Shift+Space')

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
        hint=' · short or uncertain text uses your fallback' if uncertain else ''
        self.route_label.setText(tr(LANGUAGES[language])+' · '+voice+hint)

    def sample(self):
        if self.text.toPlainText().strip():return
        self.text.setPlainText(SAMPLE)

    def read_editor(self):self.start_reading(self.text.toPlainText(),'Text box')

    def start_reading(self,text,source):
        if self.busy or self.capturing or self.exiting:return
        text=text.strip()
        if not text:self.show_error('Select some text, or type it into the reader first.');return
        if len(text)>30000:self.show_error('Please select a shorter passage (up to 30,000 characters).');return
        language,uncertain=choose_language(text,self.preferences['language'],self.preferences['fallback'])
        mid=model_for_language(language)
        model=next(m for m in self.models if m['id']==mid)
        if not self.library.ready(model):self.show_error('This model is not ready. Open Voices & models to download or verify it.');return
        settings=defaults(model['engine'])
        if model['engine']=='kokoro':settings.update(voice=self.preferences['english_voice'],speed=self.preferences['speed'])
        if model['engine']=='piper':settings['speed']=self.preferences['speed']
        if model['engine']=='chatterbox':settings['language']=language
        self.activity_failed=False
        self.busy=True;self.cancel=threading.Event();cancel=self.cancel
        self.capture_generation+=1;epoch=self.capture_generation
        self.begin_activity()
        self.show_stage(epoch,'generating')
        self.read_button.setEnabled(False);self.stop_button.setEnabled(True);self.tray_stop.setEnabled(True);self.progress.show()
        self.set_status('Preparing '+LANGUAGES[language]+' · '+model['name']+'…')
        target=Path(self.temp.name)/(uuid.uuid4().hex+'.wav')
        def work():
            result=None
            try:
                result=self.client.generate(dict(model=model,assets=str(self.library.path(model)),settings=settings,
                    text=text,output=str(target),voices=str(DATA/'voices'),vox_runtime=str(DATA/'runtimes/vox-0.8.32')),cancel,lambda stage:self.events.stage.emit(epoch,stage))
                if cancel.is_set():raise InterruptedError()
                self.events.stage.emit(epoch,'playing')
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
        self.busy=False;self.end_activity(keep_error=self.activity_failed);self.progress.hide();self.read_button.setEnabled(True);self.stop_button.setEnabled(False);self.tray_stop.setEnabled(False)
        if result:
            if self.last_audio and Path(self.last_audio).exists():Path(self.last_audio).unlink(missing_ok=True)
            self.last_result=result;self.last_audio=result['output'];self.save_button.setEnabled(True)
            self.set_status('Finished · %.1f seconds of audio · generated in %.2f seconds'%(result['audio_seconds'],result['generation_seconds']))
        elif self.cancel.is_set():self.set_status('Stopped.')
        if self.exiting:self.finish_quit()

    def stop(self):
        self.end_activity();self.cancel.set();self.ocr_cancel.set();self.player.stop();self.capture_generation+=1;self.capturing=False
        if self.region_overlay:self.region_overlay.abort();self.region_overlay=None
        if not self.busy:self.progress.hide();self.stop_button.setEnabled(False);self.tray_stop.setEnabled(False);self.read_button.setEnabled(True)
        if self.busy:self.set_status('Stopping…')

    def begin_activity(self):
        if self.activity_screen is None:self.activity_screen=self.app.screenAt(QCursor.pos()) or self.app.primaryScreen()
        if not self.preview:
            try:self.escape_hotkeys.register('Escape')
            except RuntimeError:pass

    def end_activity(self,keep_error=False):
        self.escape_hotkeys.close()
        if not keep_error:self.pill.hide()
        self.activity_screen=None

    def show_stage(self,epoch,stage):
        if self.exiting or epoch!=self.capture_generation or self.cancel.is_set():return
        titles={'starting':('Starting voice…','Getting the local voice engine ready.'),'loading':('Loading voice…','Kept ready for your next reading.'),'generating':('Preparing speech…',''),'playing':('Reading aloud','')}
        if stage not in titles:return
        title,detail=titles[stage];self.pill.present(title,detail,self.activity_screen);self.set_status(title)

    def set_status(self,text):
        self.status_label.setText(tr(text));self.tray_status.setText(text);self.tray.setToolTip('Skrivi Lytt · '+text)

    def show_error(self,text):
        self.activity_failed=True
        self.set_status(text)
        self.escape_hotkeys.close()
        self.pill.present('Could not read',text,self.activity_screen,active=False,error=True)
        if not self.isVisible() and not self.preview:self.tray.showMessage('Skrivi Lytt',text,QSystemTrayIcon.MessageIcon.Warning,6000)

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

    def region_hotkey_pressed(self):
        if self.busy or self.capturing:self.stop()
        else:self.capture_region()

    def capture_region(self):
        if self.busy or self.capturing or self.exiting:return
        runtime=runtime_executable('tesseract-5.5.2-v2','OCRWorker.exe')
        assets=ocr_assets()
        if not runtime.is_file() or not all((assets/(lang+'.traineddata')).is_file() for lang in ('nor','eng')):
            self.show_error('Screen reading needs the OCR update package. No files will be downloaded automatically.');return
        self.capturing=True;self.capture_generation+=1;epoch=self.capture_generation;self.begin_activity()
        self.pill.present('Select a screen region…','Drag around the text to read.',self.activity_screen)
        self.ocr_cancel=threading.Event();cancel=self.ocr_cancel
        screen=self.app.screenAt(QCursor.pos()) or self.app.primaryScreen()
        self.hide();self.stop_button.setEnabled(True);self.tray_stop.setEnabled(True);self.read_button.setEnabled(False)
        self.set_status('Select a paragraph or column. Escape cancels.')
        def select():
            if self.exiting or epoch!=self.capture_generation:return
            self.pill.hide()
            QTimer.singleShot(60,show_overlay)
        def show_overlay():
            if self.exiting or epoch!=self.capture_generation:return
            try:
                overlay=RegionOverlay(screen);self.region_overlay=overlay
                overlay.cancelled.connect(self.stop)
                overlay.selected.connect(lambda data:self.recognise_region(data,epoch,runtime,assets,cancel))
                overlay.show();overlay.raise_();overlay.activateWindow()
            except Exception as error:self.stop();self.show_error(str(error))
        QTimer.singleShot(250,select)

    def recognise_region(self,data,epoch,runtime,assets,cancel):
        self.region_overlay=None
        self.progress.show();self.pill.present('Recognising text…','On this device',self.activity_screen);self.set_status('Recognising text on this device…')
        layout=str(self.preferences.get('ocr_layout',6))
        def work():
            process=None
            try:
                process=subprocess.Popen([str(runtime),str(assets),layout],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
                deadline=time.monotonic()+30;first=True
                while True:
                    if cancel.is_set():raise InterruptedError()
                    if time.monotonic()>deadline:raise RuntimeError('Recognition took too long. Try a smaller region.')
                    try:
                        output,_=process.communicate(data if first else None,timeout=.1);break
                    except subprocess.TimeoutExpired:first=False
                result=json.loads(output.decode('utf-8'))
                if process.returncode or 'error' in result:raise RuntimeError(result.get('error','OCR worker failed.'))
                if not cancel.is_set():self.events.ocr.emit(epoch,result['text'],'')
            except InterruptedError:pass
            except Exception as error:
                if not cancel.is_set():self.events.ocr.emit(epoch,'',str(error))
            finally:
                if process and process.poll() is None:process.kill();process.wait()
        threading.Thread(target=work,daemon=True).start()

    def ocr_received(self,epoch,text,error):
        if self.exiting or epoch!=self.capture_generation:return
        self.capturing=False;self.progress.hide();self.read_button.setEnabled(True);self.stop_button.setEnabled(False);self.tray_stop.setEnabled(False)
        if error:self.show_error(error);return
        if not text.strip():self.show_error('No text found. Zoom in and select a paragraph or column.');return
        self.text.setPlainText(text);self.start_reading(text,'Screen region')

    def capture_selection(self):
        if self.busy or self.capturing or self.exiting:return
        self.capturing=True;self.capture_generation+=1;epoch=self.capture_generation;self.begin_activity()
        self.pill.present('Getting selected text…','',self.activity_screen);self.set_status('Reading selected text…')
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
                else:self.show_error('No selected text was available. Try copying it into the reader. For an image, use Read screen region.')
            QTimer.singleShot(60,collect)
        QTimer.singleShot(60,copy_when_released)

    def refresh_models(self):
        selected=self.model_table.currentItem();selected=selected.data(0,Qt.ItemDataRole.UserRole) if selected else None
        self.model_table.clear()
        for model in self.models:
            ready=self.library.ready(model)
            item=QTreeWidgetItem([model['name'],str(round(sum(f['bytes'] for f in model['files'])/1e6))+' MB',tr('Ready') if ready else tr('Not installed')])
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
        name,_=QFileDialog.getSaveFileName(self,'Save audio','Skrivi Lytt reading.wav','WAV audio (*.wav)')
        if name:shutil.copyfile(self.last_audio,name)

    def quit(self):
        self.exiting=True;self.library_cancel.set();self.stop();self.hide();self.tray.hide();self.hotkeys.close();self.region_hotkeys.close()
        if not self.busy:self.finish_quit()

    def finish_quit(self):
        if self.library_busy:QTimer.singleShot(100,self.finish_quit);return
        self.end_activity();self.pill.close()
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
    app=QApplication(sys.argv);app.setApplicationName('Skrivi TTS');app.setApplicationDisplayName('Skrivi Lytt');app.setOrganizationName('Skrivi')
    app.setQuitOnLastWindowClosed(False);app.setWindowIcon(speech_icon())
    socket=QLocalSocket();socket.connectToServer('SkriviTTS-reader-v1')
    if socket.waitForConnected(200):
        socket.write(b'open');socket.flush();socket.waitForBytesWritten(200);return
    server=QLocalServer();server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not server.listen('SkriviTTS-reader-v1'):raise RuntimeError('Skrivi Lytt is already starting.')
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
