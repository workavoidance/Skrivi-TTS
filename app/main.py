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
        self._saving_ready=False
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
            try:self.region_hotkeys.register(self.preferences['region_hotkey'])
            except Exception:QTimer.singleShot(0,lambda:self.show_error('Screen-region shortcut unavailable. Use Read screen region in the tray.'))
        self.restore_preferences();self.refresh_models();self.update_route();self.change_ui_language()
        self._saving_ready=True
        if STORE_BUILD:
            self.startup.setEnabled(False);self.download_button.hide();self.import_button.hide();self.cancel_download.hide()
        self.tray.show() if not preview else None
        QShortcut(QKeySequence('Ctrl+Return'),self,activated=self.read_editor)
        QShortcut(QKeySequence('Escape'),self,activated=self.stop)
        if not preview:QTimer.singleShot(100,self.adopt_bundled)

    def build(self):
        from family_ui import build_reader
        build_reader(self)

    def open_settings(self, *_):
        self.settings_dialog.showNormal();self.settings_dialog.raise_();self.settings_dialog.activateWindow()

    def verify_models(self):
        if self.library_busy:return
        self.library_busy=True
        def work():
            try:
                for model in self.models:
                    from core import sha256
                    path=self.library.path(model)
                    for item in model['files']:
                        if sha256(path/item['path'])!=item['sha256']:
                            raise ValueError('Model verification failed. Locate existing files or download the model again.')
                self.events.status.emit('Files verified.')
            except Exception as error:self.events.failure.emit(str(error))
            finally:self.events.library_done.emit()
        threading.Thread(target=work,daemon=True).start()

    def build_tray(self):
        self.tray=QSystemTrayIcon(speech_icon(),self);self.tray.setToolTip('Skrivi Lytt · Read aloud')
        self.menu=QMenu();self.menu.addAction('Skrivi Lytt').setEnabled(False)
        self.tray_status=self.menu.addAction('Ready');self.tray_status.setEnabled(False)
        self.menu.addSeparator();self.menu.addAction('Open Skrivi Lytt',self.open_reader)
        self.tray_read=self.menu.addAction('Read selected text',self.capture_selection)
        self.tray_region=self.menu.addAction('Read screen region',self.capture_region)
        self.tray_stop=self.menu.addAction('Stop reading',self.stop);self.tray_stop.setEnabled(False)
        language=self.menu.addMenu('Reading language');group=QActionGroup(self.menu);group.setExclusive(True);self.language_actions={}
        for key,name in LANGUAGES.items():
            action=language.addAction(name);action.setCheckable(True);group.addAction(action)
            action.triggered.connect(lambda checked,k=key:self.set_language(k));self.language_actions[key]=action
        self.menu.addSeparator()
        self.menu.addAction('Settings',self.open_settings)
        self.menu.addAction('Help',lambda:os.startfile('https://skrivi.no/help/'))
        self.menu.addAction('Give feedback',lambda:os.startfile('https://github.com/workavoidance/Skrivi-TTS/issues'))
        self.menu.addAction('Check for updates',self.check_updates)
        self.menu.addSeparator();self.menu.addAction('Quit Skrivi Lytt',self.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(lambda reason:self.open_reader() if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None)

    def restore_preferences(self):
        pairs=((self.language,self.preferences['language']),(self.voice,self.preferences['english_voice']),
               (self.fallback,self.preferences['fallback']),(self.layout_mode,self.preferences.get('ocr_layout',6)),(self.ui_language,self.preferences.get('ui_language','auto')))
        for widget,value in pairs:
            with QSignalBlocker(widget):widget.setCurrentIndex(max(0,widget.findData(value)))
        with QSignalBlocker(self.speed):self.speed.setValue(self.preferences['speed'])
        with QSignalBlocker(self.startup):self.startup.setChecked(self.preferences['startup'])
        with QSignalBlocker(self.overlay):self.overlay.setChecked(self.preferences['overlay_enabled'])
        self.pill.enabled=self.preferences['overlay_enabled']
        self.language_actions[self.preferences['language']].setChecked(True);self.update_hint()

    def persist_preferences(self, updated):
        if not self._saving_ready:return False
        try:
            if not self.preview:write_json(DATA/'reader-settings.json',updated)
        except OSError:
            self.restore_preferences()
            self.settings_error.setText(tr('Settings could not be saved. Previous settings remain active.'));self.settings_error.show()
            self.show_error('Settings could not be saved. Previous settings remain active.')
            return False
        self.preferences=updated
        self.settings_error.hide()
        return True

    def save_preferences(self,*_):
        if not self._saving_ready:return
        updated=dict(self.preferences,language=self.language.currentData(),english_voice=self.voice.currentData(),
            fallback=self.fallback.currentData(),speed=self.speed.value(),ocr_layout=self.layout_mode.currentData(),overlay_enabled=self.overlay.isChecked())
        if self.persist_preferences(updated):
            self.pill.enabled=updated['overlay_enabled']
            if not self.pill.enabled:self.pill.hide()
        self.update_route()

    def language_changed(self,*_):
        if not hasattr(self,'language_actions'):return
        key=self.language.currentData();self.language_actions[key].setChecked(True);self.save_preferences()

    def set_language(self,key):self.language.setCurrentIndex(self.language.findData(key))

    def change_ui_language(self,*_):
        if not hasattr(self,'ui_language') or not hasattr(self,'tray'):return
        choice=self.ui_language.currentData()
        if self._saving_ready and not self.persist_preferences(dict(self.preferences,ui_language=choice)):return
        configure(choice)
        translate_widgets(self);translate_widgets(self.menu)
        self.settings_dialog.setWindowTitle("Skrivi Lytt · "+tr("Settings"))
        self.text.setPlaceholderText(tr('Paste or type something to read…'));self.update_route();self.update_hint();self.refresh_models()
        # Preference writes go through persist_preferences for safe rollback.

    def check_updates(self):
        from update_dialog import UpdateDialog
        if not hasattr(self,'update_dialog'):self.update_dialog=UpdateDialog(self.settings_dialog)
        self.update_dialog.check()

    def change_shortcut(self,value):
        self.apply_shortcut('hotkey',value,self.hotkeys)

    def change_region_shortcut(self,value):
        self.apply_shortcut('region_hotkey',value,self.region_hotkeys)

    def apply_shortcut(self,key,value,owner):
        other='region_hotkey' if key=='hotkey' else 'hotkey'
        from shortcut_keys import shortcut_parts
        old=self.preferences[key]
        try:
            if shortcut_parts(value)==shortcut_parts(self.preferences[other]):raise ValueError('Choose different shortcuts for selected text and screen regions.')
            if not self.preview:owner.register(value)
            if not self.persist_preferences(dict(self.preferences,**{key:value})):
                if not self.preview:owner.register(old)
            self.update_hint()
        except Exception as error:
            self.settings_error.setText(tr(str(error)));self.settings_error.show()
            self.show_error(str(error))

    def update_hint(self):
        selected=self.preferences['hotkey'];region=self.preferences['region_hotkey']
        self.shortcut_hint.setText(tr('Selected-text shortcut')+': '+selected+' · '+tr('Screen-region shortcut')+': '+region)
        self.shortcut_label.setText(selected);self.region_shortcut_label.setText(region)
        self.tray_region.setText(tr('Read screen region')+' · '+region)
        self.tray_read.setText(tr('Read selected text')+' · '+selected)

    def change_startup(self,checked):
        previous=self.preferences['startup']
        try:
            if not self.preview:set_startup(checked)
            if not self.persist_preferences(dict(self.preferences,startup=checked)):
                if not self.preview:set_startup(previous)
        except Exception as error:
            with QSignalBlocker(self.startup):self.startup.setChecked(previous)
            self.show_error(str(error))

    def update_route(self):
        if not hasattr(self,'text'):return
        language,uncertain=choose_language(self.text.toPlainText(),self.preferences['language'],self.preferences['fallback'])
        voice=KOKORO_VOICES[self.preferences['english_voice']].split(' — ')[0] if language=='en' else 'Talesyntese'
        hint=' · '+tr('Short or uncertain text uses your fallback.') if uncertain else ''
        self.route_label.setText(tr(LANGUAGES[language])+' · '+voice+hint)

    def sample(self):
        if self.text.toPlainText().strip():return
        self.text.setPlainText(SAMPLE)

    def read_editor(self):
        self.retry_action=self.read_editor;self.error_actions.hide();self.error_detail.hide()
        self.start_reading(self.text.toPlainText(),'Text box')

    def start_reading(self,text,source):
        if self.busy or self.capturing or self.exiting:return
        text=text.strip()
        if not text:self.show_error('Select some text, or type it into the reader first.');return
        if len(text)>30000:self.show_error('Please select a shorter passage (up to 30,000 characters).');return
        language,uncertain=choose_language(text,self.preferences['language'],self.preferences['fallback'])
        mid=model_for_language(language)
        model=next(m for m in self.models if m['id']==mid)
        if not self.library.ready(model):self.show_error('This model is not ready. Open Settings → Models to download or verify it.');return
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
        self.set_status(tr('Preparing speech…')+' · '+tr(LANGUAGES[language]))
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
            self.set_status('Finished.')
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
        self.status_label.setText(tr(text));self.tray_status.setText(tr(text));self.tray.setToolTip('Skrivi Lytt · '+tr(text))

    def show_error(self,text):
        self.activity_failed=True
        self.set_status(text)
        self.escape_hotkeys.close()
        self.error_detail.setText(tr(text));self.error_actions.show();self.retry_button.setEnabled(self.retry_action is not None)
        self.pill.present('Could not read','Open Skrivi Lytt for details and recovery.',self.activity_screen,active=False,error=True)

    def open_reader(self,index=0):
        if index in (1,2):
            self.open_settings();self.settings_tabs.setCurrentIndex(2 if index==1 else 0);return
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
        self.retry_action=self.capture_region
        self.error_actions.hide();self.error_detail.hide()
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
        self.retry_action=self.capture_selection
        self.error_actions.hide();self.error_detail.hide()
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
        self.settings_dialog.hide()
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
