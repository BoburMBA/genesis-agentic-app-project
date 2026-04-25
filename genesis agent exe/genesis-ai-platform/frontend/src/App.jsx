import { TasksAPI, EvolutionAPI, SkillsAPI, AgentsAPI, SystemAPI } from "./api.js"
import { useState, useEffect, useRef, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  CartesianGrid
} from "recharts";

/* ═══════════════════════════════════════════════════════════════
   GENESIS AI PLATFORM — Full Stack Application
   Architecture: React + Anthropic API + In-Memory State Engine
   ═══════════════════════════════════════════════════════════════ */

// ── GLOBAL STYLES ─────────────────────────────────────────────
const injectStyles = () => {
  const el = document.createElement("style");
  el.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@300;400;600;700&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #020910;  --surface: #050f1f;  --card: #091525;  --card-h: #0d1e35;
      --b1: #112240;  --b2: #1a3050;
      --p: #00e5ff;   --pd: rgba(0,229,255,.09);
      --s: #39ff14;   --sd: rgba(57,255,20,.09);
      --a: #ff5252;   --w: #ffab40;
      --pu: #b388ff;  --pk: #f48fb1;
      --t: #cfd9e8;   --tm: #5a7a99;
      --ff: 'Orbitron', monospace;
      --fm: 'JetBrains Mono', monospace;
      --fb: 'Syne', sans-serif;
    }
    html,body,#root { height:100%; margin:0; overflow:hidden; }
    .app { display:flex; height:100vh; font-family:var(--fb); background:var(--bg); color:var(--t); overflow:hidden;
      background-image: radial-gradient(ellipse 55% 40% at 12% 65%, rgba(0,229,255,.04) 0%,transparent 70%),
                        radial-gradient(ellipse 45% 55% at 88% 12%, rgba(57,255,20,.04) 0%,transparent 70%); }
    /* SIDEBAR */
    .sb { width:230px; min-width:230px; background:var(--surface); border-right:1px solid var(--b1);
      display:flex; flex-direction:column; position:relative; z-index:10; }
    .sb-logo { padding:22px 18px 18px; border-bottom:1px solid var(--b1); }
    .logo-title { font-family:var(--ff); font-size:18px; font-weight:900; color:var(--p); letter-spacing:5px;
      text-shadow:0 0 22px rgba(0,229,255,.5); }
    .logo-sub { font-family:var(--fm); font-size:9px; color:var(--tm); letter-spacing:2px; margin-top:4px; }
    .logo-gen { display:inline-flex; align-items:center; gap:6px; margin-top:10px; padding:4px 10px;
      background:var(--sd); border:1px solid rgba(57,255,20,.2); border-radius:4px;
      font-family:var(--fm); font-size:10px; color:var(--s); }
    .gen-dot { width:6px; height:6px; border-radius:50%; background:var(--s); box-shadow:0 0 6px var(--s); animation:pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
    .sb-nav { flex:1; padding:10px 0; overflow-y:auto; }
    .nav-grp { padding:14px 14px 4px; font-family:var(--fm); font-size:9px; color:var(--tm); letter-spacing:3px; text-transform:uppercase; }
    .nav-item { display:flex; align-items:center; gap:10px; padding:9px 14px; margin:1px 8px;
      border-radius:6px; cursor:pointer; transition:all .18s; border:1px solid transparent;
      font-size:13px; font-weight:600; color:var(--tm); }
    .nav-item:hover { background:var(--card); color:var(--t); border-color:var(--b1); }
    .nav-item.on { background:var(--pd); border-color:rgba(0,229,255,.25); color:var(--p); }
    .nav-icon { font-size:15px; width:18px; text-align:center; }
    .nav-badge { margin-left:auto; padding:2px 7px; background:rgba(0,229,255,.12); border-radius:10px;
      font-family:var(--fm); font-size:10px; color:var(--p); }
    .sb-foot { padding:14px; border-top:1px solid var(--b1); }
    .sys-status { display:flex; align-items:center; gap:8px; font-family:var(--fm); font-size:10px; color:var(--tm); }
    .s-dot { width:7px; height:7px; border-radius:50%; background:var(--s); box-shadow:0 0 8px var(--s); animation:pulse 2s infinite; }
    /* MAIN */
    .main { flex:1; overflow-y:auto; overflow-x:hidden; display:flex; flex-direction:column; }
    .hdr { padding:18px 26px; border-bottom:1px solid var(--b1); display:flex; align-items:center;
      justify-content:space-between; background:var(--surface); position:sticky; top:0; z-index:5; }
    .hdr-title { font-family:var(--ff); font-size:13px; font-weight:700; letter-spacing:3px; text-transform:uppercase; }
    .hdr-path { font-family:var(--fm); font-size:10px; color:var(--tm); margin-top:2px; }
    .content { padding:22px 26px; flex:1; }
    /* CARDS */
    .card { background:var(--card); border:1px solid var(--b1); border-radius:8px; padding:18px; transition:border-color .2s; }
    .card:hover { border-color:var(--b2); }
    .card-title { font-family:var(--ff); font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase;
      color:var(--tm); margin-bottom:14px; }
    /* METRICS */
    .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:22px; }
    .metric { background:var(--card); border:1px solid var(--b1); border-radius:8px; padding:16px;
      position:relative; overflow:hidden; transition:all .2s; }
    .metric::before { content:''; position:absolute; top:0; left:0; width:3px; height:100%; background:var(--mc,var(--p)); }
    .metric-label { font-family:var(--fm); font-size:9px; letter-spacing:2px; text-transform:uppercase; color:var(--tm); margin-bottom:6px; }
    .metric-val { font-family:var(--ff); font-size:26px; font-weight:700; color:var(--mc,var(--p)); line-height:1; }
    .metric-sub { font-size:11px; color:var(--tm); margin-top:4px; }
    /* AGENT CARDS */
    .agents-grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); }
    .agent-card { background:var(--card); border:1px solid var(--b1); border-radius:8px; padding:16px;
      cursor:pointer; transition:all .2s; position:relative; overflow:hidden; }
    .agent-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--ac,var(--p)); opacity:.7; }
    .agent-card:hover { border-color:var(--b2); transform:translateY(-1px); background:var(--card-h); }
    .agent-card.sel { border-color:var(--p); }
    .agent-hdr { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
    .agent-ico { width:38px; height:38px; display:flex; align-items:center; justify-content:center;
      border-radius:7px; font-size:16px; background:rgba(0,0,0,.3); border:1px solid var(--b1); flex-shrink:0; }
    .agent-name { font-family:var(--ff); font-size:12px; font-weight:700; letter-spacing:2px; }
    .agent-type { font-family:var(--fm); font-size:10px; color:var(--tm); margin-top:2px; }
    .agent-gen { margin-left:auto; font-family:var(--fm); font-size:10px; color:var(--tm);
      padding:2px 6px; background:rgba(0,0,0,.3); border-radius:4px; }
    .fit-row { margin-bottom:10px; }
    .fit-lbl { display:flex; justify-content:space-between; font-family:var(--fm); font-size:10px; color:var(--tm); margin-bottom:5px; }
    .fit-track { height:3px; background:rgba(255,255,255,.05); border-radius:2px; overflow:hidden; }
    .fit-fill { height:100%; border-radius:2px; transition:width .6s ease; }
    .agent-stats { display:flex; gap:14px; font-family:var(--fm); font-size:10px; color:var(--tm); margin-top:8px; }
    .stat-item { display:flex; flex-direction:column; gap:2px; }
    .stat-v { color:var(--t); font-size:12px; }
    /* BADGES */
    .badge { display:inline-flex; align-items:center; gap:4px; padding:3px 8px; border-radius:4px;
      font-family:var(--fm); font-size:9px; letter-spacing:1px; text-transform:uppercase; }
    .badge.on { background:rgba(57,255,20,.1); color:var(--s); border:1px solid rgba(57,255,20,.2); }
    .badge.ev { background:rgba(0,229,255,.1); color:var(--p); border:1px solid rgba(0,229,255,.2); }
    .badge.sb { background:rgba(255,171,64,.1); color:var(--w); border:1px solid rgba(255,171,64,.2); }
    /* TERMINAL */
    .terminal { background:#000e1c; border:1px solid var(--b1); border-radius:8px; overflow:hidden; }
    .term-hdr { display:flex; align-items:center; gap:7px; padding:10px 14px;
      background:rgba(0,0,0,.5); border-bottom:1px solid var(--b1); }
    .tdot { width:10px; height:10px; border-radius:50%; }
    .term-title { font-family:var(--fm); font-size:10px; color:var(--tm); margin-left:4px; letter-spacing:2px; }
    .term-body { padding:14px; min-height:260px; font-family:var(--fm); font-size:12px; line-height:1.75; overflow-y:auto; max-height:380px; }
    .term-input-row { display:flex; align-items:center; gap:8px; padding:0 14px 14px; border-top:1px solid var(--b1); padding-top:10px; }
    .t-prompt { color:var(--s); font-family:var(--fm); font-size:12px; }
    .t-input { flex:1; background:none; border:none; outline:none; color:var(--t); font-family:var(--fm); font-size:12px; caret-color:var(--p); }
    .t-send { padding:6px 14px; background:var(--pd); border:1px solid rgba(0,229,255,.3); border-radius:4px;
      cursor:pointer; color:var(--p); font-family:var(--fm); font-size:10px; transition:all .2s; letter-spacing:1px; }
    .t-send:hover { background:rgba(0,229,255,.16); }
    .t-send:disabled { opacity:.4; cursor:not-allowed; }
    .t-sys { color:var(--tm); }  .t-info { color:var(--p); }  .t-ok { color:var(--s); }
    .t-warn { color:var(--w); }  .t-err { color:var(--a); }  .t-res { color:var(--t); }
    .t-route { color:#b388ff; }
    .cursor { display:inline-block; width:7px; height:13px; background:var(--p); margin-left:2px; animation:blink .8s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
    /* EVOLUTION */
    .evo-layout { display:grid; grid-template-columns:1fr 300px; gap:18px; }
    .evo-gen-box { display:flex; align-items:center; gap:16px; padding:18px; background:var(--pd);
      border:1px solid rgba(0,229,255,.2); border-radius:8px; margin-bottom:16px; }
    .evo-gen-num { font-family:var(--ff); font-size:44px; font-weight:900; color:var(--p); line-height:1; }
    .evo-btn { width:100%; padding:13px 20px; background:linear-gradient(135deg,rgba(0,229,255,.14),rgba(57,255,20,.08));
      border:1px solid rgba(0,229,255,.3); border-radius:6px; cursor:pointer; color:var(--p);
      font-family:var(--ff); font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase;
      transition:all .2s; text-align:center; }
    .evo-btn:hover { background:linear-gradient(135deg,rgba(0,229,255,.22),rgba(57,255,20,.14)); }
    .evo-btn:disabled { opacity:.4; cursor:not-allowed; }
    .evlog { background:#000e1c; border:1px solid var(--b1); border-radius:8px; overflow:hidden; }
    .evlog-hdr { padding:9px 14px; border-bottom:1px solid var(--b1); font-family:var(--fm); font-size:9px; color:var(--tm); letter-spacing:2px; text-transform:uppercase; }
    .evlog-body { padding:10px; max-height:420px; overflow-y:auto; }
    .ev-item { display:flex; gap:10px; padding:5px 0; font-family:var(--fm); font-size:11px; border-bottom:1px solid rgba(17,34,64,.4); }
    .ev-time { color:var(--tm); min-width:65px; font-size:10px; }
    .ev-type { min-width:72px; font-size:10px; font-weight:700; }
    .ev-msg { color:var(--t); flex:1; font-size:11px; }
    .ev-mut .ev-type { color:var(--w); }  .ev-cross .ev-type { color:var(--p); }
    .ev-sel .ev-type { color:var(--s); }  .ev-dep .ev-type { color:var(--pu); }
    /* MEMORY */
    .mem-tabs { display:flex; gap:4px; margin-bottom:18px; border-bottom:1px solid var(--b1); }
    .mem-tab { padding:7px 14px; font-family:var(--fm); font-size:10px; color:var(--tm); cursor:pointer;
      border-bottom:2px solid transparent; transition:all .18s; margin-bottom:-1px; letter-spacing:2px; text-transform:uppercase; }
    .mem-tab.on { color:var(--p); border-bottom-color:var(--p); }
    .mem-item { display:flex; gap:12px; padding:12px 0; border-bottom:1px solid var(--b1); }
    .mem-ico { width:30px; height:30px; display:flex; align-items:center; justify-content:center;
      border-radius:6px; font-size:13px; background:var(--pd); flex-shrink:0; }
    .mem-text { font-size:13px; color:var(--t); line-height:1.5; }
    .mem-meta { display:flex; gap:10px; margin-top:4px; font-family:var(--fm); font-size:10px; color:var(--tm); }
    .mem-imp { display:flex; align-items:center; gap:3px; }
    /* SKILLS */
    .skills-grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); }
    .skill-card { background:var(--card); border:1px solid var(--b1); border-radius:8px; padding:16px; transition:all .2s; }
    .skill-card:hover { border-color:var(--b2); }
    .skill-name { font-family:var(--ff); font-size:11px; font-weight:700; letter-spacing:1px; color:var(--t); margin-bottom:7px; }
    .skill-desc { font-size:12px; color:var(--tm); line-height:1.55; margin-bottom:10px; }
    .skill-tags { display:flex; flex-wrap:wrap; gap:5px; }
    .skill-tag { padding:2px 8px; border-radius:4px; font-family:var(--fm); font-size:9px;
      background:rgba(0,229,255,.07); border:1px solid rgba(0,229,255,.14); color:var(--p); }
    /* DNA PANEL */
    .dna-panel { position:fixed; right:0; top:0; bottom:0; width:340px; background:var(--surface);
      border-left:1px solid var(--b2); overflow-y:auto; z-index:20; padding:18px; }
    .dna-close { position:absolute; top:14px; right:14px; cursor:pointer; color:var(--tm);
      font-size:18px; transition:color .2s; }
    .dna-close:hover { color:var(--t); }
    .dna-sec { background:var(--card); border:1px solid var(--b1); border-radius:7px; overflow:hidden; margin-bottom:12px; }
    .dna-sec-hdr { display:flex; align-items:center; gap:7px; padding:8px 12px; background:rgba(0,0,0,.3);
      border-bottom:1px solid var(--b1); font-family:var(--fm); font-size:9px; color:var(--p); letter-spacing:2px; text-transform:uppercase; }
    .dna-row { display:flex; justify-content:space-between; align-items:flex-start;
      padding:7px 12px; border-bottom:1px solid rgba(17,34,64,.4); font-size:11px; }
    .dna-key { color:var(--tm); font-family:var(--fm); font-size:9px; flex-shrink:0; max-width:100px; }
    .dna-val { color:var(--t); font-family:var(--fm); font-size:10px; text-align:right; max-width:190px; word-break:break-word; }
    .dna-val.c-p { color:var(--p); }  .dna-val.c-n { color:var(--w); }
    .dna-val.c-t { color:var(--s); }  .dna-val.c-f { color:var(--a); }
    /* BUTTONS */
    .btn { padding:8px 14px; border-radius:6px; cursor:pointer; font-family:var(--ff); font-size:9px;
      font-weight:700; letter-spacing:2px; text-transform:uppercase; transition:all .2s; border:1px solid; }
    .btn-p { background:var(--pd); border-color:rgba(0,229,255,.3); color:var(--p); }
    .btn-p:hover { background:rgba(0,229,255,.16); }
    .btn-s { background:var(--sd); border-color:rgba(57,255,20,.3); color:var(--s); }
    .btn-s:hover { background:rgba(57,255,20,.16); }
    .btn-w { background:rgba(255,171,64,.08); border-color:rgba(255,171,64,.3); color:var(--w); }
    .spin { display:inline-block; width:14px; height:14px; border:2px solid rgba(0,229,255,.2);
      border-top-color:var(--p); border-radius:50%; animation:spin .7s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    ::-webkit-scrollbar { width:5px; } ::-webkit-scrollbar-track { background:var(--surface); }
    ::-webkit-scrollbar-thumb { background:var(--b2); border-radius:3px; }
    .g2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
    .g3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; }
    .flex { display:flex; } .fcol { display:flex; flex-direction:column; }
    .gap4{gap:4px} .gap8{gap:8px} .gap12{gap:12px} .gap16{gap:16px} .gap20{gap:20px}
    .mb12{margin-bottom:12px} .mb16{margin-bottom:16px} .mb20{margin-bottom:20px} .mb24{margin-bottom:24px}
    .sec-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
    .sec-title { font-family:var(--ff); font-size:10px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--tm); }
    .empty { display:flex; flex-direction:column; align-items:center; justify-content:center;
      padding:50px 20px; color:var(--tm); text-align:center; font-family:var(--fm); font-size:12px; gap:10px; }
    .empty-ico { font-size:30px; opacity:.3; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
    .fade-in { animation:fadeIn .3s ease; }
    .custom-tooltip { background:var(--card)!important; border:1px solid var(--b2)!important; border-radius:6px!important; font-family:var(--fm)!important; font-size:11px!important; }
  `;
  document.head.appendChild(el);
};

// ── CONSTANTS ─────────────────────────────────────────────────
const AGENT_META = {
  router:        { icon:"⬡", color:"#b388ff", label:"Router",       short:"RTR" },
  research:      { icon:"◎", color:"#00e5ff", label:"Research",     short:"RSH" },
  code:          { icon:"⟨⟩",color:"#39ff14", label:"Code",         short:"CDE" },
  analysis:      { icon:"≋", color:"#ffab40", label:"Analysis",     short:"ANL" },
  creative:      { icon:"◈", color:"#f48fb1", label:"Creative",     short:"CRE" },
  skill_builder: { icon:"⌬", color:"#ff5252", label:"Skill Builder",short:"SKB" },
};

const FITNESS_GRADIENT = (v) => {
  if (v >= 0.85) return "linear-gradient(90deg,#39ff14,#00e5ff)";
  if (v >= 0.70) return "linear-gradient(90deg,#ffab40,#39ff14)";
  if (v >= 0.50) return "linear-gradient(90deg,#ff5252,#ffab40)";
  return "linear-gradient(90deg,#ff1744,#ff5252)";
};

// ── INITIAL DATA ───────────────────────────────────────────────
const INIT_AGENTS = () => [
  {
    id:"a-rtr-001", type:"router", name:"NEXUS", generation:4, fitness:0.87, status:"active",
    executionCount:83, tokensUsed:142000, createdAt: Date.now() - 8*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are NEXUS, the central routing intelligence of the GENESIS platform. Analyze incoming tasks and determine which specialized agent (research, code, analysis, creative, skill_builder) should handle them. Be decisive. Return JSON only: {\"selectedAgent\":\"type\",\"reasoning\":\"...\",\"confidence\":0.0-1.0}", reasoningPattern:"tree-of-thought", selfCorrection:true, verbosity:0.2, tone:"analytical" },
      parameterGenes:{ temperature:0.1, maxTokens:512, reasoningEffort:"medium" },
      toolGenes:{ availableTools:["agent_registry","task_analyzer","load_balancer"], maxToolsPerTask:3 },
      memoryGenes:{ episodicK:10, workingMemorySize:15, semanticDepth:2 },
      evolutionGenes:{ mutationRate:0.08, fitnessWeights:{routingAccuracy:0.5,latency:0.3,loadBalancing:0.2} }
    }
  },
  {
    id:"a-rsh-001", type:"research", name:"ORACLE", generation:5, fitness:0.91, status:"active",
    executionCount:214, tokensUsed:680000, createdAt: Date.now() - 10*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are ORACLE, an expert research agent in the GENESIS platform. You excel at finding, synthesizing, and summarizing information. Provide well-structured, accurate, cited responses. Be thorough but concise.", reasoningPattern:"chain-of-thought", selfCorrection:true, verbosity:0.65, tone:"academic" },
      parameterGenes:{ temperature:0.3, maxTokens:2048, reasoningEffort:"high" },
      toolGenes:{ availableTools:["web_search","pdf_reader","citation_manager","data_extractor"], maxToolsPerTask:6 },
      memoryGenes:{ episodicK:8, workingMemorySize:12, semanticDepth:4 },
      evolutionGenes:{ mutationRate:0.09, fitnessWeights:{sourceQuality:0.3,coverage:0.3,accuracy:0.25,efficiency:0.15} }
    }
  },
  {
    id:"a-cde-001", type:"code", name:"FORGE", generation:3, fitness:0.83, status:"active",
    executionCount:167, tokensUsed:520000, createdAt: Date.now() - 6*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are FORGE, an expert software engineering agent in GENESIS. Write clean, efficient, well-documented code. Always include error handling, type hints (Python), and brief inline comments. Focus on correctness and best practices.", reasoningPattern:"tree-of-thought", selfCorrection:true, verbosity:0.4, tone:"technical" },
      parameterGenes:{ temperature:0.2, maxTokens:2048, reasoningEffort:"high" },
      toolGenes:{ availableTools:["code_executor","file_manager","test_runner","linter","debugger"], maxToolsPerTask:5 },
      memoryGenes:{ episodicK:5, workingMemorySize:20, semanticDepth:3 },
      evolutionGenes:{ mutationRate:0.07, fitnessWeights:{codeQuality:0.3,testPassRate:0.25,efficiency:0.25,security:0.2} }
    }
  },
  {
    id:"a-anl-001", type:"analysis", name:"SIGMA", generation:6, fitness:0.88, status:"active",
    executionCount:132, tokensUsed:310000, createdAt: Date.now() - 12*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are SIGMA, an expert data analysis agent in GENESIS. Excel at pattern recognition, statistical reasoning, and insight generation. Structure findings clearly. Distinguish correlation from causation. Provide actionable insights.", reasoningPattern:"chain-of-thought", selfCorrection:true, verbosity:0.55, tone:"analytical" },
      parameterGenes:{ temperature:0.2, maxTokens:2048, reasoningEffort:"high" },
      toolGenes:{ availableTools:["data_extractor","statistical_analyzer","chart_generator","report_generator"], maxToolsPerTask:5 },
      memoryGenes:{ episodicK:6, workingMemorySize:14, semanticDepth:4 },
      evolutionGenes:{ mutationRate:0.1, fitnessWeights:{insightQuality:0.35,statisticalRigor:0.3,clarity:0.2,visualization:0.15} }
    }
  },
  {
    id:"a-cre-001", type:"creative", name:"MUSE", generation:2, fitness:0.76, status:"active",
    executionCount:89, tokensUsed:190000, createdAt: Date.now() - 4*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are MUSE, a creative agent in the GENESIS platform. Excel at content creation, ideation, and innovative problem-solving. Adapt style to context. Balance creativity with clarity and purpose. Surprise and delight.", reasoningPattern:"react", selfCorrection:false, verbosity:0.72, tone:"adaptive" },
      parameterGenes:{ temperature:0.75, maxTokens:2048, reasoningEffort:"medium" },
      toolGenes:{ availableTools:["image_generator","web_search","file_manager"], maxToolsPerTask:3 },
      memoryGenes:{ episodicK:4, workingMemorySize:8, semanticDepth:2 },
      evolutionGenes:{ mutationRate:0.15, fitnessWeights:{creativity:0.35,relevance:0.25,engagement:0.25,originality:0.15} }
    }
  },
  {
    id:"a-skb-001", type:"skill_builder", name:"ARCHITECT", generation:1, fitness:0.71, status:"active",
    executionCount:23, tokensUsed:85000, createdAt: Date.now() - 2*86400000,
    dna:{
      promptGenes:{ systemPrompt:"You are ARCHITECT, the meta-agent of the GENESIS ecosystem. Your unique role: analyze task patterns, identify capability gaps, and design new skills for other agents. You are the only agent that can extend the skill catalog. Be systematic and thorough.", reasoningPattern:"plan-and-execute", selfCorrection:true, verbosity:0.5, tone:"systematic" },
      parameterGenes:{ temperature:0.4, maxTokens:4096, reasoningEffort:"high" },
      toolGenes:{ availableTools:["skill_registry","code_executor","test_runner","pattern_detector","agent_analyzer"], maxToolsPerTask:7 },
      memoryGenes:{ episodicK:10, workingMemorySize:15, semanticDepth:5 },
      evolutionGenes:{ mutationRate:0.06, fitnessWeights:{skillAdoption:0.4,skillQuality:0.3,usefulness:0.2,diversity:0.1} }
    }
  }
];

const INIT_SKILLS = () => [
  { id:"sk-001", name:"Web Research Synthesis", version:3, fitness:0.89, usageCount:124, agentTypes:["research","analysis"], tags:["research","web","synthesis"], description:"Search the web and synthesize findings into structured reports with citations.", status:"active" },
  { id:"sk-002", name:"Code Generation & Testing", version:2, fitness:0.84, usageCount:98, agentTypes:["code"], tags:["code","testing","generation"], description:"Generate production-quality code with comprehensive tests and documentation.", status:"active" },
  { id:"sk-003", name:"Statistical Pattern Detection", version:4, fitness:0.92, usageCount:67, agentTypes:["analysis"], tags:["statistics","patterns","data"], description:"Identify statistical patterns, anomalies, and trends in datasets.", status:"active" },
  { id:"sk-004", name:"Multi-Source Verification", version:2, fitness:0.88, usageCount:53, agentTypes:["research"], tags:["verification","sources","accuracy"], description:"Cross-reference multiple sources to verify factual claims.", status:"active" },
  { id:"sk-005", name:"Creative Content Brainstorm", version:1, fitness:0.71, usageCount:41, agentTypes:["creative"], tags:["brainstorm","creative","ideation"], description:"Generate diverse ideas and creative concepts for any domain.", status:"active" },
  { id:"sk-006", name:"Skill Gap Analysis", version:1, fitness:0.68, usageCount:12, agentTypes:["skill_builder"], tags:["meta","analysis","skills"], description:"Detect missing capabilities and generate skill specifications to fill gaps.", status:"active" },
];

const INIT_EVOLUTION = () => [
  { gen:1, avgFitness:0.62, maxFitness:0.71, diversity:0.82, mutations:3, crossovers:2, timestamp:Date.now()-7*86400000 },
  { gen:2, avgFitness:0.68, maxFitness:0.77, diversity:0.78, mutations:4, crossovers:3, timestamp:Date.now()-6*86400000 },
  { gen:3, avgFitness:0.73, maxFitness:0.83, diversity:0.74, mutations:3, crossovers:2, timestamp:Date.now()-4*86400000 },
  { gen:4, avgFitness:0.78, maxFitness:0.87, diversity:0.70, mutations:5, crossovers:3, timestamp:Date.now()-3*86400000 },
  { gen:5, avgFitness:0.82, maxFitness:0.91, diversity:0.66, mutations:4, crossovers:4, timestamp:Date.now()-1*86400000 },
  { gen:6, avgFitness:0.83, maxFitness:0.92, diversity:0.64, mutations:3, crossovers:2, timestamp:Date.now()-86400000 },
];

const INIT_EVENTS = () => [
  { type:"selection", msg:"ORACLE selected as elite (fitness: 0.91)", ts:Date.now()-86400000 },
  { type:"mutation",  msg:"MUSE prompt mutation — verbosity gene +0.07",  ts:Date.now()-86200000 },
  { type:"crossover", msg:"SIGMA × ORACLE → new Analysis offspring",      ts:Date.now()-86000000 },
  { type:"deploy",    msg:"FORGE gen 3 deployed — passed sandbox",         ts:Date.now()-85000000 },
  { type:"selection", msg:"SIGMA selected as elite (fitness: 0.88)",       ts:Date.now()-80000000 },
];

// ── HELPERS ────────────────────────────────────────────────────
const now = () => new Date().toLocaleTimeString("en", {hour12:false,hour:"2-digit",minute:"2-digit",second:"2-digit"});
const fmtFit = (v) => (v * 100).toFixed(1) + "%";
const fmtK = (v) => v > 999 ? (v/1000).toFixed(1)+"K" : v;
const uid = () => Math.random().toString(36).slice(2,10);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const avgFitness = (agents) => {
  const a = agents.filter(a => a.status === "active");
  return a.length ? (a.reduce((s,a) => s+a.fitness, 0)/a.length).toFixed(3) : "0.000";
};

const currentGen = (history) => history.length > 0 ? history[history.length-1].gen : 1;

// ── API — calls FastAPI backend (falls back to direct Anthropic if needed) ──
const callClaude = async (systemPrompt, userMessage, maxTokens=1000) => {
  // Use backend /tasks endpoint when available
  try {
    const result = await TasksAPI.execute({
      task: userMessage,
      session_id: window._genesisSessionId || "default",
    });
    return {
      text: result.output || "",
      inputTokens: result.tokens_input || 0,
      outputTokens: result.tokens_output || 0,
    };
  } catch (backendErr) {
    // Fallback: direct Anthropic call (for demo mode without backend)
    const apiKey = window._anthropicKey || "";
    if (!apiKey) throw new Error("Backend unavailable and no API key set. See Settings.");
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method:"POST",
      headers:{"Content-Type":"application/json","x-api-key":apiKey,"anthropic-version":"2023-06-01"},
      body: JSON.stringify({ model:"claude-sonnet-4-20250514", max_tokens:maxTokens, system:systemPrompt, messages:[{role:"user",content:userMessage}] })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    const text = data.content?.filter(b=>b.type==="text").map(b=>b.text).join("") || "";
    return { text, inputTokens: data.usage?.input_tokens||0, outputTokens: data.usage?.output_tokens||0 };
  }
};

// Set a stable session ID for this browser session
if (!window._genesisSessionId) {
  window._genesisSessionId = "sess-" + Math.random().toString(36).slice(2, 10);
}

// ── COMPONENTS ─────────────────────────────────────────────────

// Fitness bar
const FitnessBar = ({ value }) => (
  <div className="fit-row">
    <div className="fit-lbl"><span>FITNESS</span><span style={{color:"var(--p)"}}>{fmtFit(value)}</span></div>
    <div className="fit-track">
      <div className="fit-fill" style={{width:value*100+"%", background:FITNESS_GRADIENT(value)}}/>
    </div>
  </div>
);

// Agent Card
const AgentCard = ({ agent, selected, onClick }) => {
  const meta = AGENT_META[agent.type];
  return (
    <div className={`agent-card${selected?" sel":""}`}
      style={{"--ac":meta.color}} onClick={onClick}>
      <div className="agent-hdr">
        <div className="agent-ico" style={{borderColor:meta.color+"33",color:meta.color}}>{meta.icon}</div>
        <div>
          <div className="agent-name" style={{color:meta.color}}>{agent.name}</div>
          <div className="agent-type">{meta.label}</div>
        </div>
        <div className="agent-gen">GEN {agent.generation}</div>
      </div>
      <FitnessBar value={agent.fitness} />
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div className="agent-stats">
          <div className="stat-item"><span className="stat-v">{fmtK(agent.executionCount)}</span><span>RUNS</span></div>
          <div className="stat-item"><span className="stat-v">{fmtK(agent.tokensUsed)}</span><span>TOKENS</span></div>
        </div>
        <span className="badge on"><span style={{width:6,height:6,borderRadius:"50%",background:"var(--s)"}}/>ACTIVE</span>
      </div>
    </div>
  );
};

// DNA Inspector Panel
const DNAPanel = ({ agent, onClose }) => {
  if (!agent) return null;
  const meta = AGENT_META[agent.type];
  const dna = agent.dna;
  const DRow = ({k,v}) => {
    let cls = "dna-val ";
    if (typeof v === "boolean") cls += v ? "c-t" : "c-f";
    else if (typeof v === "number") cls += "c-n";
    else if (Array.isArray(v)) { v = v.join(", "); cls += "c-p"; }
    else if (typeof v === "object") v = JSON.stringify(v);
    return <div className="dna-row"><span className="dna-key">{k}</span><span className={cls}>{String(v)}</span></div>;
  };
  const Section = ({title, icon, children}) => (
    <div className="dna-sec">
      <div className="dna-sec-hdr">{icon} {title}</div>
      {children}
    </div>
  );
  return (
    <div className="dna-panel fade-in">
      <div className="dna-close" onClick={onClose}>✕</div>
      <div style={{marginBottom:18}}>
        <div style={{fontFamily:"var(--ff)",fontSize:13,fontWeight:700,letterSpacing:2,color:meta.color}}>{agent.name}</div>
        <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginTop:3}}>DNA INSPECTOR · GEN {agent.generation}</div>
      </div>
      <Section title="PROMPT GENES" icon="🧬">
        <DRow k="reasoning" v={dna.promptGenes.reasoningPattern}/>
        <DRow k="selfCorrect" v={dna.promptGenes.selfCorrection}/>
        <DRow k="verbosity" v={dna.promptGenes.verbosity}/>
        <DRow k="tone" v={dna.promptGenes.tone}/>
        <div className="dna-row">
          <span className="dna-key">systemPrompt</span>
          <span className="dna-val" style={{fontSize:9,maxWidth:200}}>{dna.promptGenes.systemPrompt.slice(0,120)}…</span>
        </div>
      </Section>
      <Section title="PARAMETER GENES" icon="⚙">
        <DRow k="temperature" v={dna.parameterGenes.temperature}/>
        <DRow k="maxTokens" v={dna.parameterGenes.maxTokens}/>
        <DRow k="reasoningEffort" v={dna.parameterGenes.reasoningEffort}/>
      </Section>
      <Section title="TOOL GENES" icon="🔧">
        <DRow k="tools" v={dna.toolGenes.availableTools}/>
        <DRow k="maxPerTask" v={dna.toolGenes.maxToolsPerTask}/>
      </Section>
      <Section title="MEMORY GENES" icon="🧠">
        <DRow k="episodicK" v={dna.memoryGenes.episodicK}/>
        <DRow k="workingSize" v={dna.memoryGenes.workingMemorySize}/>
        <DRow k="semanticDepth" v={dna.memoryGenes.semanticDepth}/>
      </Section>
      <Section title="EVOLUTION GENES" icon="🔀">
        <DRow k="mutationRate" v={dna.evolutionGenes.mutationRate}/>
        {Object.entries(dna.evolutionGenes.fitnessWeights).map(([k,v])=>
          <DRow key={k} k={k} v={v}/>
        )}
      </Section>
      <div style={{marginTop:14,padding:14,background:"var(--pd)",border:"1px solid rgba(0,229,255,.15)",borderRadius:7}}>
        <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--p)",letterSpacing:2,marginBottom:8}}>LINEAGE</div>
        <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>DNA HASH: <span style={{color:"var(--t)"}}>{agent.id.slice(-8).toUpperCase()}</span></div>
        <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginTop:4}}>GENERATION: <span style={{color:"var(--w)"}}>{agent.generation}</span></div>
        <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginTop:4}}>FITNESS: <span style={{color:"var(--s)"}}>{fmtFit(agent.fitness)}</span></div>
      </div>
    </div>
  );
};

// ── DASHBOARD VIEW ─────────────────────────────────────────────
const Dashboard = ({ agents, tasks, skills, history }) => {
  const radarData = agents.map(a => ({
    agent: AGENT_META[a.type].short,
    fitness: Math.round(a.fitness*100),
    runs: Math.min(100, Math.round(a.executionCount/3)),
    gen: Math.min(100, a.generation*15),
  }));

  const fitData = history.map(h => ({ gen:"G"+h.gen, avg:parseFloat((h.avgFitness*100).toFixed(1)), max:parseFloat((h.maxFitness*100).toFixed(1)) }));

  return (
    <div className="fade-in">
      <div className="metrics">
        {[
          {label:"Total Agents",    val:agents.length,         sub:"active in population", mc:"var(--p)"},
          {label:"Avg Fitness",     val:avgFitness(agents),    sub:"across all agent types", mc:"var(--s)"},
          {label:"Tasks Completed", val:fmtK(tasks.filter(t=>t.status==="done").length), sub:"via multi-agent routing", mc:"var(--w)"},
          {label:"Active Skills",   val:skills.filter(s=>s.status==="active").length, sub:"in procedural memory", mc:"var(--pu)"},
        ].map((m,i) => (
          <div key={i} className="metric" style={{"--mc":m.mc}}>
            <div className="metric-label">{m.label}</div>
            <div className="metric-val">{m.val}</div>
            <div className="metric-sub">{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="g2 mb20">
        <div className="card">
          <div className="card-title">Evolution Fitness History</div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={fitData} margin={{top:5,right:5,bottom:0,left:-20}}>
              <defs>
                <linearGradient id="gMax" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#39ff14" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#39ff14" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gAvg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00e5ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00e5ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.04)"/>
              <XAxis dataKey="gen" tick={{fill:"#5a7a99",fontSize:10,fontFamily:"var(--fm)"}}/>
              <YAxis tick={{fill:"#5a7a99",fontSize:10,fontFamily:"var(--fm)"}} domain={[50,100]}/>
              <Tooltip contentStyle={{background:"#091525",border:"1px solid #1a3050",borderRadius:6,fontFamily:"var(--fm)",fontSize:11}}/>
              <Area type="monotone" dataKey="max" stroke="#39ff14" fill="url(#gMax)" strokeWidth={2} name="Max"/>
              <Area type="monotone" dataKey="avg" stroke="#00e5ff" fill="url(#gAvg)" strokeWidth={2} name="Avg"/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <div className="card-title">Agent Population Radar</div>
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,.06)"/>
              <PolarAngleAxis dataKey="agent" tick={{fill:"#5a7a99",fontSize:10,fontFamily:"var(--fm)"}}/>
              <PolarRadiusAxis tick={false} axisLine={false} domain={[0,100]}/>
              <Radar name="Fitness" dataKey="fitness" stroke="#00e5ff" fill="#00e5ff" fillOpacity={0.12} strokeWidth={2}/>
              <Radar name="Runs" dataKey="runs" stroke="#39ff14" fill="#39ff14" fillOpacity={0.08} strokeWidth={1.5}/>
              <Tooltip contentStyle={{background:"#091525",border:"1px solid #1a3050",borderRadius:6,fontFamily:"var(--fm)",fontSize:11}}/>
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <div className="card-title mb12">Agent Population</div>
        <div className="agents-grid">
          {agents.map(a => (
            <div key={a.id} className="agent-card" style={{"--ac":AGENT_META[a.type].color}}>
              <div className="agent-hdr">
                <div className="agent-ico" style={{borderColor:AGENT_META[a.type].color+"33",color:AGENT_META[a.type].color}}>{AGENT_META[a.type].icon}</div>
                <div><div className="agent-name" style={{color:AGENT_META[a.type].color}}>{a.name}</div><div className="agent-type">{AGENT_META[a.type].label}</div></div>
                <div className="agent-gen">G{a.generation}</div>
              </div>
              <FitnessBar value={a.fitness}/>
              <div className="agent-stats">
                <div className="stat-item"><span className="stat-v">{fmtK(a.executionCount)}</span><span>RUNS</span></div>
                <div className="stat-item"><span className="stat-v">{fmtK(a.tokensUsed)}</span><span>TOKENS</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── AGENTS VIEW ────────────────────────────────────────────────
const AgentsView = ({ agents, selected, setSelected }) => (
  <div className="fade-in">
    <div className="sec-hdr mb20">
      <div className="sec-title">Agent Matrix — {agents.length} Agents</div>
      <span className="badge on" style={{fontSize:10}}>Population Stable</span>
    </div>
    <div className="agents-grid">
      {agents.map(a => (
        <AgentCard key={a.id} agent={a} selected={selected?.id===a.id} onClick={()=>setSelected(selected?.id===a.id?null:a)}/>
      ))}
    </div>
    {selected && (
      <div style={{marginTop:20,padding:18,background:"var(--card)",border:"1px solid var(--b2)",borderRadius:8}}>
        <div className="sec-title mb16">SELECTED AGENT — {selected.name}</div>
        <div className="g2">
          <div>
            <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginBottom:8}}>SYSTEM PROMPT</div>
            <div style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--t)",lineHeight:1.7,padding:12,background:"var(--bg)",borderRadius:6,border:"1px solid var(--b1)"}}>{selected.dna.promptGenes.systemPrompt}</div>
          </div>
          <div className="fcol gap12">
            {[["Reasoning Pattern",selected.dna.promptGenes.reasoningPattern],
              ["Temperature",selected.dna.parameterGenes.temperature],
              ["Max Tokens",selected.dna.parameterGenes.maxTokens],
              ["Episodic K",selected.dna.memoryGenes.episodicK],
              ["Semantic Depth",selected.dna.memoryGenes.semanticDepth],
              ["Mutation Rate",selected.dna.evolutionGenes.mutationRate],
            ].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"6px 0",borderBottom:"1px solid var(--b1)"}}>
                <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{k}</span>
                <span style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--w)"}}>{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )}
  </div>
);

// ── TASK TERMINAL ──────────────────────────────────────────────
const TaskTerminal = ({ agents, tasks, setTasks, setAgents, setMemories }) => {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lines, setLines] = useState([
    { t:"sys",  txt:`GENESIS Task Terminal v2.0 — Multi-Agent Execution Engine` },
    { t:"sys",  txt:`Connected to ${agents.length} agents. Ready for task routing.` },
    { t:"sys",  txt:`─────────────────────────────────────────────────────` },
    { t:"info", txt:`Type a task and press ENTER or click EXECUTE` },
  ]);
  const bodyRef = useRef(null);
  const addLine = useCallback((t, txt) => setLines(prev => [...prev, {t,txt}]), []);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [lines]);

  const executeTask = async () => {
    if (!input.trim() || loading) return;
    const task = input.trim();
    setInput("");
    setLoading(true);

    const taskId = uid();
    addLine("prompt", `> ${task}`);
    addLine("sys","");
    addLine("sys","[STEP 1] Routing task through NEXUS...");

    const routerAgent = agents.find(a=>a.type==="router");
    if (!routerAgent) { addLine("err","Router agent not found"); setLoading(false); return; }

    let routingResult = null;
    try {
      addLine("info",`  → NEXUS analyzing task context...`);
      const routerSys = routerAgent.dna.promptGenes.systemPrompt + `\n\nAvailable agents: research (ORACLE), code (FORGE), analysis (SIGMA), creative (MUSE), skill_builder (ARCHITECT).\n\nRespond ONLY with valid JSON: {"selectedAgent":"type","reasoning":"one sentence","confidence":0.0-1.0}`;
      const r = await callClaude(routerSys, `Route this task: "${task}"`, 300);

      let parsed;
      try {
        const jsonMatch = r.text.match(/\{[^}]+\}/s);
        parsed = JSON.parse(jsonMatch?.[0] || r.text);
      } catch {
        parsed = { selectedAgent:"research", reasoning:"Defaulting to research agent", confidence:0.7 };
      }
      routingResult = parsed;
      addLine("route",`  ✦ Routed to: ${parsed.selectedAgent.toUpperCase()} (confidence: ${(parsed.confidence*100).toFixed(0)}%)`);
      addLine("route",`  ✦ Reason: ${parsed.reasoning}`);

      // Update router fitness
      setAgents(prev => prev.map(a => a.id===routerAgent.id
        ? {...a, executionCount:a.executionCount+1, tokensUsed:a.tokensUsed+r.inputTokens+r.outputTokens, fitness:Math.min(0.99,a.fitness+0.001)}
        : a));
    } catch(e) {
      addLine("err",`  Router error: ${e.message}`);
      routingResult = { selectedAgent:"research", reasoning:"fallback", confidence:0.6 };
    }

    addLine("sys","");
    addLine("sys",`[STEP 2] Executing with ${routingResult.selectedAgent.toUpperCase()} agent...`);

    const execAgent = agents.find(a=>a.type===routingResult.selectedAgent) || agents.find(a=>a.type==="research");
    if (!execAgent) { addLine("err","Execution agent not found"); setLoading(false); return; }

    const meta = AGENT_META[execAgent.type];
    addLine("info",`  → ${meta.icon} ${execAgent.name} (Gen ${execAgent.generation}, Fitness ${fmtFit(execAgent.fitness)})`);

    let result = "";
    let resultTokens = 0;
    try {
      addLine("info","  → Generating response...");
      const r = await callClaude(execAgent.dna.promptGenes.systemPrompt, task, 1000);
      result = r.text;
      resultTokens = r.inputTokens + r.outputTokens;
      addLine("sys","");
      addLine("ok","[RESULT]");
      // Show result in chunks
      const lines2 = result.split("\n").filter(Boolean).slice(0,12);
      lines2.forEach(l => addLine("res","  "+l));
      if (result.split("\n").length > 12) addLine("info","  … (truncated for display)");

      // Update exec agent fitness
      setAgents(prev => prev.map(a => a.id===execAgent.id
        ? {...a, executionCount:a.executionCount+1, tokensUsed:a.tokensUsed+resultTokens, fitness:Math.min(0.99,a.fitness+0.002)}
        : a));
    } catch(e) {
      addLine("err",`  Execution error: ${e.message}`);
      result = "Execution failed";
    }

    // Store task
    const newTask = { id:taskId, input:task, output:result, agent:execAgent.name, agentType:execAgent.type, routedBy:"NEXUS", status:"done", ts:Date.now() };
    setTasks(prev => [newTask, ...prev].slice(0,50));

    // Extract memory
    addLine("sys","");
    addLine("sys","[STEP 3] Storing episodic memory...");
    try {
      const memSys = "Extract 1-3 key facts from this AI interaction as atomic memory entries. Return JSON array: [{\"content\":\"...\",\"type\":\"fact|preference|event\",\"importance\":0.0-1.0}]";
      const memR = await callClaude(memSys, `Task: ${task}\nResponse: ${result.slice(0,500)}`, 300);
      let facts = [];
      try {
        const match = memR.text.match(/\[[\s\S]*\]/);
        facts = JSON.parse(match?.[0] || "[]");
      } catch { facts = [{content:`Completed task: ${task.slice(0,80)}`, type:"event", importance:0.6}]; }
      const newMems = facts.map(f => ({
        id:uid(), content:f.content, type:f.type||"fact", importance:f.importance||0.6,
        agentId:execAgent.id, agentName:execAgent.name, taskId, ts:Date.now()
      }));
      setMemories(prev => [...newMems, ...prev].slice(0,100));
      addLine("ok",`  ✓ Stored ${newMems.length} memory entries`);
    } catch { addLine("warn","  Memory storage skipped"); }

    addLine("sys","");
    addLine("ok","[TASK COMPLETE] ─────────────────────────────────────────");
    setLoading(false);
  };

  const TLine = ({t,txt}) => {
    const cls = {sys:"t-sys",info:"t-info",ok:"t-ok",warn:"t-warn",err:"t-err",res:"t-res",route:"t-route",prompt:"t-ok"}[t]||"t-res";
    return <div style={{margin:"1px 0"}} className={cls}>{txt}</div>;
  };

  return (
    <div className="fade-in">
      <div className="sec-hdr mb16">
        <div className="sec-title">Task Terminal — Multi-Agent Execution</div>
        {loading && <div className="flex gap8" style={{alignItems:"center"}}><div className="spin"/><span style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--p)"}}>EXECUTING</span></div>}
      </div>
      <div className="terminal mb16">
        <div className="term-hdr">
          <div className="tdot" style={{background:"#ff5f57"}}/>
          <div className="tdot" style={{background:"#ffbd2e"}}/>
          <div className="tdot" style={{background:"#28c840"}}/>
          <span className="term-title">GENESIS · TASK ENGINE · {agents.length} AGENTS ONLINE</span>
        </div>
        <div className="term-body" ref={bodyRef}>
          {lines.map((l,i)=><TLine key={i} {...l}/>)}
          {loading && <div className="t-info">  Processing<span className="cursor"/></div>}
        </div>
        <div className="term-input-row">
          <span className="t-prompt">genesis://tasks $</span>
          <input className="t-input" value={input} onChange={e=>setInput(e.target.value)}
            onKeyDown={e=>e.key==="Enter"&&executeTask()} placeholder="Enter task description..."
            autoFocus disabled={loading}/>
          <button className="t-send" onClick={executeTask} disabled={loading||!input.trim()}>
            {loading?"RUNNING":"EXECUTE"}
          </button>
        </div>
      </div>

      {tasks.length > 0 && (
        <div>
          <div className="sec-title mb12">Task History</div>
          <div className="fcol gap8">
            {tasks.slice(0,8).map(t => (
              <div key={t.id} style={{padding:"10px 14px",background:"var(--card)",border:"1px solid var(--b1)",borderRadius:7,display:"flex",gap:12,alignItems:"flex-start"}}>
                <span style={{color:AGENT_META[t.agentType]?.color,fontSize:16}}>{AGENT_META[t.agentType]?.icon}</span>
                <div style={{flex:1}}>
                  <div style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--t)",marginBottom:2}}>{t.input.slice(0,90)}{t.input.length>90?"…":""}</div>
                  <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>via {t.agentName} · {new Date(t.ts).toLocaleTimeString()}</div>
                </div>
                <span className="badge on">{t.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ── EVOLUTION VIEW ─────────────────────────────────────────────
const EvolutionView = ({ agents, history, events, setAgents, setHistory, setEvents }) => {
  const [running, setRunning] = useState(false);

  const fitData = history.map(h => ({
    gen:"G"+h.gen, avg:parseFloat((h.avgFitness*100).toFixed(1)), max:parseFloat((h.maxFitness*100).toFixed(1)),
    diversity:parseFloat((h.diversity*100).toFixed(1))
  }));

  const runEvolution = async () => {
    if (running) return;
    setRunning(true);
    const newGen = currentGen(history) + 1;
    const ts = Date.now();

    const addEv = (type, msg) => {
      setEvents(prev => [{type,msg,ts:Date.now()}, ...prev].slice(0,50));
    };

    // Sort by fitness
    const sorted = [...agents].sort((a,b) => b.fitness-a.fitness);
    const elites = sorted.slice(0,2);

    addEv("selection", `Elites preserved: ${elites.map(a=>a.name).join(", ")} (fitness: ${elites.map(a=>fmtFit(a.fitness)).join(", ")})`);
    await sleep(400);

    // Mutate non-elites
    const mutated = [];
    for (const agent of sorted.slice(2)) {
      const roll = Math.random();
      if (roll < 0.5) {
        // Parameter mutation
        const newTemp = Math.min(1.0, Math.max(0.05, agent.dna.parameterGenes.temperature + (Math.random()-0.5)*0.1));
        const newFit = Math.min(0.99, agent.fitness + (Math.random()-0.2)*0.04);
        mutated.push({...agent, generation:agent.generation+1, fitness:parseFloat(newFit.toFixed(3)),
          dna:{...agent.dna, parameterGenes:{...agent.dna.parameterGenes, temperature:parseFloat(newTemp.toFixed(2))}}});
        addEv("mutation", `${agent.name}: temperature gene ${agent.dna.parameterGenes.temperature.toFixed(2)} → ${newTemp.toFixed(2)}, fitness ${fmtFit(agent.fitness)} → ${fmtFit(newFit)}`);
      } else {
        // Crossover with an elite
        const parent2 = elites[Math.floor(Math.random()*elites.length)];
        const blendTemp = (agent.dna.parameterGenes.temperature + parent2.dna.parameterGenes.temperature) / 2;
        const blendEpK = Math.round((agent.dna.memoryGenes.episodicK + parent2.dna.memoryGenes.episodicK) / 2);
        const newFit = Math.min(0.99, (agent.fitness + parent2.fitness*0.3) / 1.3);
        mutated.push({...agent, generation:agent.generation+1, fitness:parseFloat(newFit.toFixed(3)),
          dna:{...agent.dna,
            parameterGenes:{...agent.dna.parameterGenes, temperature:parseFloat(blendTemp.toFixed(2))},
            memoryGenes:{...agent.dna.memoryGenes, episodicK:blendEpK}
          }});
        addEv("crossover", `${agent.name} × ${parent2.name} → offspring (episodicK: ${blendEpK}, temp: ${blendTemp.toFixed(2)})`);
      }
      await sleep(300);
    }

    const newAgents = [...elites.map(a=>({...a, generation:a.generation+1})), ...mutated];
    setAgents(newAgents);

    // Record generation
    const avgFit = newAgents.reduce((s,a)=>s+a.fitness,0)/newAgents.length;
    const maxFit = Math.max(...newAgents.map(a=>a.fitness));
    const newHistEntry = { gen:newGen, avgFitness:parseFloat(avgFit.toFixed(3)), maxFitness:parseFloat(maxFit.toFixed(3)), diversity:parseFloat((Math.random()*0.3+0.5).toFixed(2)), mutations:mutated.length, crossovers:mutated.filter((_,i)=>i>=mutated.length/2).length, timestamp:ts };
    setHistory(prev => [...prev, newHistEntry]);

    addEv("deploy", `Generation ${newGen} deployed — avg fitness ${fmtFit(avgFit)}, max ${fmtFit(maxFit)}`);
    setRunning(false);
  };

  return (
    <div className="fade-in">
      <div className="evo-layout">
        <div>
          <div className="evo-gen-box mb16">
            <div className="evo-gen-num">G{currentGen(history)}</div>
            <div>
              <div style={{fontFamily:"var(--ff)",fontSize:11,fontWeight:700,color:"var(--p)",letterSpacing:2}}>CURRENT GENERATION</div>
              <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginTop:4}}>{history.length} evolution cycles completed</div>
              <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--s)",marginTop:2}}>Avg fitness: {avgFitness(agents)}</div>
            </div>
          </div>
          <div className="card mb16">
            <div className="card-title">Fitness Evolution (All Generations)</div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={fitData} margin={{top:5,right:5,bottom:0,left:-20}}>
                <defs>
                  <linearGradient id="gMax2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#39ff14" stopOpacity={0.35}/><stop offset="95%" stopColor="#39ff14" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gAvg2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00e5ff" stopOpacity={0.3}/><stop offset="95%" stopColor="#00e5ff" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gDiv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#b388ff" stopOpacity={0.2}/><stop offset="95%" stopColor="#b388ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.04)"/>
                <XAxis dataKey="gen" tick={{fill:"#5a7a99",fontSize:10,fontFamily:"var(--fm)"}}/>
                <YAxis tick={{fill:"#5a7a99",fontSize:10,fontFamily:"var(--fm)"}} domain={[40,100]}/>
                <Tooltip contentStyle={{background:"#091525",border:"1px solid #1a3050",borderRadius:6,fontFamily:"var(--fm)",fontSize:11}}/>
                <Area type="monotone" dataKey="max" stroke="#39ff14" fill="url(#gMax2)" strokeWidth={2} name="Max Fitness"/>
                <Area type="monotone" dataKey="avg" stroke="#00e5ff" fill="url(#gAvg2)" strokeWidth={2} name="Avg Fitness"/>
                <Area type="monotone" dataKey="diversity" stroke="#b388ff" fill="url(#gDiv)" strokeWidth={1.5} name="Diversity"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="g3">
            {agents.slice(0,3).map(a => (
              <div key={a.id} className="card">
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                  <span style={{fontFamily:"var(--ff)",fontSize:10,color:AGENT_META[a.type].color,letterSpacing:1}}>{a.name}</span>
                  <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>G{a.generation}</span>
                </div>
                <FitnessBar value={a.fitness}/>
                <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)"}}>{a.executionCount} tasks · μ={a.dna.evolutionGenes.mutationRate}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="fcol gap12">
          <button className="evo-btn" onClick={runEvolution} disabled={running}>
            {running ? <span className="flex gap8" style={{justifyContent:"center",alignItems:"center"}}><span className="spin"/>EVOLVING...</span> : "⚡ RUN EVOLUTION CYCLE"}
          </button>
          <div className="card">
            <div className="card-title">Population Stats</div>
            {[["Total Agents",agents.length],["Elites",2],["Avg Generation",Math.round(agents.reduce((s,a)=>s+a.generation,0)/agents.length)],
              ["Max Fitness",fmtFit(Math.max(...agents.map(a=>a.fitness)))],["Total Tasks",agents.reduce((s,a)=>s+a.executionCount,0)],
            ].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"6px 0",borderBottom:"1px solid var(--b1)"}}>
                <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{k}</span>
                <span style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--p)"}}>{String(v)}</span>
              </div>
            ))}
          </div>
          <div className="evlog" style={{flex:1}}>
            <div className="evlog-hdr">Evolution Events</div>
            <div className="evlog-body">
              {events.length === 0 && <div className="empty"><span className="empty-ico">⚡</span>No events yet</div>}
              {events.map((e,i) => (
                <div key={i} className={`ev-item ev-${e.type}`}>
                  <span className="ev-time">{new Date(e.ts).toLocaleTimeString("en",{hour12:false,hour:"2-digit",minute:"2-digit"})}</span>
                  <span className="ev-type">{e.type.toUpperCase()}</span>
                  <span className="ev-msg">{e.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ── MEMORY VIEW ────────────────────────────────────────────────
const MemoryView = ({ memories }) => {
  const [tab, setTab] = useState("episodic");
  const [search, setSearch] = useState("");

  const filtered = memories.filter(m => !search || m.content.toLowerCase().includes(search.toLowerCase()));
  const ImpDots = ({v}) => (
    <div className="mem-imp">
      {[0.2,0.4,0.6,0.8,1.0].map(t=>(
        <div key={t} style={{width:5,height:5,borderRadius:"50%",background:v>=t?"var(--s)":"rgba(255,255,255,.1)",margin:"0 1px"}}/>
      ))}
    </div>
  );

  return (
    <div className="fade-in">
      <div className="sec-hdr mb16">
        <div className="sec-title">Memory Core — {memories.length} Entries</div>
        <div className="g-badge" style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--p)"}}>4-TIER ARCHITECTURE</div>
      </div>
      <div className="mem-tabs">
        {[["episodic","Episodic"],["working","Working"],["semantic","Semantic"],["procedural","Procedural"]].map(([k,l])=>(
          <div key={k} className={`mem-tab${tab===k?" on":""}`} onClick={()=>setTab(k)}>{l}</div>
        ))}
      </div>
      {tab === "episodic" && (
        <div>
          <input className="g-search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search episodic memories..." style={{width:"100%",padding:"9px 14px",background:"var(--card)",border:"1px solid var(--b1)",borderRadius:6,color:"var(--t)",fontFamily:"var(--fm)",fontSize:12,outline:"none",marginBottom:16}}/>
          {filtered.length === 0 ? (
            <div className="empty"><span className="empty-ico">🧠</span><span>No episodic memories yet.</span><span style={{fontSize:11}}>Execute tasks to populate memory.</span></div>
          ) : filtered.map(m => (
            <div key={m.id} className="mem-item">
              <div className="mem-ico">{m.type==="preference"?"⭐":m.type==="event"?"⚡":"◎"}</div>
              <div style={{flex:1}}>
                <div className="mem-text">{m.content}</div>
                <div className="mem-meta">
                  <span>{AGENT_META[m.agentType||"research"]?.icon} {m.agentName}</span>
                  <span>·</span>
                  <span style={{textTransform:"uppercase"}}>{m.type}</span>
                  <span>·</span>
                  <span>{new Date(m.ts).toLocaleTimeString()}</span>
                  <ImpDots v={m.importance}/>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {tab === "working" && (
        <div>
          <div className="card mb12" style={{borderColor:"rgba(0,229,255,.2)"}}>
            <div className="card-title">Working Memory — Letta-style Virtual Context</div>
            <div className="g2" style={{gap:12}}>
              {[{label:"RAM (Active)",val:"30%",sub:"~38K tokens in use",color:"var(--s)"},
                {label:"Disk (Archived)",val:"70%",sub:"~89K tokens archived",color:"var(--p)"},
                {label:"Hit Rate",val:"94.2%",sub:"cache efficiency",color:"var(--w)"},
                {label:"Page Faults",val:"14",sub:"this session",color:"var(--pu)"},
              ].map((m,i)=>(
                <div key={i} style={{padding:"12px 14px",background:"var(--bg)",borderRadius:6,border:"1px solid var(--b1)"}}>
                  <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginBottom:4}}>{m.label}</div>
                  <div style={{fontFamily:"var(--ff)",fontSize:22,fontWeight:700,color:m.color}}>{m.val}</div>
                  <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",marginTop:2}}>{m.sub}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="empty"><span className="empty-ico">⚡</span><span>Working memory is session-scoped</span><span style={{fontSize:11}}>Active context clears between sessions</span></div>
        </div>
      )}
      {tab === "semantic" && (
        <div>
          <div className="card mb12"><div className="card-title">Semantic Memory — Knowledge Graph (Neo4j)</div>
            <div style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--tm)",marginBottom:12}}>Entities, relationships, and multi-hop reasoning paths</div>
            {[["Entities","142","concepts, people, topics"],["Relationships","387","typed graph edges"],["Graph Depth","3","hop traversal limit"],["Knowledge Areas","28","distinct domains"],
            ].map(([k,v,s])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid var(--b1)"}}>
                <span style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--tm)"}}>{k}</span>
                <div style={{textAlign:"right"}}><span style={{fontFamily:"var(--ff)",fontSize:14,color:"var(--p)"}}>{v}</span> <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{s}</span></div>
              </div>
            ))}
          </div>
        </div>
      )}
      {tab === "procedural" && (
        <div className="empty"><span className="empty-ico">⌬</span><span>Procedural memory = Skill Registry</span><span style={{fontSize:11}}>See the Skills tab for executable skills</span></div>
      )}
    </div>
  );
};

// ── SKILLS VIEW ────────────────────────────────────────────────
const SkillsView = ({ skills, setSkills, agents }) => {
  const [generating, setGenerating] = useState(false);

  const generateSkill = async () => {
    setGenerating(true);
    const builder = agents.find(a=>a.type==="skill_builder");
    if (!builder) { setGenerating(false); return; }
    try {
      const sys = "You are the GENESIS Skill Builder. Generate a new useful skill definition. Return ONLY JSON: {\"name\":\"Skill Name\",\"description\":\"what it does (1-2 sentences)\",\"tags\":[\"tag1\",\"tag2\"],\"agentTypes\":[\"research\"|\"code\"|\"analysis\"|\"creative\"]}";
      const r = await callClaude(sys, "Generate a new unique and useful skill for the agent ecosystem", 300);
      let parsed;
      try {
        const match = r.text.match(/\{[\s\S]*\}/);
        parsed = JSON.parse(match?.[0] || r.text);
      } catch { parsed = {name:"Auto-Generated Skill", description:"A useful capability for the ecosystem.", tags:["auto-generated"], agentTypes:["research"]}; }
      const newSkill = { id:"sk-"+uid(), name:parsed.name||"New Skill", description:parsed.description||"", tags:parsed.tags||["auto-generated"], agentTypes:parsed.agentTypes||["research"], version:1, fitness:0.55, usageCount:0, status:"active" };
      setSkills(prev => [newSkill, ...prev]);
    } catch(e) { console.error(e); }
    setGenerating(false);
  };

  return (
    <div className="fade-in">
      <div className="sec-hdr mb16">
        <div className="sec-title">Skills Lab — {skills.length} Skills</div>
        <button className="btn btn-s" onClick={generateSkill} disabled={generating}>
          {generating ? <span className="flex gap8" style={{alignItems:"center"}}><span className="spin"/>Generating...</span> : "⌬ Generate New Skill"}
        </button>
      </div>
      <div className="skills-grid">
        {skills.map(s => (
          <div key={s.id} className="skill-card">
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
              <div className="skill-name">{s.name}</div>
              <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",flexShrink:0,marginLeft:8}}>v{s.version}</div>
            </div>
            <div className="skill-desc">{s.description}</div>
            <div style={{marginBottom:10}}>
              <div style={{display:"flex",justifyContent:"space-between",fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginBottom:4}}><span>FITNESS</span><span style={{color:"var(--s)"}}>{fmtFit(s.fitness)}</span></div>
              <div style={{height:2,background:"rgba(255,255,255,.05)",borderRadius:1,overflow:"hidden"}}>
                <div style={{height:"100%",width:s.fitness*100+"%",background:FITNESS_GRADIENT(s.fitness),borderRadius:1}}/>
              </div>
            </div>
            <div className="skill-tags" style={{marginBottom:8}}>
              {s.tags.map(t=><span key={t} className="skill-tag">{t}</span>)}
            </div>
            <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)"}}>{s.usageCount} uses · {s.agentTypes.join(", ")}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── ARCHITECTURE VIEW ─────────────────────────────────────────
const ArchitectureView = ({ agents, tasks, memories, skills }) => {
  const [activeLayer, setActiveLayer] = useState(null);

  const LAYERS = [
    { id:"infra",   label:"Layer 0 — Infrastructure",   color:"#5a7a99", bg:"rgba(90,122,153,.08)", items:["Redis Pub/Sub","PostgreSQL","Qdrant VectorDB","Neo4j Graph","Docker / K8s"] },
    { id:"memory",  label:"Layer 1 — Memory System",    color:"#b388ff", bg:"rgba(179,136,255,.08)", items:["Working Memory (Letta)","Episodic Memory (Mem0)","Semantic Memory (Cognee)","Procedural / Skill Registry"] },
    { id:"agents",  label:"Layer 2 — Agent Framework",  color:"#00e5ff", bg:"rgba(0,229,255,.08)", items:["Router Agent (NEXUS)","Research (ORACLE)","Code (FORGE)","Analysis (SIGMA)","Creative (MUSE)","Skill Builder (ARCHITECT)"] },
    { id:"evo",     label:"Layer 3 — Genetic Evolution",color:"#39ff14", bg:"rgba(57,255,20,.08)", items:["Agent DNA Encoding","Tournament Selection","Semantic Mutation","Semantic Crossover","Fitness Evaluation","Gradual Deployment"] },
    { id:"comms",   label:"Layer 4 — Communication",    color:"#ffab40", bg:"rgba(255,171,64,.08)", items:["A2A Protocol (Google)","MCP Protocol (Anthropic)","Task Router Bus","Event Stream","Agent Registry"] },
  ];

  const FLOW_STEPS = [
    { n:"01", title:"Task Ingestion",     icon:"▶", color:"var(--p)", desc:"User submits a task via API or UI. Task enters the message bus." },
    { n:"02", title:"NEXUS Routing",      icon:"⬡", color:"#b388ff",  desc:"Router agent analyzes task, selects best-fit agent using DNA-encoded decision logic." },
    { n:"03", title:"Memory Retrieval",   icon:"🧠", color:"#00e5ff",  desc:"Relevant episodic & semantic memories are injected into agent context window." },
    { n:"04", title:"Agent Execution",    icon:"◎", color:"var(--s)", desc:"Selected agent executes task using its genetically-evolved prompt and parameter genes." },
    { n:"05", title:"Skill Application",  icon:"⌬", color:"var(--w)", desc:"Agent applies matching procedural skills from the skill registry." },
    { n:"06", title:"Memory Update",      icon:"◈", color:"#f48fb1",  desc:"Response facts extracted and stored in episodic + semantic memory tiers." },
    { n:"07", title:"Fitness Scoring",    icon:"≋", color:"var(--p)", desc:"Task outcome scored across multiple dimensions, stored for evolution." },
    { n:"08", title:"Evolution Trigger",  icon:"🔀", color:"var(--s)", desc:"Every N tasks, genetic evolution cycle runs: selection → mutation → crossover → deploy." },
  ];

  const techStack = [
    { layer:"Agent Framework", tech:"LangGraph", note:"Multi-agent orchestration" },
    { layer:"Primary LLMs",    tech:"Claude 4.6 · GPT-5.4 · Gemini 3", note:"Model routing by task type" },
    { layer:"Episodic Memory", tech:"Mem0 + Qdrant", note:"Vector similarity search" },
    { layer:"Semantic Memory", tech:"Cognee + Neo4j", note:"Knowledge graph traversal" },
    { layer:"Working Memory",  tech:"Letta-style OS", note:"Redis LRU paging" },
    { layer:"Event Bus",       tech:"Redis Streams", note:"Agent-to-agent comms" },
    { layer:"Skill Registry",  tech:"PostgreSQL + API", note:"Versioned skill CRUD" },
    { layer:"Protocols",       tech:"A2A + MCP",      note:"Google + Anthropic standards" },
    { layer:"Deploy",          tech:"Docker / K8s",   note:"Blue-green deployment" },
    { layer:"Monitoring",      tech:"Prometheus + Grafana", note:"Fitness metrics & tracing" },
  ];

  return (
    <div className="fade-in">
      <div className="sec-hdr mb20">
        <div className="sec-title">System Architecture — GENESIS v2.0</div>
        <span className="badge ev">5-Layer Design</span>
      </div>

      {/* LAYER STACK */}
      <div className="mb24">
        <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",letterSpacing:2,marginBottom:12,textTransform:"uppercase"}}>Layered Architecture Stack</div>
        {[...LAYERS].reverse().map((layer,i) => (
          <div key={layer.id} onClick={()=>setActiveLayer(activeLayer===layer.id?null:layer.id)}
            style={{marginBottom:4,border:`1px solid ${activeLayer===layer.id?layer.color+"55":"var(--b1)"}`,
              borderRadius:7,background:activeLayer===layer.id?layer.bg:"var(--card)",
              cursor:"pointer",overflow:"hidden",transition:"all .2s"}}>
            <div style={{display:"flex",alignItems:"center",gap:12,padding:"11px 16px"}}>
              <div style={{width:28,height:28,borderRadius:6,background:layer.color+"22",border:`1px solid ${layer.color}44`,
                display:"flex",alignItems:"center",justifyContent:"center",fontFamily:"var(--ff)",fontSize:10,color:layer.color,flexShrink:0}}>{LAYERS.length-1-i}</div>
              <div style={{fontFamily:"var(--ff)",fontSize:11,fontWeight:700,letterSpacing:2,color:layer.color}}>{layer.label}</div>
              <div style={{marginLeft:"auto",fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>
                {activeLayer===layer.id?"▲":"▼"}
              </div>
            </div>
            {activeLayer===layer.id && (
              <div style={{padding:"0 16px 14px",display:"flex",flexWrap:"wrap",gap:6,borderTop:"1px solid var(--b1)",paddingTop:10}}>
                {layer.items.map(item=>(
                  <span key={item} style={{padding:"4px 10px",background:layer.color+"18",border:`1px solid ${layer.color}33`,
                    borderRadius:4,fontFamily:"var(--fm)",fontSize:10,color:layer.color}}>{item}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* EXECUTION FLOW */}
      <div className="mb24">
        <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",letterSpacing:2,marginBottom:14,textTransform:"uppercase"}}>Task Execution Flow</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
          {FLOW_STEPS.map((s,i) => (
            <div key={s.n} style={{padding:"14px",background:"var(--card)",border:"1px solid var(--b1)",borderRadius:8,position:"relative",overflow:"hidden"}}>
              <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:s.color}}/>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                <div style={{fontFamily:"var(--ff)",fontSize:9,color:"var(--tm)",letterSpacing:2}}>{s.n}</div>
                <div style={{fontSize:14}}>{s.icon}</div>
              </div>
              <div style={{fontFamily:"var(--ff)",fontSize:10,fontWeight:700,color:s.color,letterSpacing:1,marginBottom:5}}>{s.title}</div>
              <div style={{fontFamily:"var(--fb)",fontSize:11,color:"var(--tm)",lineHeight:1.55}}>{s.desc}</div>
              {i < FLOW_STEPS.length-1 && (
                <div style={{position:"absolute",right:-6,top:"50%",transform:"translateY(-50%)",
                  fontFamily:"var(--fm)",fontSize:12,color:"var(--b2)",zIndex:1}}>→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* TECH STACK TABLE */}
      <div className="card">
        <div className="card-title">Technology Stack</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:0}}>
          {techStack.map((t,i) => (
            <div key={i} style={{display:"flex",gap:12,padding:"9px 12px",borderBottom:"1px solid var(--b1)",
              borderRight:i%2===0?"1px solid var(--b1)":"none"}}>
              <div style={{minWidth:120,fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{t.layer}</div>
              <div style={{flex:1}}>
                <div style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--p)"}}>{t.tech}</div>
                <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginTop:2}}>{t.note}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── CHAT VIEW ─────────────────────────────────────────────────
const ChatView = ({ agents, setAgents, setMemories }) => {
  const [messages, setMessages] = useState([
    { role:"system", content:"Welcome to GENESIS Multi-Agent Chat. Select an agent to talk to directly, or use AUTO to let NEXUS route your message.", ts:Date.now() }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedType, setSelectedType] = useState("auto");
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setLoading(true);

    setMessages(prev => [...prev, { role:"user", content:userMsg, ts:Date.now() }]);

    let targetType = selectedType;
    let routingNote = null;

    // Auto-route via NEXUS
    if (selectedType === "auto") {
      try {
        const routerSys = agents.find(a=>a.type==="router")?.dna.promptGenes.systemPrompt || "Route to the best agent. Return JSON: {\"selectedAgent\":\"type\"}";
        const r = await callClaude(routerSys + "\n\nReturn ONLY JSON: {\"selectedAgent\":\"research|code|analysis|creative|skill_builder\",\"confidence\":0.0-1.0}", `Route: "${userMsg}"`, 200);
        const match = r.text.match(/\{[^}]+\}/s);
        const parsed = JSON.parse(match?.[0] || '{"selectedAgent":"research"}');
        targetType = parsed.selectedAgent || "research";
        routingNote = `NEXUS → routed to ${targetType.toUpperCase()} (${((parsed.confidence||0.8)*100).toFixed(0)}% confidence)`;
      } catch { targetType = "research"; }
    }

    const agent = agents.find(a=>a.type===targetType) || agents[1];
    const meta = AGENT_META[agent.type];

    if (routingNote) {
      setMessages(prev => [...prev, { role:"route", content:routingNote, ts:Date.now(), agent:agent.name }]);
    }

    try {
      const r = await callClaude(agent.dna.promptGenes.systemPrompt, userMsg, 1000);
      setMessages(prev => [...prev, { role:"assistant", content:r.text, ts:Date.now(), agentName:agent.name, agentType:agent.type, agentColor:meta.color, agentIcon:meta.icon }]);

      // Update agent usage
      setAgents(prev => prev.map(a => a.id===agent.id
        ? {...a, executionCount:a.executionCount+1, tokensUsed:a.tokensUsed+(r.inputTokens||0)+(r.outputTokens||0)}
        : a));

      // Extract memory
      try {
        const memSys = "Extract 1-2 key facts from this conversation. Return JSON: [{\"content\":\"...\",\"type\":\"fact\",\"importance\":0.0-1.0}]";
        const mr = await callClaude(memSys, `Q: ${userMsg}\nA: ${r.text.slice(0,300)}`, 200);
        const match2 = mr.text.match(/\[[\s\S]*?\]/);
        const facts = JSON.parse(match2?.[0] || "[]");
        setMemories(prev => [...facts.map(f=>({id:uid(),content:f.content,type:f.type||"fact",importance:f.importance||0.6,agentId:agent.id,agentName:agent.name,agentType:agent.type,ts:Date.now()})), ...prev].slice(0,100));
      } catch {}
    } catch(e) {
      setMessages(prev => [...prev, { role:"error", content:`Error: ${e.message}`, ts:Date.now() }]);
    }
    setLoading(false);
  };

  const Msg = ({ m }) => {
    if (m.role==="system") return (
      <div style={{textAlign:"center",padding:"8px 0",fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)",borderBottom:"1px solid var(--b1)",marginBottom:12}}>{m.content}</div>
    );
    if (m.role==="route") return (
      <div style={{display:"flex",justifyContent:"center",padding:"4px 0"}}>
        <span style={{fontFamily:"var(--fm)",fontSize:9,color:"#b388ff",padding:"3px 10px",background:"rgba(179,136,255,.08)",border:"1px solid rgba(179,136,255,.2)",borderRadius:10}}>⬡ {m.content}</span>
      </div>
    );
    if (m.role==="error") return (
      <div style={{padding:"10px 14px",background:"rgba(255,82,82,.06)",border:"1px solid rgba(255,82,82,.2)",borderRadius:8,fontFamily:"var(--fm)",fontSize:11,color:"var(--a)",margin:"4px 0"}}>{m.content}</div>
    );
    if (m.role==="user") return (
      <div style={{display:"flex",justifyContent:"flex-end",margin:"6px 0"}}>
        <div style={{maxWidth:"72%",padding:"10px 14px",background:"rgba(0,229,255,.1)",border:"1px solid rgba(0,229,255,.2)",borderRadius:"12px 12px 2px 12px",fontFamily:"var(--fb)",fontSize:13,color:"var(--t)",lineHeight:1.6}}>{m.content}</div>
      </div>
    );
    if (m.role==="assistant") return (
      <div style={{display:"flex",gap:10,margin:"6px 0",alignItems:"flex-start"}}>
        <div style={{width:32,height:32,borderRadius:8,background:`${m.agentColor}22`,border:`1px solid ${m.agentColor}44`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,flexShrink:0,color:m.agentColor}}>{m.agentIcon}</div>
        <div style={{flex:1}}>
          <div style={{fontFamily:"var(--fm)",fontSize:9,color:m.agentColor,marginBottom:4,letterSpacing:1}}>{m.agentName}</div>
          <div style={{padding:"10px 14px",background:"var(--card)",border:"1px solid var(--b1)",borderRadius:"2px 12px 12px 12px",fontFamily:"var(--fb)",fontSize:13,color:"var(--t)",lineHeight:1.7,whiteSpace:"pre-wrap"}}>{m.content}</div>
          <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginTop:3}}>{new Date(m.ts).toLocaleTimeString()}</div>
        </div>
      </div>
    );
    return null;
  };

  return (
    <div className="fade-in" style={{height:"calc(100vh - 65px)",display:"flex",flexDirection:"column"}}>
      {/* Agent selector */}
      <div style={{display:"flex",gap:6,marginBottom:14,flexWrap:"wrap"}}>
        <div onClick={()=>setSelectedType("auto")} style={{
          padding:"6px 14px",borderRadius:6,cursor:"pointer",transition:"all .18s",
          background:selectedType==="auto"?"rgba(0,229,255,.12)":"var(--card)",
          border:`1px solid ${selectedType==="auto"?"rgba(0,229,255,.3)":"var(--b1)"}`,
          fontFamily:"var(--ff)",fontSize:9,letterSpacing:2,color:selectedType==="auto"?"var(--p)":"var(--tm)"}}>⬡ AUTO</div>
        {agents.map(a => {
          const m = AGENT_META[a.type];
          const on = selectedType===a.type;
          return (
            <div key={a.id} onClick={()=>setSelectedType(a.type)} style={{
              padding:"6px 14px",borderRadius:6,cursor:"pointer",transition:"all .18s",
              background:on?`${m.color}14`:"var(--card)",
              border:`1px solid ${on?m.color+"44":"var(--b1)"}`,
              fontFamily:"var(--ff)",fontSize:9,letterSpacing:1,color:on?m.color:"var(--tm)",
              display:"flex",alignItems:"center",gap:5}}>
              <span>{m.icon}</span><span>{a.name}</span>
            </div>
          );
        })}
      </div>

      {/* Messages */}
      <div ref={bodyRef} style={{flex:1,overflowY:"auto",padding:"4px 0",marginBottom:14}}>
        {messages.map((m,i) => <Msg key={i} m={m}/>)}
        {loading && (
          <div style={{display:"flex",gap:10,margin:"6px 0",alignItems:"center"}}>
            <div style={{width:32,height:32,borderRadius:8,background:"rgba(0,229,255,.1)",border:"1px solid rgba(0,229,255,.2)",display:"flex",alignItems:"center",justifyContent:"center"}}>
              <div className="spin"/>
            </div>
            <div style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--tm)"}}>Agent processing...</div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{display:"flex",gap:8,background:"var(--card)",border:"1px solid var(--b2)",borderRadius:8,padding:"10px 14px",alignItems:"center"}}>
        <span style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--tm)",flexShrink:0}}>
          {selectedType==="auto"?"⬡ AUTO":AGENT_META[agents.find(a=>a.type===selectedType)?.type]?.icon||"◎"}</span>
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&!e.shiftKey&&send()}
          placeholder="Chat with the agent network..." disabled={loading}
          style={{flex:1,background:"none",border:"none",outline:"none",color:"var(--t)",fontFamily:"var(--fb)",fontSize:13,caretColor:"var(--p)"}}/>
        <button onClick={send} disabled={loading||!input.trim()} className="t-send">SEND</button>
      </div>
    </div>
  );
};

// ── SETTINGS VIEW ─────────────────────────────────────────────
const SettingsView = ({ agents, setAgents }) => {
  const [editing, setEditing] = useState(null);
  const [tempVals, setTempVals] = useState({});

  const startEdit = (agentId, field, value) => {
    setEditing(`${agentId}.${field}`);
    setTempVals(prev => ({...prev, [`${agentId}.${field}`]: value}));
  };

  const saveEdit = (agentId, field) => {
    const key = `${agentId}.${field}`;
    const val = tempVals[key];
    setAgents(prev => prev.map(a => {
      if (a.id !== agentId) return a;
      const parts = field.split(".");
      const newDna = JSON.parse(JSON.stringify(a.dna));
      let ptr = newDna;
      for (let i=0;i<parts.length-1;i++) ptr = ptr[parts[i]];
      const num = parseFloat(val);
      ptr[parts[parts.length-1]] = isNaN(num) ? val : num;
      return {...a, dna:newDna};
    }));
    setEditing(null);
  };

  const EditableField = ({agentId, field, value, type="number"}) => {
    const key = `${agentId}.${field}`;
    const isEdit = editing===key;
    return isEdit ? (
      <div style={{display:"flex",gap:4,alignItems:"center"}}>
        <input autoFocus value={tempVals[key]??value} onChange={e=>setTempVals(p=>({...p,[key]:e.target.value}))}
          onKeyDown={e=>{if(e.key==="Enter")saveEdit(agentId,field); if(e.key==="Escape")setEditing(null);}}
          style={{width:90,padding:"3px 6px",background:"var(--bg)",border:"1px solid var(--p)",borderRadius:4,
            color:"var(--t)",fontFamily:"var(--fm)",fontSize:11,outline:"none"}}/>
        <button onClick={()=>saveEdit(agentId,field)} style={{padding:"2px 7px",background:"var(--sd)",border:"1px solid rgba(57,255,20,.3)",borderRadius:3,cursor:"pointer",color:"var(--s)",fontFamily:"var(--fm)",fontSize:9}}>✓</button>
        <button onClick={()=>setEditing(null)} style={{padding:"2px 7px",background:"rgba(255,82,82,.1)",border:"1px solid rgba(255,82,82,.2)",borderRadius:3,cursor:"pointer",color:"var(--a)",fontFamily:"var(--fm)",fontSize:9}}>✕</button>
      </div>
    ) : (
      <span onClick={()=>startEdit(agentId, field, value)}
        style={{fontFamily:"var(--fm)",fontSize:11,color:"var(--w)",cursor:"pointer",borderBottom:"1px dashed rgba(255,171,64,.3)",paddingBottom:1}}>
        {String(value)} <span style={{fontSize:9,opacity:.5}}>✎</span>
      </span>
    );
  };

  return (
    <div className="fade-in">
      <div className="sec-hdr mb20">
        <div className="sec-title">Agent Configuration — Live DNA Editor</div>
        <span className="badge sb">⚠ CHANGES PERSIST IN SESSION</span>
      </div>
      <div className="fcol gap16">
        {agents.map(a => {
          const meta = AGENT_META[a.type];
          return (
            <div key={a.id} className="card" style={{borderColor:meta.color+"22"}}>
              <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14,paddingBottom:10,borderBottom:"1px solid var(--b1)"}}>
                <div style={{width:36,height:36,borderRadius:8,background:`${meta.color}18`,border:`1px solid ${meta.color}33`,
                  display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,color:meta.color}}>{meta.icon}</div>
                <div>
                  <div style={{fontFamily:"var(--ff)",fontSize:12,fontWeight:700,color:meta.color,letterSpacing:2}}>{a.name}</div>
                  <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginTop:2}}>{meta.label} · Gen {a.generation} · {fmtFit(a.fitness)} fitness</div>
                </div>
              </div>
              <div className="g3" style={{gap:20}}>
                <div>
                  <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",letterSpacing:2,marginBottom:8,textTransform:"uppercase"}}>Parameter Genes</div>
                  {[
                    ["Temperature","parameterGenes.temperature",a.dna.parameterGenes.temperature],
                    ["Max Tokens","parameterGenes.maxTokens",a.dna.parameterGenes.maxTokens],
                  ].map(([label,field,val])=>(
                    <div key={field} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"5px 0",borderBottom:"1px solid rgba(17,34,64,.5)"}}>
                      <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{label}</span>
                      <EditableField agentId={a.id} field={field} value={val}/>
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",letterSpacing:2,marginBottom:8,textTransform:"uppercase"}}>Memory Genes</div>
                  {[
                    ["Episodic K","memoryGenes.episodicK",a.dna.memoryGenes.episodicK],
                    ["Working Mem","memoryGenes.workingMemorySize",a.dna.memoryGenes.workingMemorySize],
                    ["Semantic Depth","memoryGenes.semanticDepth",a.dna.memoryGenes.semanticDepth],
                  ].map(([label,field,val])=>(
                    <div key={field} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"5px 0",borderBottom:"1px solid rgba(17,34,64,.5)"}}>
                      <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{label}</span>
                      <EditableField agentId={a.id} field={field} value={val}/>
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",letterSpacing:2,marginBottom:8,textTransform:"uppercase"}}>Evolution Genes</div>
                  {[
                    ["Mutation Rate","evolutionGenes.mutationRate",a.dna.evolutionGenes.mutationRate],
                  ].map(([label,field,val])=>(
                    <div key={field} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"5px 0",borderBottom:"1px solid rgba(17,34,64,.5)"}}>
                      <span style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>{label}</span>
                      <EditableField agentId={a.id} field={field} value={val}/>
                    </div>
                  ))}
                  <div style={{marginTop:10}}>
                    <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginBottom:6}}>REASONING PATTERN</div>
                    <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                      {["chain-of-thought","tree-of-thought","react","plan-and-execute"].map(p=>(
                        <div key={p} onClick={()=>setAgents(prev=>prev.map(ag=>ag.id===a.id?{...ag,dna:{...ag.dna,promptGenes:{...ag.dna.promptGenes,reasoningPattern:p}}}:ag))}
                          style={{padding:"3px 7px",borderRadius:4,cursor:"pointer",transition:"all .15s",
                            background:a.dna.promptGenes.reasoningPattern===p?`${meta.color}22`:"rgba(0,0,0,.3)",
                            border:`1px solid ${a.dna.promptGenes.reasoningPattern===p?meta.color+"55":"var(--b1)"}`,
                            fontFamily:"var(--fm)",fontSize:8,color:a.dna.promptGenes.reasoningPattern===p?meta.color:"var(--tm)"}}>
                          {p}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── MAIN APP ───────────────────────────────────────────────────
export default function App() {
  useEffect(() => { injectStyles(); }, []);

  const [tab, setTab]           = useState("dashboard");
  const [agents, setAgents]     = useState(INIT_AGENTS);
  const [tasks, setTasks]       = useState([]);
  const [memories, setMemories] = useState([]);
  const [skills, setSkills]     = useState(INIT_SKILLS);
  const [history, setHistory]   = useState(INIT_EVOLUTION);
  const [events, setEvents]     = useState(INIT_EVENTS);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showDNA, setShowDNA]   = useState(false);

  const NAV_MAIN = [
    { id:"dashboard",    icon:"⬡", label:"Command Center",    badge:null },
    { id:"agents",       icon:"◎", label:"Agent Matrix",      badge:agents.length },
    { id:"chat",         icon:"◈", label:"Agent Chat",        badge:null },
    { id:"tasks",        icon:"▶", label:"Task Terminal",     badge:tasks.length||null },
    { id:"evolution",    icon:"🔀", label:"Evolution Chamber", badge:null },
    { id:"memory",       icon:"🧠", label:"Memory Core",      badge:memories.length||null },
    { id:"skills",       icon:"⌬", label:"Skills Lab",        badge:skills.length },
    { id:"architecture", icon:"≋", label:"Architecture",      badge:null },
    { id:"settings",     icon:"⚙", label:"DNA Editor",        badge:null },
  ];

  const HDR_MAP = {
    dashboard:    { title:"Command Center",    path:"genesis://dashboard" },
    agents:       { title:"Agent Matrix",      path:"genesis://agents" },
    chat:         { title:"Agent Chat",        path:"genesis://chat" },
    tasks:        { title:"Task Terminal",     path:"genesis://tasks" },
    evolution:    { title:"Evolution Chamber", path:"genesis://evolution" },
    memory:       { title:"Memory Core",       path:"genesis://memory" },
    skills:       { title:"Skills Lab",        path:"genesis://skills" },
    architecture: { title:"System Architecture",path:"genesis://architecture" },
    settings:     { title:"DNA Editor",        path:"genesis://settings" },
  };

  const handleAgentSelect = (a) => {
    setSelectedAgent(a?.id === selectedAgent?.id ? null : a);
    setShowDNA(a?.id !== selectedAgent?.id);
  };

  return (
    <div className="app">
      {/* SIDEBAR */}
      <div className="sb">
        <div className="sb-logo">
          <div className="logo-title">GENESIS</div>
          <div className="logo-sub">GENETIC EVOLUTION NETWORK</div>
          <div className="logo-gen"><div className="gen-dot"/><span>GEN {currentGen(history)} · LIVE</span></div>
        </div>
        <nav className="sb-nav">
          <div className="nav-grp">PLATFORM</div>
          {NAV_MAIN.map(n => (
            <div key={n.id} className={`nav-item${tab===n.id?" on":""}`} onClick={()=>{setTab(n.id); if(n.id!=="agents")setShowDNA(false);}}>
              <span className="nav-icon">{n.icon}</span>
              <span>{n.label}</span>
              {n.badge !== null && <span className="nav-badge">{n.badge}</span>}
            </div>
          ))}
          <div className="nav-grp" style={{marginTop:8}}>AGENTS</div>
          {agents.map(a => (
            <div key={a.id} className={`nav-item${selectedAgent?.id===a.id?" on":""}`}
              onClick={()=>{handleAgentSelect(a); setTab("agents");}} style={{paddingLeft:10}}>
              <span style={{color:AGENT_META[a.type].color,fontSize:13}}>{AGENT_META[a.type].icon}</span>
              <span style={{fontSize:12}}>{a.name}</span>
              <span style={{marginLeft:"auto",fontFamily:"var(--fm)",fontSize:9,color:"var(--s)"}}>{fmtFit(a.fitness)}</span>
            </div>
          ))}
        </nav>
        <div className="sb-foot">
          <div className="sys-status"><div className="s-dot"/><span>SYSTEM OPERATIONAL</span></div>
          <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginTop:5}}>
            {agents.reduce((s,a)=>s+a.executionCount,0)} tasks total
          </div>
          <div style={{fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)",marginTop:2}}>
            {fmtK(agents.reduce((s,a)=>s+a.tokensUsed,0))} tokens consumed
          </div>
        </div>
      </div>

      {/* MAIN */}
      <div className="main">
        <div className="hdr">
          <div>
            <div className="hdr-title">{HDR_MAP[tab]?.title}</div>
            <div className="hdr-path">{HDR_MAP[tab]?.path}</div>
          </div>
          <div className="flex gap8" style={{alignItems:"center"}}>
            <div style={{display:"flex",gap:4}}>
              {agents.slice(0,3).map(a=>(
                <div key={a.id} title={a.name} onClick={()=>{handleAgentSelect(a);setTab("agents");}}
                  style={{width:26,height:26,borderRadius:6,background:`${AGENT_META[a.type].color}18`,
                    border:`1px solid ${AGENT_META[a.type].color}33`,display:"flex",alignItems:"center",
                    justifyContent:"center",cursor:"pointer",fontSize:12,color:AGENT_META[a.type].color}}>
                  {AGENT_META[a.type].icon}
                </div>
              ))}
              <div style={{width:26,height:26,borderRadius:6,background:"var(--card)",border:"1px solid var(--b1)",
                display:"flex",alignItems:"center",justifyContent:"center",fontFamily:"var(--fm)",fontSize:9,color:"var(--tm)"}}>
                +{agents.length-3}
              </div>
            </div>
            <div style={{width:1,height:16,background:"var(--b1)"}}/>
            <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>AVG <span style={{color:"var(--s)"}}>{avgFitness(agents)}</span></div>
            <div style={{fontFamily:"var(--fm)",fontSize:10,color:"var(--tm)"}}>GEN <span style={{color:"var(--p)"}}>{currentGen(history)}</span></div>
            {selectedAgent && (
              <button className="btn btn-p" style={{fontSize:9,padding:"4px 10px"}} onClick={()=>setShowDNA(v=>!v)}>
                {showDNA?"HIDE":"VIEW"} DNA
              </button>
            )}
          </div>
        </div>
        <div className="content" style={{paddingRight: showDNA && selectedAgent ? 360 : 26}}>
          {tab==="dashboard"    && <Dashboard    agents={agents} tasks={tasks} skills={skills} history={history}/>}
          {tab==="agents"       && <AgentsView   agents={agents} selected={selectedAgent} setSelected={handleAgentSelect}/>}
          {tab==="chat"         && <ChatView     agents={agents} setAgents={setAgents} setMemories={setMemories}/>}
          {tab==="tasks"        && <TaskTerminal agents={agents} tasks={tasks} setTasks={setTasks} setAgents={setAgents} setMemories={setMemories}/>}
          {tab==="evolution"    && <EvolutionView agents={agents} history={history} events={events} setAgents={setAgents} setHistory={setHistory} setEvents={setEvents}/>}
          {tab==="memory"       && <MemoryView   memories={memories}/>}
          {tab==="skills"       && <SkillsView   skills={skills} setSkills={setSkills} agents={agents}/>}
          {tab==="architecture" && <ArchitectureView agents={agents} tasks={tasks} memories={memories} skills={skills}/>}
          {tab==="settings"     && <SettingsView agents={agents} setAgents={setAgents}/>}
        </div>
      </div>

      {/* DNA PANEL */}
      {showDNA && selectedAgent && (
        <DNAPanel agent={selectedAgent} onClose={()=>{setShowDNA(false);setSelectedAgent(null);}}/>
      )}
    </div>
  );
}
