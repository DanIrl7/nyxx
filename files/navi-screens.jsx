import { useState, useEffect, useRef, useCallback } from "react";

export default function NaviScreens() {
  const [screen, setScreen] = useState("cd");
  const [cdSel, setCdSel]     = useState(2);
  const [jumpSel, setJumpSel] = useState(0);
  const [memoSel, setMemoSel] = useState(0);
  const canvasRef = useRef(null);

  // ── Sample data ────────────────────────────────────────
  const cdEntries = [
    { icon: "🔼", name: ".."              },
    { icon: "📁", name: "documents"       },
    { icon: "📁", name: "navii"           },
    { icon: "📁", name: "downloads"       },
    { icon: "🐍", name: "main.py"         },
    { icon: "📝", name: "README.md"       },
    { icon: "📄", name: "requirements.txt"},
    { icon: "🧾", name: "config.json"     },
    { icon: "⚙️", name: "setup.sh"        },
  ];

  const jumpEntries = [
    { name: "code",   desc: "my projects folder",       path: "~/projects/coding"  },
    { name: "home",   desc: "personal home directory",  path: "~/"                 },
    { name: "work",   desc: "work projects",            path: "~/work/projects"    },
  ];

  const memoEntries = [
    { name: "virtual", desc: "activate virtual environment",  cmd: "source venv/bin/activate"    },
    { name: "update",  desc: "update all pip packages",       cmd: "pip install --upgrade pip"   },
    { name: "serve",   desc: "start local dev server",        cmd: "python -m http.server 8000"  },
  ];

  // ── Draw starry background ─────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;

    ctx.fillStyle = "#010408";
    ctx.fillRect(0, 0, W, H);

    const stars = [
      { char: "✦", size: 11, w: 1 },
      { char: "✧", size: 10, w: 2 },
      { char: "·",  size: 9,  w: 7 },
      { char: "*",  size: 9,  w: 3 },
    ];
    const tw = stars.reduce((a, s) => a + s.w, 0);

    for (let i = 0; i < 300; i++) {
      const x = Math.random() * W;
      const y = Math.random() * (H * 0.82);
      let r = Math.random() * tw, star = stars[0];
      for (const s of stars) { r -= s.w; if (r <= 0) { star = s; break; } }
      const b = Math.random();
      ctx.font = `${star.size}px 'Courier New'`;
      ctx.fillStyle = `rgba(${130+b*70},${130+b*70},${190+b*55},${0.1+b*0.45})`;
      ctx.fillText(star.char, x, y);
    }

    ctx.font = "22px serif";
    ctx.fillStyle = "rgba(210,210,255,0.4)";
    ctx.fillText("◯", W - 58, 45);

    const bldgs = [[0,75],[60,118],[118,52],[174,132],[228,88],[288,106],[342,62],[398,122],[458,82],[522,112],[574,68],[634,98]];
    bldgs.forEach(([x, h]) => { ctx.fillStyle = "#04040e"; ctx.fillRect(x, H - h, 55, h); });

    const wins = [[8,H-55],[23,H-38],[68,H-88],[83,H-68],[83,H-48],[122,H-38],[179,H-108],[179,H-88],[194,H-68],[234,H-68],[249,H-48],[296,H-76],[311,H-56],[348,H-46],[404,H-92],[419,H-72],[404,H-52],[463,H-62],[478,H-42],[528,H-82],[543,H-62],[579,H-52],[640,H-72],[640,H-52]];
    wins.forEach(([x, y]) => {
      const b = Math.random();
      ctx.fillStyle = `rgba(${70+b*40},${70+b*40},${155+b*65},0.15)`;
      ctx.fillRect(x, y, 8, 11);
    });

    const grd = ctx.createLinearGradient(0, H-140, 0, H);
    grd.addColorStop(0, "rgba(8,8,30,0)");
    grd.addColorStop(1, "rgba(8,8,30,0.65)");
    ctx.fillStyle = grd;
    ctx.fillRect(0, H-140, W, 140);
  }, []);

  // ── Keyboard ───────────────────────────────────────────
  useEffect(() => {
    const map = { cd: [cdSel, setCdSel, cdEntries.length-1], jump: [jumpSel, setJumpSel, jumpEntries.length-1], memo: [memoSel, setMemoSel, memoEntries.length-1] };
    const onKey = (e) => {
      const [sel, set, max] = map[screen] || [];
      if (!set) return;
      if (e.key === "ArrowUp")   set(s => Math.max(0, s-1));
      if (e.key === "ArrowDown") set(s => Math.min(max, s+1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [screen, cdSel, jumpSel, memoSel]);

  // ── Shared styles ──────────────────────────────────────
  const mono = "'Courier New', monospace";
  const panel = { position:"absolute", top:"50%", left:"50%", transform:"translate(-50%,-52%)", background:"rgba(1,3,10,0.95)", border:"1px solid #22224e", borderRadius:7, width:490, overflow:"hidden", fontFamily:mono };
  const hdr = (extra={}) => ({ padding:"10px 16px", borderBottom:"1px solid #0e0e22", fontSize:11, color:"#8888de", fontWeight:"bold", display:"flex", alignItems:"center", gap:8, ...extra });
  const row = (sel) => ({ padding:"9px 16px", background:sel?"#111128":"transparent", borderLeft:`2px solid ${sel?"#4848a0":"transparent"}`, cursor:"pointer", display:"flex", alignItems:"center", gap:10 });
  const ftr = { borderTop:"1px solid #0e0e22", padding:"7px 16px", display:"flex", gap:16, fontSize:9, color:"#16163a", letterSpacing:1 };
  const sel_text   = (s) => s ? "#9090e0" : "#2a2a5a";
  const arrow      = (s) => <span style={{fontSize:11,color:s?"#7070c8":"#1a1a38",width:14,flexShrink:0}}>{s?"▸":""}</span>;

  // ── CD panel ───────────────────────────────────────────
  const CdPanel = () => (
    <div style={panel}>
      <div style={hdr()}>
        <span>📂</span>
        <span style={{color:"#9090e0"}}>~/projects/coding</span>
      </div>
      <div style={{padding:"4px 0"}}>
        {cdEntries.map((e,i) => (
          <div key={e.name} onClick={()=>setCdSel(i)} style={row(i===cdSel)}>
            {arrow(i===cdSel)}
            <span style={{fontSize:13,lineHeight:1}}>{e.icon}</span>
            <span style={{fontSize:11,color:sel_text(i===cdSel),fontWeight:i===cdSel?"bold":"normal"}}>{e.name}</span>
          </div>
        ))}
      </div>
      <div style={{borderTop:"1px solid #0e0e22",padding:"6px 16px",fontSize:10,color:"#3a3a72"}}>
        → ~/projects/coding/{cdEntries[cdSel]?.name === ".." ? "(go up)" : cdEntries[cdSel]?.name}
      </div>
      <div style={ftr}>
        <span>↑↓ navigate</span><span>→ enter dir</span><span>← go back</span><span>SPC jump here</span><span>. hidden</span><span>q quit</span>
      </div>
    </div>
  );

  // ── Jump panel ─────────────────────────────────────────
  const JumpPanel = () => (
    <div style={panel}>
      <div style={hdr()}>
        <span>📌</span><span>saved locations</span>
        <span style={{marginLeft:"auto",fontSize:9,color:"#20203a",fontWeight:"normal"}}>{jumpEntries.length} saved</span>
      </div>
      <div style={{padding:"4px 0"}}>
        {jumpEntries.map((e,i) => (
          <div key={e.name} onClick={()=>setJumpSel(i)} style={{...row(i===jumpSel),flexDirection:"column",alignItems:"flex-start",gap:3,padding:"11px 16px"}}>
            <div style={{display:"flex",alignItems:"center",gap:10,width:"100%"}}>
              {arrow(i===jumpSel)}
              <span style={{fontSize:11,color:sel_text(i===jumpSel),fontWeight:"bold",minWidth:56}}>{e.name}</span>
              <span style={{fontSize:10,color:i===jumpSel?"#4848a0":"#181838"}}>{e.desc}</span>
            </div>
            <div style={{paddingLeft:24,fontSize:9,color:i===jumpSel?"#36367a":"#141430"}}>{e.path}</div>
          </div>
        ))}
      </div>
      <div style={{...ftr,gap:20}}>
        <span>↑↓ navigate</span><span>enter jump here</span><span>d delete</span><span>q quit</span>
      </div>
    </div>
  );

  // ── Memo panel ─────────────────────────────────────────
  const MemoPanel = () => (
    <div style={panel}>
      <div style={hdr()}>
        <span>📝</span><span>saved commands</span>
        <span style={{marginLeft:"auto",fontSize:9,color:"#20203a",fontWeight:"normal"}}>{memoEntries.length} saved</span>
      </div>
      <div style={{padding:"4px 0"}}>
        {memoEntries.map((e,i) => (
          <div key={e.name} onClick={()=>setMemoSel(i)} style={{...row(i===memoSel),flexDirection:"column",alignItems:"flex-start",gap:4,padding:"11px 16px"}}>
            <div style={{display:"flex",alignItems:"center",gap:10,width:"100%"}}>
              {arrow(i===memoSel)}
              <span style={{fontSize:11,color:sel_text(i===memoSel),fontWeight:"bold",minWidth:56}}>{e.name}</span>
              <span style={{fontSize:10,color:i===memoSel?"#4848a0":"#181838"}}>{e.desc}</span>
            </div>
            <div style={{paddingLeft:24,fontSize:9,color:i===memoSel?"#5050a8":"#141430",fontStyle:"italic"}}>$ {e.cmd}</div>
          </div>
        ))}
      </div>
      <div style={{...ftr,gap:20}}>
        <span>↑↓ navigate</span><span>enter run command</span><span>d delete</span><span>q quit</span>
      </div>
    </div>
  );

  const tabs = ["cd","jump","memo"];

  return (
    <div style={{background:"#00000a",padding:20,fontFamily:mono}}>
      {/* Tab bar */}
      <div style={{display:"flex",gap:6,marginBottom:14,justifyContent:"center"}}>
        {tabs.map(t => (
          <button key={t} onClick={()=>setScreen(t)} style={{
            background: screen===t?"#111128":"transparent",
            border:`1px solid ${screen===t?"#4848a0":"#16163a"}`,
            color: screen===t?"#8888de":"#303060",
            padding:"5px 22px", borderRadius:4, cursor:"pointer",
            fontSize:11, fontFamily:mono, letterSpacing:2,
          }}>{t}</button>
        ))}
      </div>

      {/* Terminal */}
      <div style={{borderRadius:10,overflow:"hidden",border:"1px solid #16163a",maxWidth:680,margin:"0 auto",boxShadow:"0 0 60px rgba(30,30,80,0.4)"}}>
        <div style={{background:"#07070f",padding:"8px 14px",display:"flex",alignItems:"center",gap:6,borderBottom:"1px solid #0e0e20"}}>
          <span style={{width:12,height:12,borderRadius:"50%",background:"#2e1212",display:"inline-block"}}/>
          <span style={{width:12,height:12,borderRadius:"50%",background:"#2e2412",display:"inline-block"}}/>
          <span style={{width:12,height:12,borderRadius:"50%",background:"#12261a",display:"inline-block"}}/>
          <span style={{fontSize:11,color:"#20204a",marginLeft:10,letterSpacing:3}}>navi — {screen}</span>
        </div>
        <div style={{position:"relative"}}>
          <canvas ref={canvasRef} width={680} height={440} style={{display:"block"}}/>
          {screen==="cd"   && <CdPanel/>}
          {screen==="jump" && <JumpPanel/>}
          {screen==="memo" && <MemoPanel/>}
        </div>
      </div>

      <p style={{textAlign:"center",fontSize:10,color:"#20204a",marginTop:10,fontFamily:"sans-serif",letterSpacing:1}}>
        click a tab above or press ↑ ↓ to move selection
      </p>
    </div>
  );
}
