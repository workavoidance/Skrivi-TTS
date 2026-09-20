using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

internal static class VerifyPackage {
    public static int Main(string[] args) {
        try {
            if (args.Length != 2) throw new ArgumentException("Expected package manifest and library folder.");
            var manifestText = File.ReadAllText(args[0]);
            if (manifestText.Length > 16 * 1024 * 1024) throw new InvalidDataException("Manifest is too large.");
            var parser = new JavaScriptSerializer { MaxJsonLength = 16 * 1024 * 1024 };
            var manifest = parser.Deserialize<Dictionary<string, object>>(manifestText);
            var files = manifest["files"] as Dictionary<string, object>;
            if (files == null) throw new InvalidDataException("Invalid package file list.");
            var root = Path.GetFullPath(args[1]).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            int checkedCount = 0;
            foreach (var entry in files) {
                if (!entry.Key.StartsWith("models/", StringComparison.Ordinal) && !entry.Key.StartsWith("runtimes/", StringComparison.Ordinal)) continue;
                var expected = entry.Value as string;
                if (expected == null || !Regex.IsMatch(expected, "\\A[0-9a-fA-F]{64}\\z")) throw new InvalidDataException("Invalid file checksum.");
                var target = Path.GetFullPath(Path.Combine(root, entry.Key.Replace('/', Path.DirectorySeparatorChar)));
                if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Invalid package path.");
                if (Directory.Exists(target)) throw new IOException("A folder occupies a required file: " + entry.Key);
                if (!File.Exists(target)) continue;
                using (var hash = SHA256.Create()) using (var input = File.OpenRead(target)) {
                    var actual = BitConverter.ToString(hash.ComputeHash(input)).Replace("-", "");
                    if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Existing file differs and has been preserved: " + entry.Key);
                }
                checkedCount++;
            }
            Console.WriteLine("Verified " + checkedCount + " existing model/runtime files.");
            return 0;
        } catch (Exception error) {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }
}
