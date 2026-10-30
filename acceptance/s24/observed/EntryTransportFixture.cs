// Native console transport fixture, never SSH/CIM/inventory or an arbitrary executor.
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Web.Script.Serialization;
public static class EntryTransportFixture {
    private static string Binding=new string('a',64), Challenge=new string('b',64);
    private static void Emit(string kind,string challenge,bool receipt) {
        Console.WriteLine("{\"kind\":\""+kind+"\",\"binding\":\""+Binding+
            "\",\"challenge\":\""+challenge+"\",\"r1_complete\":false,\"r2_authorized\":false,"+
            "\"authenticated\":false,\"complete_writer_coverage\":false,\"host_identity_proved\":false,"+
            "\"scope_granted\":false"+(receipt?",\"receipt_sha256\":\""+new string('c',64)+"\"":"")+"}");
    }
    public static int Main(string[] args) {
        if (args.Length<3 || args[0]!="-T" || args[args.Length-2]!="fixture@invalid" ||
            args[args.Length-1]!="'/fixture/python' -I -S -B '/fixture/observer.py' --config '/fixture/config.json'") return 2;
        foreach (string flag in new string[] {"BatchMode=yes","StrictHostKeyChecking=yes","UpdateHostKeys=no",
            "IdentitiesOnly=yes","IdentityAgent=none","ForwardAgent=no","ClearAllForwardings=yes",
            "ControlMaster=no","ControlPath=none","PermitLocalCommand=no","ConnectTimeout=5"})
            if (Array.IndexOf(args,flag)<0) return 2;
        string root=Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string trace=Path.Combine(root,"peer.trace");
        File.WriteAllText(trace,"started\n");
        if (File.ReadAllText(Path.Combine(root,"case.txt")).Trim()=="wrong_challenge") {
            Emit("sample_window_open",new string('d',64),false); return 0;
        }
        Emit("sample_window_open",Challenge,false);
        string line=Console.ReadLine();
        if (line==null || line.Length>2048) return 2;
        Dictionary<string,object> post=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(line);
        if (post.Count!=3 || !post.ContainsKey("kind") || !post.ContainsKey("binding") || !post.ContainsKey("challenge") ||
            !(post["kind"] is string) || (string)post["kind"]!="check_window_after" ||
            !(post["binding"] is string) || (string)post["binding"]!=Binding ||
            !(post["challenge"] is string) || (string)post["challenge"]!=Challenge) return 2;
        File.AppendAllText(trace,"post-received\n");
        Emit("window_confirmed",Challenge,false);
        Emit("observation_complete_pending_review",Challenge,true);
        return 0;
    }
}
