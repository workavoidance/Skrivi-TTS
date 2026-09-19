"""Global shortcuts and selection capture; no microphone or OCR access."""
import ctypes
from ctypes import wintypes
import subprocess
import sys
import winreg
from PySide6.QtCore import QAbstractNativeEventFilter

HOTKEYS={'Ctrl+Alt+Space':(0x0002|0x0001,0x20),'Ctrl+Alt+R':(0x0002|0x0001,0x52),'Ctrl+Shift+F8':(0x0002|0x0004,0x77),'Ctrl+Alt+Shift+Space':(0x0002|0x0001|0x0004,0x20)}
user32=ctypes.windll.user32
user32.GetForegroundWindow.restype=wintypes.HWND
user32.GetClipboardSequenceNumber.restype=wintypes.DWORD

class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self,callback,identifier=0x5311):
        super().__init__();self.callback=callback;self.current=None;self.identifier=identifier
    def register(self,choice):
        if choice not in HOTKEYS: raise ValueError('Unsupported shortcut.')
        if choice==self.current:return
        mods,key=HOTKEYS[choice]
        if self.current:user32.UnregisterHotKey(None,self.identifier)
        if not user32.RegisterHotKey(None,self.identifier,mods|0x4000,key):
            if self.current:
                oldmod,oldkey=HOTKEYS[self.current];user32.RegisterHotKey(None,self.identifier,oldmod|0x4000,oldkey)
            raise RuntimeError('That shortcut is already in use. Choose another in Settings.')
        self.current=choice
    def nativeEventFilter(self,event_type,message):
        msg=wintypes.MSG.from_address(int(message))
        if msg.message==0x0312 and msg.wParam==self.identifier:
            self.callback();return True,0
        return False,0
    def close(self):
        user32.UnregisterHotKey(None,self.identifier);self.current=None

def modifiers_released():
    return not any(user32.GetAsyncKeyState(key)&0x8000 for key in (0x10,0x11,0x12,0x5B,0x5C))

def copy_selection():
    # Correct pointer-sized Win32 INPUT layout for SendInput on x64.
    class KEYBDINPUT(ctypes.Structure):
        _fields_=[('wVk',wintypes.WORD),('wScan',wintypes.WORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.c_size_t)]
    class MOUSEINPUT(ctypes.Structure):
        _fields_=[('dx',wintypes.LONG),('dy',wintypes.LONG),('mouseData',wintypes.DWORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.c_size_t)]
    class UNION(ctypes.Union):_fields_=[('ki',KEYBDINPUT),('mi',MOUSEINPUT)]
    class INPUT(ctypes.Structure):_fields_=[('type',wintypes.DWORD),('value',UNION)]
    events=(INPUT*4)()
    for item,key,flags in zip(events,(0xA2,0x43,0x43,0xA2),(0,0,2,2)):
        item.type=1;item.value.ki=KEYBDINPUT(key,0,flags,0,0)
    if user32.SendInput(4,events,ctypes.sizeof(INPUT))!=4:
        raise RuntimeError('Could not copy selected text from this application.')

def set_startup(enabled):
    path=r'Software\Microsoft\Windows\CurrentVersion\Run'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,path) as key:
        if enabled:
            if not getattr(sys,'frozen',False):raise RuntimeError('Install the app before enabling sign-in startup.')
            winreg.SetValueEx(key,'SkriviTTS',0,winreg.REG_SZ,subprocess.list2cmdline([sys.executable,'--tray']))
        else:
            try:winreg.DeleteValue(key,'SkriviTTS')
            except FileNotFoundError:pass


class WavePlayer:
    """Play a native WAV and wait for the device to finish; cancellable without a start/stop race."""
    def __init__(self):
        import threading
        self.lock=threading.Lock();self.alias=None
        self.mci=ctypes.windll.winmm.mciSendStringW
        self.mci.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.UINT,wintypes.HWND]
        self.mci.restype=wintypes.DWORD
    def command(self,text):
        output=ctypes.create_unicode_buffer(256)
        error=self.mci(text,output,256,None)
        if error:
            message=ctypes.create_unicode_buffer(256)
            ctypes.windll.winmm.mciGetErrorStringW(error,message,256)
            raise RuntimeError('Audio playback: '+message.value)
        return output.value
    def play(self,path,cancel):
        import uuid
        alias='skrivi'+uuid.uuid4().hex
        try:
            with self.lock:
                if cancel.is_set():return
                self.command('open "'+str(path)+'" type waveaudio alias '+alias)
                self.alias=alias
                self.command('play '+alias)
            while not cancel.wait(.05):
                with self.lock:
                    if self.command('status '+alias+' mode')!='playing':break
        finally:
            with self.lock:
                if self.alias==alias:
                    try:self.command('close '+alias)
                    finally:self.alias=None
    def stop(self):
        with self.lock:
            if self.alias:
                try:self.command('stop '+self.alias)
                except RuntimeError:pass
