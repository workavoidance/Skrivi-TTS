import os
import json
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
import zipfile
import queue
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

if os.name != "nt":
    raise SystemExit("This lightweight shoot-out is Windows-only.")

import winsound

APP_DIR = Path(__file__).resolve().parent
# September 8 continuation of the existing v5 UI; reuse its persistent resources.
LOCAL = json.loads((APP_DIR / "local-paths.json").read_text(encoding="utf-8-sig"))
STATE_DIR = Path(LOCAL["shootout_state"])
UV = STATE_DIR / ".bootstrap" / "Scripts" / "uv.exe"
ENVS = STATE_DIR / "envs"
OUTPUTS = Path(LOCAL.get("outputs", str(Path(LOCAL["lab_root"]) / "shootout-outputs")))
VENDOR = STATE_DIR / "vendor"
MODELS_DIR = STATE_DIR / "models"
for p in (ENVS, OUTPUTS, VENDOR, MODELS_DIR):
    p.mkdir(exist_ok=True)

DEFAULT_TEXT = (
    "Dette er en sammenligning av lokale norske talesyntesemodeller. "
    "Målet er å finne en stemme som er tydelig, naturlig og behagelig nok til å lese "
    "skoletekst høyt over lengre tid. I 2026 kostet boka 349 kroner, og eleven skulle "
    "lese kapittel 7 på side 128. Hvordan uttaler modellen navn, tall, forkortelser og "
    "litt vanskeligere norske ord?"
)

MODEL_LIST = [
    {
        "id": "voxcpm_q4", "name": "Public VoxCPM2 Q4 — CPU",
        "family": "VoxCPM2", "license": "Model Apache-2.0; CrispASR MIT",
        "size": "1.689 GB model (existing cache)",
        "note": "Approved public model; reuses Reader 0.2 engine. Default voice, seed 42, 10 steps, guidance 2.0. CPU only.",
        "env": "external", "py": "3.12",
    },
    {
        "id": "chatterbox_q4", "name": "Chatterbox Multilingual Q4 ONNX — CPU",
        "family": "Chatterbox ONNX", "license": "Model MIT",
        "size": "1.556 GB assets + 212 MB dedicated environment",
        "note": "Q4 language model with FP32 companions. Native bundled reference; CPU only. Full WAV before playback.",
        "env": "external", "py": "3.12",
    },
    {
        "id": "piper_nvcc",
        "name": "Piper NVCC medium",
        "family": "Piper",
        "license": "Voice data CC0; current Piper runtime GPL-3.0-or-later",
        "size": "~77 MB voice",
        "note": "10 Norwegian speakers. Very light and fast.",
        "env": "piper",
        "py": "3.12",
    },
    {
        "id": "piper_talesyntese",
        "name": "Piper Talesyntese medium",
        "family": "Piper",
        "license": "Voice data CC0; current Piper runtime GPL-3.0-or-later",
        "size": "~63 MB voice",
        "note": "Single Norwegian speaker. Very light and fast.",
        "env": "piper",
        "py": "3.12",
    },
    {
        "id": "nb_piper",
        "name": "NbAiLab Piper NST trimmed",
        "family": "Piper",
        "license": "Model Apache-2.0; current Piper runtime GPL-3.0-or-later",
        "size": "~64 MB model",
        "note": "Norwegian National Library model. Same fast Piper runtime.",
        "env": "piper",
        "py": "3.12",
    },
    {
        "id": "chatterbox",
        "name": "Chatterbox Multilingual V3",
        "family": "Chatterbox",
        "license": "MIT",
        "size": "Large, 500M parameters",
        "note": "Direct Norwegian support. Better licence; much heavier than Piper.",
        "env": "chatterbox_v3src_nogit",
        "py": "3.11",
    },
    {
        "id": "speecht5",
        "name": "Norwegian SpeechT5 (NST)",
        "family": "SpeechT5",
        "license": "Norwegian model Apache-2.0",
        "size": "~578 MB model + vocoder",
        "note": "Older 100M-parameter Norwegian fine-tune; useful permissive baseline.",
        "env": "speecht5",
        "py": "3.12",
    },
    {
        "id": "moss",
        "name": "NbAiLab MOSS-TTS-Nano",
        "family": "MOSS-TTS-Nano",
        "license": "Apache-2.0",
        "size": "~100M TTS + ~22M audio tokenizer",
        "note": "New CPU-oriented Norwegian fine-tune. Experimental path in this tester.",
        "env": "moss",
        "py": "3.12",
    },
]

NVCC_SPEAKERS = [
    "KNN (speaker 1)",
    "KSV (speaker 2)",
    "MMN (speaker 3)",
    "KON (speaker 4)",
    "MNN (speaker 5)",
    "MSV (speaker 6)",
    "MON (speaker 7)",
    "MNV (speaker 8)",
    "KMN (speaker 9)",
    "KNV (speaker 10)",
]

if LOCAL.get("ready_only"):
    MODEL_LIST = [m for m in MODEL_LIST if m['id'] in
                  {'voxcpm_q4', 'chatterbox_q4', 'piper_nvcc', 'piper_talesyntese'}]

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run(cmd, cwd=None, timeout=None):
    result = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Unknown error").strip()
        raise RuntimeError(detail[-8000:])
    return result.stdout.strip()


def env_python(env_name):
    return ENVS / env_name / "Scripts" / "python.exe"


def ensure_uv():
    if not UV.exists():
        raise RuntimeError(
            "The bootstrap tool is missing. Close the tester and start it again with RUN_SHOOTOUT.bat."
        )


def ensure_env(model, status):
    if LOCAL.get('ready_only') and model['family'] == 'Piper':
        key = {'piper_nvcc': 'no_NO-nvcc-medium', 'piper_talesyntese': 'no_NO-talesyntese-medium'}[model['id']]
        required = [env_python('piper'), MODELS_DIR / 'piper' / (key + '.onnx'),
                    MODELS_DIR / 'piper' / (key + '.onnx.json')]
        if not all(path.is_file() for path in required):
            raise RuntimeError('A cached Piper file is missing. This edition does not install models automatically.')
        return env_python('piper')
    if model["id"] in {"voxcpm_q4", "chatterbox_q4"}:
        python = Path(LOCAL["python"])
        if not python.exists():
            raise RuntimeError("The configured local experiment environment is missing. See PROJECT_STATUS.md.")
        return python
    ensure_uv()
    env_name = model["env"]
    pyexe = env_python(env_name)
    marker = ENVS / env_name / ".ready"
    if pyexe.exists() and marker.exists():
        return pyexe

    status(f"Setting up {model['family']} environment (first use only)…")
    env_dir = ENVS / env_name
    if env_dir.exists():
        raise RuntimeError("Existing environment is incomplete; it was preserved. See PROJECT_STATUS.md before repairing it.")

    run([UV, "venv", "--python", model["py"], str(env_dir)])

    if env_name == "piper":
        status("Installing Piper runtime…")
        run([
            UV, "pip", "install", "--python", str(pyexe),
            "piper-tts>=1.4,<2", "huggingface_hub>=0.30"
        ])
    elif env_name == "chatterbox_v3src_nogit":
        status("Preparing Chatterbox Multilingual V3 source…")
        chatterbox_repo = ensure_chatterbox_repo(status)
        status("Installing Chatterbox Multilingual V3 without Git…")
        # Perth's PyPI wheel imports pkg_resources, which is safest with
        # setuptools < 81. Install this first, then let the patched Chatterbox
        # pyproject pull Perth from PyPI rather than from git+https.
        run([
            UV, "pip", "install", "--python", str(pyexe),
            "setuptools<81"
        ], timeout=600)
        run([
            UV, "pip", "install", "--python", str(pyexe),
            str(chatterbox_repo),
            "soundfile"
        ], timeout=1800)
    elif env_name == "speecht5":
        status("Installing SpeechT5 dependencies…")
        run([
            UV, "pip", "install", "--python", str(pyexe),
            "torch", "transformers>=4.45,<5", "datasets>=3,<5",
            "soundfile", "sentencepiece"
        ], timeout=1800)
    elif env_name == "moss":
        status("Preparing MOSS-TTS-Nano source…")
        moss_repo = ensure_moss_repo(status)
        status("Installing MOSS-TTS-Nano dependencies…")
        run([
            UV, "pip", "install", "--python", str(pyexe),
            "numpy>=1.24",
            "sentencepiece>=0.1.99",
            "torch==2.7.0",
            "torchaudio==2.7.0",
            "transformers==4.57.1",
            "soundfile",
            "onnxruntime>=1.20.0",
            "huggingface_hub",
            "safetensors",
            "accelerate"
        ], timeout=1800)
        run([
            UV, "pip", "install", "--python", str(pyexe),
            "--no-deps", "-e", str(moss_repo)
        ], timeout=600)
    else:
        raise RuntimeError(f"Unknown environment: {env_name}")

    marker.write_text("ok", encoding="utf-8")
    return pyexe



def ensure_chatterbox_repo(status):
    """Download official Chatterbox source as ZIP and replace its Git-only
    Perth dependency with the official PyPI package.

    This keeps the test machine Git-free while using the current V3 source.
    """
    dest = VENDOR / "chatterbox-v3-source"
    pyproject = dest / "pyproject.toml"

    if pyproject.exists():
        contents = pyproject.read_text(encoding="utf-8")
        if 'resemble-perth==1.0.1' in contents:
            return dest

    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)

    status("Downloading current official Chatterbox source…")
    zip_path = VENDOR / "chatterbox-master.zip"
    url = "https://github.com/resemble-ai/chatterbox/archive/refs/heads/master.zip"
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path) as z:
        z.extractall(VENDOR)

    extracted = VENDOR / "chatterbox-master"
    if not extracted.exists():
        candidates = [
            p for p in VENDOR.iterdir()
            if p.is_dir()
            and p.name.startswith("chatterbox-")
            and p.name != dest.name
            and (p / "pyproject.toml").exists()
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                "Chatterbox source downloaded, but the extracted source folder "
                "could not be identified."
            )
        extracted = candidates[0]

    extracted.rename(dest)

    contents = pyproject.read_text(encoding="utf-8")
    git_dep = '"resemble-perth @ git+https://github.com/resemble-ai/Perth.git@master",'
    if git_dep not in contents:
        # Accept the source only if it already has a normal Perth dependency.
        if '"resemble-perth' not in contents:
            raise RuntimeError(
                "The current Chatterbox dependency layout has changed. "
                "Please use a newer version of this tester."
            )
    else:
        contents = contents.replace(
            git_dep,
            '"resemble-perth==1.0.1",'
        )
        pyproject.write_text(contents, encoding="utf-8")

    try:
        zip_path.unlink()
    except OSError:
        pass

    return dest


def ensure_moss_repo(status):
    dest = VENDOR / "MOSS-TTS-Nano"
    if (dest / "infer.py").exists():
        return dest

    status("Downloading the MOSS-TTS-Nano inference code…")
    zip_path = VENDOR / "moss-main.zip"
    url = "https://github.com/OpenMOSS/MOSS-TTS-Nano/archive/refs/heads/main.zip"
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(VENDOR)
    extracted = VENDOR / "MOSS-TTS-Nano-main"
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    extracted.rename(dest)
    try:
        zip_path.unlink()
    except OSError:
        pass
    return dest


def backend_command(model_id, pyexe, text_file, output_file, speaker_id):
    if model_id in {"voxcpm_q4", "chatterbox_q4"}:
        return [pyexe, APP_DIR / "new_backends.py", "--engine", model_id,
                "--text-file", text_file, "--output", output_file]
    if model_id in {"piper_nvcc", "piper_talesyntese", "nb_piper"}:
        cmd = [
            pyexe, APP_DIR / "backends" / "piper_backend.py",
            "--model", model_id,
            "--text-file", text_file,
            "--output", output_file,
            "--model-dir", MODELS_DIR / "piper",
        ]
        if speaker_id is not None:
            cmd.extend(["--speaker", str(speaker_id)])
        return cmd

    if model_id == "chatterbox":
        return [
            pyexe, APP_DIR / "backends" / "chatterbox_backend.py",
            "--text-file", text_file,
            "--output", output_file,
        ]

    if model_id == "speecht5":
        return [
            pyexe, APP_DIR / "backends" / "speecht5_backend.py",
            "--text-file", text_file,
            "--output", output_file,
        ]

    if model_id == "moss":
        moss_repo = VENDOR / "MOSS-TTS-Nano"
        return [
            pyexe, moss_repo / "infer.py",
            "--checkpoint", "NbAiLab/nb-tts-norwegian-moss-nano-trimmed",
            "--audio-tokenizer-pretrained-name-or-path", "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano",
            "--mode", "continuation",
            "--text-file", text_file,
            "--output-audio-path", output_file,
            "--device", "auto",
            "--dtype", "auto",
            "--disable-wetext-processing",
            "--disable-normalize-tts-text",
            "--seed", "7",
        ]

    raise RuntimeError(f"Unknown model: {model_id}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Norwegian Local TTS Model Shoot-out")
        self.geometry("1050x820")
        self.minsize(950, 760)

        self.model_name = tk.StringVar(value=MODEL_LIST[0]["name"])
        self.speaker_name = tk.StringVar(value=NVCC_SPEAKERS[0])
        self.status = tk.StringVar(value="Ready. Choose a model, enter Norwegian text, then Generate & listen.")
        self.license_text = tk.StringVar()
        self.details_text = tk.StringVar()
        self.busy = False
        self.cancelled = threading.Event()
        self.protocol("WM_DELETE_WINDOW", self.close_when_idle)
        self.last_output = None
        self.results_queue = queue.Queue()
        self.saved_runs = {}
        self.started_at = None
        self.waiting_for_audio = False

        self._build()
        self._model_changed()
        self.restore_results()
        self.after(100, self.poll_results)

    def _build(self):
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Norwegian Local TTS Model Shoot-out",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer,
            text="Same text, different local engines. Listen for naturalness, pronunciation and reading comfort.",
        ).pack(anchor="w", pady=(2, 14))

        row = ttk.Frame(outer)
        row.pack(fill="x")

        ttk.Label(row, text="Model / engine").grid(row=0, column=0, sticky="w")
        model_combo = ttk.Combobox(
            row,
            textvariable=self.model_name,
            values=[m["name"] for m in MODEL_LIST],
            state="readonly",
            width=42,
        )
        model_combo.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        model_combo.bind("<<ComboboxSelected>>", lambda _e: self._model_changed())

        ttk.Label(row, text="Speaker").grid(row=0, column=1, sticky="w")
        self.speaker_combo = ttk.Combobox(
            row,
            textvariable=self.speaker_name,
            state="readonly",
            width=23,
        )
        self.speaker_combo.grid(row=1, column=1, sticky="ew")

        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=1)

        info = ttk.Frame(outer)
        info.pack(fill="x", pady=(10, 0))
        ttk.Label(info, textvariable=self.license_text, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(info, textvariable=self.details_text, wraplength=820).pack(anchor="w", pady=(2, 0))

        self.text = tk.Text(
            outer,
            wrap="word",
            font=("Segoe UI", 12),
            undo=True,
            height=8,
        )
        self.text.pack(fill="both", expand=True, pady=(14, 12))
        self.text.insert("1.0", DEFAULT_TEXT)

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x")

        self.speak_button = ttk.Button(buttons, text="▶ Generate & listen", command=self.speak)
        self.speak_button.pack(side="left")
        ttk.Button(buttons, text="■ Stop", command=self.stop).pack(side="left", padx=(8, 0))
        self.next_button = ttk.Button(buttons, text="Next speaker", command=self.next_speaker)
        self.next_button.pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Open outputs", command=self.open_outputs).pack(side="left", padx=(8, 0))
        self.replay_button = ttk.Button(buttons, text="Replay selected result", command=self.replay)
        self.replay_button.pack(side="left", padx=(8, 0))

        ttk.Label(outer, text="Saved comparisons — select a row to replay (all CPU)").pack(anchor="w", pady=(12, 4))
        columns = ('model', 'load', 'generate', 'audio', 'ratio', 'wait')
        self.results = ttk.Treeview(outer, columns=columns, show='headings', height=6, selectmode='browse')
        for key, title, width in zip(columns,
                ('Model / speaker', 'Load (s)', 'Generate (s)', 'Audio (s)', 'Gen / audio', 'Total wait (s)'),
                (330, 95, 105, 95, 105, 110)):
            self.results.heading(key, text=title)
            self.results.column(key, width=width, anchor='w' if key == 'model' else 'e')
        self.results.pack(fill='x')
        self.results.bind('<Double-1>', lambda _e: self.replay())

        ttk.Label(
            outer,
            textvariable=self.status,
            wraplength=850,
        ).pack(anchor="w", pady=(12, 0))

        ttk.Separator(outer).pack(fill="x", pady=(12, 8))
        ttk.Label(
            outer,
            text=(
                "Each click loads a fresh model. Total wait includes startup and loading; Generate measures speech creation. "
                "Gen / audio below 1 means faster than playback. Complete audio plays at its native speed. "
                "This local edition reuses installed models; Chatterbox loading can take about 40 seconds."
            ),
            wraplength=850,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

    def selected_model(self):
        for model in MODEL_LIST:
            if model["name"] == self.model_name.get():
                return model
        return MODEL_LIST[0]

    def _model_changed(self):
        model = self.selected_model()
        self.license_text.set(f"Licence: {model['license']}")
        self.details_text.set(f"{model['size']}  •  {model['note']}")
        if model["id"] == "piper_nvcc":
            self.speaker_combo["values"] = NVCC_SPEAKERS
            self.speaker_name.set(NVCC_SPEAKERS[3])
            self.speaker_combo.config(state="readonly")
            self.next_button.config(state="normal")
        else:
            self.speaker_combo["values"] = ["Default / model voice"]
            self.speaker_name.set("Default / model voice")
            self.speaker_combo.config(state="disabled")
            self.next_button.config(state="disabled")

    def selected_speaker_id(self):
        if self.selected_model()["id"] != "piper_nvcc":
            return None
        try:
            return NVCC_SPEAKERS.index(self.speaker_name.get())
        except ValueError:
            return 0

    def next_speaker(self):
        if self.selected_model()["id"] != "piper_nvcc":
            return
        current = self.selected_speaker_id() or 0
        self.speaker_name.set(NVCC_SPEAKERS[(current + 1) % len(NVCC_SPEAKERS)])
        self.speak()

    def set_status(self, text):
        self.after(0, self.status.set, text)

    def set_busy(self, busy):
        self.busy = busy
        self.after(
            0,
            lambda: self.speak_button.config(
                state=("disabled" if busy else "normal")
            )
        )

    def add_result(self, result):
        key = result['output']
        if key in self.saved_runs:
            return
        self.saved_runs[key] = result
        values = (result['label'], *(f"{result[field]:.2f}" for field in
                  ('load_seconds', 'generation_seconds', 'audio_seconds', 'real_time_factor', 'total_wait_seconds')))
        self.results.insert('', 0, iid=key, values=values)
        self.results.selection_set(key)

    def restore_results(self):
        for path in sorted(OUTPUTS.glob('*.result.json')):
            try:
                result = json.loads(path.read_text(encoding='utf-8'))
                if Path(result['output']).exists():
                    self.add_result(result)
            except (ValueError, KeyError, OSError, tk.TclError):
                continue

    def poll_results(self):
        while not self.results_queue.empty():
            self.add_result(self.results_queue.get_nowait())
        if self.waiting_for_audio and not self.cancelled.is_set():
            elapsed = time.perf_counter() - self.started_at
            self.status.set(f"Loading model / generating speech — {elapsed:.1f} seconds elapsed. Stop cancels this run.")
        self.after(100, self.poll_results)

    def replay(self):
        if self.busy:
            return
        selected = self.results.selection()
        if not selected:
            messagebox.showinfo('Replay', 'Generate some audio, then select a result to replay.')
            return
        output = Path(selected[0])
        self.cancelled.clear()
        self.set_busy(True)
        def play():
            try:
                self.set_status(f'Playing {output.name}')
                winsound.PlaySound(str(output), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                self.set_status('Stopped.' if self.cancelled.is_set() else 'Playback finished. Ready.')
            except Exception as exc:
                self.set_status(f'Playback failed: {exc}')
            finally:
                self.set_busy(False)
        threading.Thread(target=play, daemon=True).start()

    def stop(self):
        self.cancelled.set()
        winsound.PlaySound(None, winsound.SND_PURGE)
        self.status.set("Stopped.")

    def close_when_idle(self):
        self.stop()
        if self.busy:
            self.after(100, self.close_when_idle)
        else:
            self.destroy()

    def open_outputs(self):
        OUTPUTS.mkdir(exist_ok=True)
        os.startfile(str(OUTPUTS))

    def speak(self):
        if self.busy:
            return
        text = self.text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Nothing to speak", "Enter some Norwegian text first.")
            return

        self.stop()
        self.cancelled.clear()
        model = self.selected_model()
        speaker_id = self.selected_speaker_id()
        self.set_busy(True)
        self.started_at = time.perf_counter()
        self.waiting_for_audio = True

        threading.Thread(
            target=self._worker,
            args=(model, speaker_id, text),
            daemon=True,
        ).start()

    def _worker(self, model, speaker_id, text):
        text_path = None
        try:
            pyexe = ensure_env(model, self.set_status)

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(text)
                text_path = Path(fh.name)

            timestamp = time.strftime("%Y%m%d-%H%M%S") + '-' + uuid.uuid4().hex[:6]
            suffix = f"-speaker{speaker_id+1}" if speaker_id is not None else ""
            output = OUTPUTS / f"{timestamp}-{model['id']}{suffix}.wav"

            self.set_status(f"Running {model['name']} locally…")
            started = time.perf_counter()
            cmd = backend_command(
                model["id"], pyexe, text_path, output, speaker_id
            )
            stdout = self.run_synthesis(cmd)
            elapsed = time.perf_counter() - started
            self.waiting_for_audio = False

            if self.cancelled.is_set():
                self.set_status("Stopped.")
                return

            if not output.exists() or output.stat().st_size < 1000:
                raise RuntimeError(
                    "The engine finished but did not create a usable WAV file.\n\n" + stdout
                )

            self.last_output = output
            sidecar = Path(str(output) + '.json')
            if sidecar.exists():
                metrics = json.loads(sidecar.read_text(encoding='utf-8-sig'))
                if isinstance(metrics, list):
                    metrics = metrics[0]
                metrics.update(output=str(output), label=model['name'] +
                               (f' / {NVCC_SPEAKERS[speaker_id]}' if speaker_id is not None else ''),
                               total_wait_seconds=time.perf_counter() - self.started_at)
                Path(str(output) + '.result.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
                self.results_queue.put(metrics)
            self.set_status(
                f"{model['name']} ready in {elapsed:.1f}s including model load. Playing now. "
                f"Saved as {output.name}"
            )
            winsound.PlaySound(
                str(output),
                winsound.SND_FILENAME | winsound.SND_NODEFAULT,
            )
            self.set_status('Stopped.' if self.cancelled.is_set() else 'Playback finished. Select another model to compare, or replay a saved result.')
        except subprocess.TimeoutExpired:
            self.set_status("Timed out.")
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Timed out",
                    "This model took more than 30 minutes. It is probably not practical on this machine."
                )
            )
        except Exception as exc:
            self.set_status(f"{model['name']} failed.")
            detail = str(exc)
            self.after(
                0,
                lambda d=detail, n=model["name"]: messagebox.showerror(
                    f"{n} failed",
                    d + "\n\nThe other models are independent, so you can still test them."
                )
            )
        finally:
            self.waiting_for_audio = False
            if text_path:
                try:
                    text_path.unlink()
                except OSError:
                    pass
            self.set_busy(False)

    def run_synthesis(self, cmd):
        # Own only this invocation's process tree; stop must not leave delayed speech.
        process = subprocess.Popen([str(x) for x in cmd], cwd=str(APP_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW)
        started = time.monotonic()
        try:
            while True:
                if self.cancelled.is_set():
                    return ""
                try:
                    stdout, stderr = process.communicate(timeout=0.1)
                    if process.returncode:
                        raise RuntimeError((stderr or stdout or "Engine failed")[-8000:])
                    return stdout
                except subprocess.TimeoutExpired:
                    if time.monotonic() - started > 1800:
                        raise subprocess.TimeoutExpired(cmd, 1800)
        finally:
            if process.poll() is None:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW, timeout=15)
            process.communicate()


if __name__ == "__main__":
    App().mainloop()
