using System;
using System.Text;
using System.IO;
using Newtonsoft.Json;

namespace TMG.Aimsun
{
    /// <summary>
    /// Class to build the Parameters as a JSON
    /// </summary>
    public static class JsonParameterBuilder
    {
        public static string BuildParameters(Action<JsonTextWriter> toExecute)
        {
            using (var backing = new MemoryStream())
            {
                using (var textStream = new StreamWriter(backing, new UnicodeEncoding(false,false) ))
                using (var writer = new JsonTextWriter(textStream))
                {
                    writer.WriteStartObject();
                    toExecute(writer);
                    writer.WriteEndObject();
                    writer.Flush();
                    return Encoding.Unicode.GetString(backing.ToArray());
                }
            } 
        }
    }
}
