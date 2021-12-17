using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TMG.Aimsun
{
    public class AimsunControllerParameter
    {
        internal string Name;
        internal string Value;
        public AimsunControllerParameter(string name, string value)
        {
            Name = name;
            Value = value;
        }
    }
}