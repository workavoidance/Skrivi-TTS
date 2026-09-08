"""Skrivi TTS desktop application, evolved from the existing v5 shootout."""
import os
from pathlib import Path
import queue
import shutil
import sys
import threading
import time
import uuid
import wave
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import winsound
from core import DATA, ROOT, VERSION, Library, catalog, defaults, validate, read_json, write_json, sha256
from client import Client

DEFAULT_TEXT = ('Dette er en test av norsk talesyntese. Målet er å finne en stemme som er tydelig, '
                'naturlig og behagelig å høre på over lengre tid. I 2026 kostet boka 349 kroner, '
                'og eleven skulle lese kapittel sju på side 128.')
LABELS = {'seed': 'Seed', 'steps': 'Diffusion steps (4–20)', 'guidance': 'Guidance (1–4)',
          'threads': 'CPU threads (1–16)', 'language': 'Language', 'exaggeration': 'Exaggeration (0–2)',
          'repetition_penalty': 'Repetition penalty (1–2)', 'max_tokens': 'Token safety limit (128–8192)',
          'speaker': 'Speaker number (0–9; 3 = female Oslo)', 'speed': 'Speed (1 = native cadence)',
          'noise_scale': 'Noise scale (blank = native)', 'noise_w_scale': 'Noise width (blank = native)'}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'Skrivi TTS {VERSION}')
        self.geometry('1100x850')
        self.minsize(950, 740)
        self.library = Library()
        self.models = catalog()
        self.saved = read_json(DATA / 'settings.json', {'schema': 1, 'models': {}})
        self.client = Client()
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.closing = False
        self.started = None
        self.generating = False
        self.active_id = None
        self.runs = {}
        self.fields = {}
        self.model_name = tk.StringVar(value=self.models[0]['name'])
        self.status = tk.StringVar(value='Ready. Model downloads and settings are kept separately from app updates.')
        self.build()
        self.change_model()
        self.restore_history()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def model(self):
        return next(m for m in self.models if m['name'] == self.model_name.get())

    def build(self):
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Skrivi TTS', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Local speech • persistent model library • repeatable comparisons').pack(anchor='w', pady=(0, 12))
        tabs = ttk.Notebook(outer)
        tabs.pack(fill='both', expand=True)
        read = ttk.Frame(tabs, padding=12)
        models = ttk.Frame(tabs, padding=12)
        tabs.add(read, text='Read & compare')
        tabs.add(models, text='Model library')
        self.combo = ttk.Combobox(read, textvariable=self.model_name, values=[m['name'] for m in self.models], state='readonly', width=60)
        self.combo.pack(anchor='w')
        self.combo.bind('<<ComboboxSelected>>', lambda _: self.change_model())
        self.info = ttk.Label(read, wraplength=1000)
        self.info.pack(anchor='w', pady=5)
        middle = ttk.Frame(read)
        middle.pack(fill='both', expand=True)
        left = ttk.Frame(middle)
        left.pack(side='left', fill='both', expand=True, padx=(0, 12))
        self.text = tk.Text(left, wrap='word', height=10, font=('Segoe UI', 12), undo=True)
        self.text.pack(fill='both', expand=True)
        self.text.insert('1.0', DEFAULT_TEXT)
        self.controls = ttk.LabelFrame(middle, text='Model settings', padding=8)
        self.controls.pack(side='right', fill='y')
        buttons = ttk.Frame(read)
        buttons.pack(fill='x', pady=10)
        self.generate_button = ttk.Button(buttons, text='Generate & listen', command=self.generate)
        self.generate_button.pack(side='left')
        ttk.Button(buttons, text='Stop / unload model', command=self.stop).pack(side='left', padx=6)
        ttk.Button(buttons, text='Replay selected', command=self.replay).pack(side='left')
        ttk.Button(buttons, text='Open audio folder', command=lambda: os.startfile(DATA / 'outputs')).pack(side='left', padx=6)
        columns = ('model', 'state', 'load', 'generate', 'audio', 'ratio', 'wait', 'rating')
        self.history = ttk.Treeview(read, columns=columns, show='headings', height=7, selectmode='browse')
        for key, title, width in zip(columns, ('Model', 'Session', 'Load s', 'Generate s', 'Audio s', 'Gen/audio', 'Wait s', 'Quality'), (255, 65, 70, 80, 70, 80, 70, 65)):
            self.history.heading(key, text=title)
            self.history.column(key, width=width, anchor='w' if key == 'model' else 'center')
        self.history.pack(fill='x')
        self.history.bind('<Double-1>', lambda _: self.replay())
        row = ttk.Frame(read)
        row.pack(fill='x', pady=6)
        ttk.Button(row, text='Rate selected audio', command=self.rate).pack(side='left')
        ttk.Button(row, text='Use selected settings', command=self.use_settings).pack(side='left', padx=6)
        ttk.Label(read, text='Models stay loaded between runs with unchanged settings. Stop releases memory. Gen/audio < 1 is faster than playback.', wraplength=980).pack(anchor='w')
        self.model_table = ttk.Treeview(models, columns=('name','size','license','state'), show='headings', height=8, selectmode='browse')
        for key, title, width in [('name','Model',330), ('size','Model size',110), ('license','License',230), ('state','State',150)]:
            self.model_table.heading(key, text=title)
            self.model_table.column(key, width=width)
        self.model_table.pack(fill='x')
        self.refresh_models()
        row = ttk.Frame(models)
        row.pack(fill='x', pady=12)
        ttk.Button(row, text='Download selected', command=lambda: self.model_action('download')).pack(side='left')
        ttk.Button(row, text='Import existing folder', command=lambda: self.model_action('import')).pack(side='left', padx=6)
        ttk.Button(row, text='Verify selected files', command=lambda: self.model_action('verify')).pack(side='left')
        ttk.Button(row, text='Open library', command=lambda: os.startfile(DATA)).pack(side='left', padx=6)
        ttk.Label(models, text=f'Permanent library: {DATA}\n\nApplication upgrades do not remove models, presets, references or audio. Downloads are explicit and verified against pinned checksums. Import copies existing files here once, without downloading them.\n\nAll four current adapters use CPU. New models are added through the versioned catalog and engine adapters.\n\nReference voices must be your own or used with permission. Imported audio stays local. Shared generated audio should be identified as AI-generated speech.', wraplength=970).pack(anchor='w')
        ttk.Button(models, text='Open GitHub project', command=lambda: webbrowser.open('https://github.com/workavoidance/Skrivi-TTS')).pack(anchor='w', pady=12)
        ttk.Label(outer, textvariable=self.status, wraplength=1050).pack(anchor='w', pady=(10, 0))

    def refresh_models(self):
        self.model_table.delete(*self.model_table.get_children())
        for model in self.models:
            self.model_table.insert('', 'end', iid=model['id'], values=(model['name'], f"{sum(f['bytes'] for f in model['files']) / 1e6:.0f} MB", model['license'], 'Installed' if self.library.ready(model) else 'Not installed'))
        self.model_table.selection_set(self.models[0]['id'])

    def current_settings(self):
        return validate(self.model()['engine'], {key: value.get() for key, value in self.fields.items()})

    def change_model(self):
        for child in self.controls.winfo_children():
            child.destroy()
        model = self.model()
        self.active_id = model['id']
        values = defaults(model['engine'])
        values.update(self.saved['models'].get(model['id'], {}))
        self.fields = {}
        for key, value in values.items():
            variable = tk.BooleanVar(value=value) if key == 'consent' else tk.StringVar(value=value)
            self.fields[key] = variable
            if key == 'consent':
                ttk.Checkbutton(self.controls, text='I have permission to use this voice', variable=variable).pack(anchor='w')
            elif key == 'reference':
                row = ttk.Frame(self.controls)
                row.pack(fill='x', pady=4)
                ttk.Button(row, text='Import reference WAV', command=self.import_reference).pack(side='left')
                ttk.Button(row, text='Clear', command=lambda v=variable: v.set('')).pack(side='left')
                ttk.Label(self.controls, textvariable=variable, wraplength=260).pack(anchor='w')
            else:
                row = ttk.Frame(self.controls)
                row.pack(fill='x', pady=2)
                ttk.Label(row, text=LABELS[key]).pack(side='left')
                if key == 'language':
                    ttk.Combobox(row, textvariable=variable, values=['no', 'en'], state='readonly', width=7).pack(side='right')
                else:
                    ttk.Entry(row, textvariable=variable, width=8).pack(side='right', padx=(6,0))
        row = ttk.Frame(self.controls)
        row.pack(fill='x', pady=8)
        ttk.Button(row, text='Save preset', command=self.save_preset).pack(side='left')
        ttk.Button(row, text='Load preset', command=self.load_preset).pack(side='left', padx=4)
        ttk.Button(self.controls, text='Restore native defaults', command=self.reset_settings).pack(anchor='w')
        self.info.configure(text=model['description'] + (' • Installed' if self.library.ready(model) else ' • Install or import in Model library'))

    def reset_settings(self):
        for key, value in defaults(self.model()['engine']).items():
            self.fields[key].set(value)

    def save_preset(self):
        try:
            settings = self.current_settings()
            name = simpledialog.askstring('Preset', 'Name this preset:')
            if name:
                write_json(DATA / 'presets' / (uuid.uuid4().hex + '.json'), {'name': name, 'model_id': self.model()['id'], 'settings': settings})
                self.status.set('Preset saved in your permanent library.')
        except Exception as error:
            messagebox.showerror('Preset', str(error))

    def load_preset(self):
        path = filedialog.askopenfilename(initialdir=DATA / 'presets', filetypes=[('Preset', '*.json')])
        if path:
            try:
                preset = read_json(Path(path))
                model = next(m for m in self.models if m['id'] == preset['model_id'])
                self.saved['models'][model['id']] = validate(model['engine'], preset['settings'])
                self.model_name.set(model['name'])
                self.change_model()
            except Exception as error:
                messagebox.showerror('Preset', str(error))

    def import_reference(self):
        path = filedialog.askopenfilename(filetypes=[('WAV audio', '*.wav')])
        if not path:
            return
        try:
            with wave.open(path) as wav:
                duration = wav.getnframes() / wav.getframerate()
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or not 2 <= duration <= 20:
                    raise ValueError('Use a 2–20 second mono PCM16 WAV.')
                if self.model()['engine'] == 'chatterbox' and wav.getframerate() != 24000:
                    raise ValueError('Chatterbox reference must already be 24 kHz. No automatic resampling is applied.')
                if not 16000 <= wav.getframerate() <= 48000 or Path(path).stat().st_size > 2000000:
                    raise ValueError('Use a 16–48 kHz reference under 2 MB.')
            target = DATA / 'voices' / ('voice-' + sha256(Path(path))[:24] + '.wav')
            if not target.exists():
                shutil.copyfile(path, target)
            self.fields['reference'].set(target.name)
            self.fields['consent'].set(False)
        except Exception as error:
            messagebox.showerror('Reference voice', str(error))

    def background(self, action):
        if self.busy:
            return
        self.busy = True
        self.cancel.clear()
        self.generate_button.configure(state='disabled')
        self.combo.configure(state='disabled')
        def work():
            try:
                action()
            except InterruptedError:
                self.events.put(('status', 'Stopped.'))
            except Exception as error:
                self.events.put(('error', str(error)))
            finally:
                self.events.put(('done', None))
        threading.Thread(target=work, daemon=True).start()

    def model_action(self, action):
        if self.busy:
            return
        selected = self.model_table.selection()
        if not selected:
            return
        model = next(m for m in self.models if m['id'] == selected[0])
        source = filedialog.askdirectory(title='Select the folder containing this model') if action == 'import' else None
        if action == 'import' and not source:
            return
        def work():
            progress = lambda value: self.events.put(('status', value))
            if action == 'verify':
                self.library.register(model, self.library.path(model), progress, self.cancel)
            else:
                self.library.install(model, progress, self.cancel, source)
            self.events.put(('status', 'Model ready. Files will be reused by future versions.'))
            self.events.put(('models', None))
        self.background(work)

    def generate(self):
        if self.busy:
            return
        model = self.model()
        try:
            settings = self.current_settings()
            text = self.text.get('1.0', 'end').strip()
            if not text:
                raise ValueError('Enter some text first.')
            if not self.library.ready(model):
                raise ValueError('Install or import this model in the Model library tab first.')
            self.saved['models'][model['id']] = settings
            write_json(DATA / 'settings.json', self.saved)
        except Exception as error:
            messagebox.showerror('Cannot generate', str(error))
            return
        self.started = time.perf_counter()
        self.generating = True
        output = DATA / 'outputs' / (time.strftime('%Y%m%d-%H%M%S') + '-' + model['id'] + '-' + uuid.uuid4().hex[:6] + '.wav')
        def work():
            result = self.client.generate({'model': model, 'assets': str(self.library.path(model)), 'settings': settings,
                'text': text, 'output': str(output), 'voices': str(DATA / 'voices'),
                'vox_runtime': str(DATA / 'runtimes' / 'vox-0.8.32')}, self.cancel)
            result.update(total_wait_seconds=time.perf_counter() - self.started, app_version=VERSION,
                          quality_rating=None, playback_completed=False)
            write_json(output.with_suffix('.json'), result)
            self.events.put(('result', result))
            self.events.put(('generated', None))
            if self.cancel.is_set():
                raise InterruptedError()
            self.events.put(('status', 'Playing complete audio at native output rate.'))
            winsound.PlaySound(str(output), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            result['playback_completed'] = not self.cancel.is_set()
            write_json(output.with_suffix('.json'), result)
            self.events.put(('status', 'Ready. The model is loaded for another reading.' if not self.cancel.is_set() else 'Stopped.'))
        self.background(work)

    def stop(self):
        self.cancel.set()
        winsound.PlaySound(None, winsound.SND_PURGE)
        if not self.busy:
            self.client.stop()
        self.status.set('Stopping and unloading…' if self.busy else 'Model unloaded. Ready.')

    def add_result(self, result):
        key = result['output']
        self.runs[key] = result
        if self.history.exists(key):
            self.history.delete(key)
        self.history.insert('', 0, iid=key, values=(result['model'], 'warm' if result['warm'] else 'cold',
            *(f"{result[k]:.2f}" for k in ('load_seconds', 'generation_seconds', 'audio_seconds', 'real_time_factor', 'total_wait_seconds')),
            result.get('quality_rating') or '—'))
        self.history.selection_set(key)

    def restore_history(self):
        for file in sorted((DATA / 'outputs').glob('*.json')):
            try:
                result = read_json(file)
                if Path(result['output']).exists():
                    self.add_result(result)
            except (KeyError, ValueError, OSError):
                continue

    def replay(self):
        if self.busy or not self.history.selection():
            return
        path = self.history.selection()[0]
        def work():
            self.events.put(('status', 'Replaying saved audio…'))
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            self.events.put(('status', 'Ready.'))
        self.background(work)

    def rate(self):
        if self.busy or not self.history.selection():
            return
        result = self.runs[self.history.selection()[0]]
        rating = simpledialog.askinteger('Listening quality', 'Overall quality: 1 (poor) to 5 (excellent)', minvalue=1, maxvalue=5)
        if rating:
            result['quality_rating'] = rating
            write_json(Path(result['output']).with_suffix('.json'), result)
            self.add_result(result)

    def use_settings(self):
        if self.busy or not self.history.selection():
            return
        result = self.runs[self.history.selection()[0]]
        model = next(m for m in self.models if m['id'] == result['model_id'])
        self.saved['models'][model['id']] = result['settings']
        self.model_name.set(model['name'])
        self.change_model()

    def poll(self):
        while not self.events.empty():
            event, value = self.events.get_nowait()
            if event == 'status':
                self.status.set(value)
            elif event == 'error':
                self.status.set('Operation failed; existing library files were preserved.')
                if not self.closing:
                    messagebox.showerror('Skrivi TTS', value)
            elif event == 'models':
                self.refresh_models()
                self.change_model()
            elif event == 'result':
                self.add_result(value)
            elif event == 'generated':
                self.generating = False
            elif event == 'done':
                self.busy = False
                self.generating = False
                if self.cancel.is_set():
                    self.client.stop()
                self.generate_button.configure(state='normal')
                self.combo.configure(state='readonly')
        if self.generating and not self.cancel.is_set():
            self.status.set(f'Loading / generating on CPU… {time.perf_counter() - self.started:.1f} seconds. No audio is uploaded.')
        if self.closing and not self.busy:
            self.client.stop()
            self.destroy()
            return
        self.after(100, self.poll)

    def close(self):
        self.closing = True
        self.stop()

if __name__ == '__main__':
    try:
        App().mainloop()
    except Exception as error:
        messagebox.showerror('Skrivi TTS could not start', str(error))
