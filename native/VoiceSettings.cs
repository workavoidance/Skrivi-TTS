using System;
using System.IO;
using System.Web.Script.Serialization;

namespace Reader.Windows
{
    public sealed class VoiceSettings
    {
        public int Seed { get; set; }
        public int Threads { get; set; }
        public int Steps { get; set; }
        public decimal Guidance { get; set; }
        public string Reference { get; set; }
        public string Consent { get; set; }
        public VoiceSettings() { Seed = 42; Threads = 8; Steps = 10; Guidance = 2.0m; Reference = ""; Consent = ""; }
        public void Validate()
        {
            if (Threads < 1 || Threads > 16 || Seed < 1 || Seed > 999999 || Steps < 4 || Steps > 20 || Guidance < 1 || Guidance > 4)
                throw new InvalidDataException("Voice settings are outside supported ranges.");
            if (!string.IsNullOrEmpty(Reference) &&
                (Path.GetFileName(Reference) != Reference || !Reference.StartsWith("voice-") || !Reference.EndsWith(".wav") || string.IsNullOrWhiteSpace(Consent)))
                throw new InvalidDataException("Invalid reference voice or missing permission confirmation.");
        }
        public static VoiceSettings Load(string path)
        {
            try { var s = new JavaScriptSerializer().Deserialize<VoiceSettings>(File.ReadAllText(path)); s.Validate(); return s; }
            catch { return new VoiceSettings(); }
        }
        public void Save(string path)
        {
            Validate(); Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temp = path + ".tmp";
            File.WriteAllText(temp, new JavaScriptSerializer().Serialize(this));
            if (File.Exists(path)) File.Replace(temp, path, null); else File.Move(temp, path);
        }
    }
}
