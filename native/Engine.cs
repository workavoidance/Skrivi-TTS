using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Media;
using Reader.Core;

namespace Reader.Windows
{
    internal sealed class VoxEngine : ISpeechEngine
    {
        readonly string model;
        readonly string voices;
        VoiceSettings settings = new VoiceSettings();
        public void Configure(VoiceSettings value)
        {
            value.Validate();
            if (settings.Steps != value.Steps || settings.Guidance != value.Guidance || settings.Threads != value.Threads) Stop();
            settings = value;
        }
        readonly object gate = new object();
        readonly SemaphoreSlim serial = new SemaphoreSlim(1, 1);
        Process process;
        HttpClient http;
        OwnedJob job;
        public double LastLoadSeconds { get; private set; }
        public double LastGenerationSeconds { get; private set; }
        public long PeakRamBytes { get; private set; }
        public event Action<string> Status;
        public VoxEngine(string modelPath, string voicesPath) { model = modelPath; voices = voicesPath; Directory.CreateDirectory(voices); }
        public async Task WarmAsync(CancellationToken token)
        {
            await serial.WaitAsync(token);
            try { await EnsureReady(token); } finally { serial.Release(); }
        }
        async Task EnsureReady(CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            lock (gate) { if (process != null && !process.HasExited && http != null) return; }
            Stop();
            if (Status != null) Status("Loading VoxCPM2...");
            var watch = Stopwatch.StartNew();
            var listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start(); int port = ((IPEndPoint)listener.LocalEndpoint).Port; listener.Stop();
            string key = Guid.NewGuid().ToString("N") + Guid.NewGuid().ToString("N");
            var psi = new ProcessStartInfo(Path.Combine(Environment.GetEnvironmentVariable("SKRIVI_TTS_RUNTIME"), "crispasr.exe"))
            {
                Arguments = "--server --backend voxcpm2-tts -m \"" + model + "\" --voice-dir \"" + voices + "\" --host 127.0.0.1 --port " + port + " --ws-port -1 --no-gpu -t " + settings.Threads,
                WorkingDirectory = voices,
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true
            };
            psi.EnvironmentVariables["CRISPASR_API_KEYS"] = key;
            psi.EnvironmentVariables.Remove("CRISPASR_CONSENT_LOG");
            // Never inherit user overrides that lower diffusion quality or alter cadence.
            psi.EnvironmentVariables.Remove("CRISPASR_VOXCPM2_INFERENCE_STEPS");
            psi.EnvironmentVariables.Remove("CRISPASR_VOXCPM2_CFG_VALUE");
            psi.EnvironmentVariables.Remove("CRISPASR_VOXCPM2_MAX_LEN");
            psi.EnvironmentVariables["CRISPASR_VOXCPM2_INFERENCE_STEPS"] = settings.Steps.ToString(System.Globalization.CultureInfo.InvariantCulture);
            psi.EnvironmentVariables["CRISPASR_VOXCPM2_CFG_VALUE"] = settings.Guidance.ToString(System.Globalization.CultureInfo.InvariantCulture);
            var child = new Process { StartInfo = psi };
            var client = new HttpClient(new HttpClientHandler { UseProxy = false, AllowAutoRedirect = false })
            { BaseAddress = new Uri("http://127.0.0.1:" + port + "/"), Timeout = TimeSpan.FromMinutes(15) };
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
            lock (gate)
            {
                token.ThrowIfCancellationRequested();
                child.Start(); process = child; http = client;
                job = new OwnedJob(child);
                // Runtime diagnostics may contain selected text. Drain and discard them.
                child.OutputDataReceived += (s, e) => { };
                child.ErrorDataReceived += (s, e) => { };
                child.BeginOutputReadLine(); child.BeginErrorReadLine();
            }
            try
            {
                while (watch.Elapsed < TimeSpan.FromMinutes(3))
                {
                    token.ThrowIfCancellationRequested();
                    if (child.HasExited) throw new InvalidOperationException("The VoxCPM2 runtime exited while loading. This build needs an x64 CPU with AVX2 and sufficient memory.");
                    using (var probe = CancellationTokenSource.CreateLinkedTokenSource(token))
                    {
                        probe.CancelAfter(1000);
                        try
                        {
                            // An authenticated model request avoids mistaking an unrelated service for our runtime.
                            var result = await client.GetAsync("v1/models", probe.Token);
                            using (result)
                            {
                                if (result.IsSuccessStatusCode)
                                { LastLoadSeconds = watch.Elapsed.TotalSeconds; return; }
                            }
                        }
                        catch (HttpRequestException) { }
                        catch (OperationCanceledException) { token.ThrowIfCancellationRequested(); }
                    }
                    await Task.Delay(200, token);
                }
                throw new TimeoutException("VoxCPM2 did not load within three minutes.");
            }
            catch { Stop(); throw; }
        }
        public async Task<byte[]> SynthesizeAsync(string text, CancellationToken token)
        {
            text = ReadingText.Validate(text);
            await serial.WaitAsync(token);
            try
            {
                await EnsureReady(token);
                if (Status != null) Status("Generating speech...");
                var watch = Stopwatch.StartNew();
                if (!string.IsNullOrEmpty(settings.Reference))
                {
                    string referencePath = Path.Combine(voices, settings.Reference);
                    if (!File.Exists(referencePath) || new FileInfo(referencePath).Length > 2000000)
                        throw new InvalidDataException("Reference voice is missing or invalid. Import the WAV again.");
                    WaveInfo.ParseReference(File.ReadAllBytes(referencePath));
                }
                var json = new JavaScriptSerializer().Serialize(new {
                    input = text, response_format = "wav", speed = 1.0, seed = settings.Seed,
                    voice = settings.Reference, consent_attestation = settings.Consent,
                    spoken_disclaimer = false,
                    marking_attestation = string.IsNullOrEmpty(settings.Reference) ? "" : "Reader displays AI-generated speech; the user accepted responsibility for identifying any shared output."
                });
                using (var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json"))
                using (var response = await http.PostAsync("v1/audio/speech", content, token))
                {
                    if (!response.IsSuccessStatusCode) throw new InvalidOperationException("VoxCPM2 could not generate speech (HTTP " + (int)response.StatusCode + "). Try a shorter selection.");
                    byte[] wav = await response.Content.ReadAsByteArrayAsync();
                    token.ThrowIfCancellationRequested(); WaveInfo.Parse(wav);
                    LastGenerationSeconds = watch.Elapsed.TotalSeconds;
                    lock (gate) { if (process != null && !process.HasExited) { process.Refresh(); PeakRamBytes = process.PeakWorkingSet64; } }
                    return wav;
                }
            }
            catch { Stop(); throw; }
            finally { serial.Release(); }
        }
        public void Stop()
        {
            lock (gate)
            {
                if (process != null) { try { if (!process.HasExited) process.Kill(); } catch { } process.Dispose(); process = null; }
                if (job != null) { job.Dispose(); job = null; }
                if (http != null) { http.Dispose(); http = null; }
            }
        }
        public void Dispose() { Stop(); }
    }
    internal sealed class WindowsAudio : IAudioPlayer
    {
        readonly object gate = new object();
        SoundPlayer player;
        MemoryStream stream;
        public async Task PlayAsync(byte[] wav, CancellationToken token)
        {
            var info = WaveInfo.Parse(wav);
            using (token.Register(Stop))
            {
                lock (gate)
                {
                    token.ThrowIfCancellationRequested(); Stop();
                    stream = new MemoryStream(wav, false);
                    player = new SoundPlayer(stream); player.Load(); player.Play();
                }
                // Windows plays the complete unchanged WAV. Do not stop or dispose at the nominal end.
                await Task.Delay(TimeSpan.FromSeconds(info.Seconds + 0.5), token);
            }
        }
        public void Stop()
        {
            lock (gate)
            {
                if (player != null) { player.Stop(); player.Dispose(); player = null; }
                if (stream != null) { stream.Dispose(); stream = null; }
            }
        }
        public void Dispose() { Stop(); }
    }
}
