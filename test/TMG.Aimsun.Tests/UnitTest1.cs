/*
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of XTMF.

    XTMF is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    XTMF is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XTMF.  If not, see <http://www.gnu.org/licenses/>.
*/

using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class UnitTest1
    {
        [Microsoft.VisualStudio.TestTools.UnitTesting.AssemblyCleanup]
        public static void testCleanUp()
        {
            //get modeller if modeller is not null dispose
            Helper.Modeller?.Dispose();
        }
        [Microsoft.VisualStudio.TestTools.UnitTesting.AssemblyInitialize]
        public static void InitTest(TestContext _)
        {
            //initalize the Aimsun module
            Helper.InitializeAimsun();
        }

        [TestMethod]
        public void Test1()
        {
            string test = "{'Name': 'test1', 'Name2':'test2'}";
            Helper.Modeller.Run(null, "Module1Test", test);
            Helper.Modeller.Run(null, "Module1Test2", test);
        }
    }
}


