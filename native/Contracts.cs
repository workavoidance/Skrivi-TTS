using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Reader.Core
{
    public interface ISpeechEngine : IDisposable
    {
        Task<byte[]> SynthesizeAsync(string text, CancellationToken cancel);
        void Stop();
    }
    public interface IAudioPlayer : IDisposable
    {
        Task PlayAsync(byte[] wav, CancellationToken cancel);
        void Stop();
    }
    public static class ModelSpec
    {
        public const string FileName = "voxcpm2-q4_k.gguf";
        public const long Bytes = 1689498432L;
        public const string Sha256 = "502efe74f6a59c370b3abf5a3fcfd7c3955ca6c167b411c8aee3977e9e46c079";
        public const string Url = "https://huggingface.co/cstr/voxcpm2-GGUF/resolve/d426b5da661d5f833b45663879b1a0b0573a5b8e/voxcpm2-q4_k.gguf";
    }
    public static class ReadingText
    {
        public static string Validate(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) throw new InvalidOperationException("No selected text was found. Highlight a short passage and try again.");
            if (text.Length > 4096) throw new InvalidOperationException("This POC reads up to 4,096 characters at a time. Select a shorter passage.");
            if (text.IndexOf('\0') >= 0) throw new InvalidOperationException("The selection contains unsupported null characters.");
            return text.Trim();
        }
    }
    public sealed class WaveInfo
    {
        public int SampleRate { get; private set; }
        public int Channels { get; private set; }
        public double Seconds { get; private set; }
        public static WaveInfo Parse(byte[] bytes) { return ParseInternal(bytes, false); }
        public static WaveInfo ParseReference(byte[] bytes) { return ParseInternal(bytes, true); }
        static WaveInfo ParseInternal(byte[] bytes, bool reference)
        {
            if (bytes == null || bytes.Length < 44) throw new InvalidDataException("The speech engine returned no valid WAV audio.");
            using (var reader = new BinaryReader(new MemoryStream(bytes)))
            {
                if (Encoding.ASCII.GetString(reader.ReadBytes(4)) != "RIFF") throw new InvalidDataException("Expected WAV audio.");
                uint riffSize = reader.ReadUInt32();
                if (riffSize + 8L > bytes.Length || Encoding.ASCII.GetString(reader.ReadBytes(4)) != "WAVE") throw new InvalidDataException("Incomplete WAV audio.");
                int sr = 0, ch = 0, bits = 0, align = 0; long data = 0;
                while (reader.BaseStream.Position + 8 <= riffSize + 8L)
                {
                    string id = Encoding.ASCII.GetString(reader.ReadBytes(4));
                    uint size = reader.ReadUInt32(); long end = reader.BaseStream.Position + size;
                    if (end > riffSize + 8L) throw new InvalidDataException("Truncated WAV chunk.");
                    if (id == "fmt ")
                    {
                        if (size < 16 || reader.ReadUInt16() != 1) throw new InvalidDataException("Expected PCM WAV audio.");
                        ch = reader.ReadUInt16(); sr = reader.ReadInt32(); reader.ReadInt32();
                        align = reader.ReadUInt16(); bits = reader.ReadUInt16();
                    }
                    if (id == "data") data += size;
                    reader.BaseStream.Position = end + (size & 1);
                }
                if (ch != 1 || bits != 16 || align != 2 || data <= 0 || data % align != 0 ||
                    (reference ? sr < 16000 || sr > 48000 : sr != 48000))
                    throw new InvalidDataException(reference ? "Choose mono PCM16 WAV audio at 16–48 kHz, between 2 and 20 seconds." : "Expected complete native 48 kHz mono PCM16 VoxCPM2 audio; playback was refused.");
                double seconds = (double)data / (sr * align);
                if (reference && (seconds < 2 || seconds > 20))
                    throw new InvalidDataException("Choose a reference between 2 and 20 seconds, mono PCM16 WAV (16–48 kHz).");
                return new WaveInfo { SampleRate = sr, Channels = ch, Seconds = (double)data / (sr * align) };
            }
        }
    }
}
