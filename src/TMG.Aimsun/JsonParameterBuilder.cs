using System;
using System.Text;
using System.IO;
using Newtonsoft.Json;

namespace TMG.Aimsun
{
    public static class JsonParameterBuilder
    {
        public static string BuildParameters(Action<JsonTextWriter> toExecute)
        {
            using (var backing = new MemoryStream())
            {
                using (var textStream = new StreamWriter(backing, Encoding.UTF8))

                using (var writer = new JsonTextWriter(textStream))
                {
                    writer.WriteStartObject();
                    toExecute(writer);
                    writer.WriteEndObject();
                    writer.Flush();
                    return Encoding.UTF8.GetString(backing.ToArray());
                }
            } 
        }
    }
}
