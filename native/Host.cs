using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Web.Script.Serialization;
using Reader.Windows;
using Reader.Core;

class Request {
    public string text { get; set; }
    public string output { get; set; }
    public VoiceSettings settings { get; set; }
}
class Host {
    static int Main(string[] args) {
        var json = new JavaScriptSerializer();
        using (var engine = new VoxEngine(args[0], args[1])) {
            string line;
            while ((line = Console.ReadLine()) != null) {
                try {
                    var request = json.Deserialize<Request>(line);
                    engine.Configure(request.settings);
                    var load = Stopwatch.StartNew();
                    engine.WarmAsync(CancellationToken.None).GetAwaiter().GetResult();
                    double loadSeconds = load.Elapsed.TotalSeconds;
                    var clock = Stopwatch.StartNew();
                    byte[] wav = engine.SynthesizeAsync(request.text, CancellationToken.None).GetAwaiter().GetResult();
                    double generation = clock.Elapsed.TotalSeconds;
                    File.WriteAllBytes(request.output, wav);
                    var info = WaveInfo.Parse(wav);
                    Console.WriteLine(json.Serialize(new { ok = true, load_seconds = loadSeconds,
                        generation_seconds = generation, audio_seconds = info.Seconds,
                        sample_rate = 48000, peak_ram_bytes = engine.PeakRamBytes }));
                } catch (Exception error) {
                    Console.WriteLine(json.Serialize(new { ok = false, error = error.GetBaseException().Message }));
                }
            }
        }
        return 0;
    }
}
