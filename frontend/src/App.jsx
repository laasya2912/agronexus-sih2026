import React,{useState,useEffect,useCallback} from 'react';
import {UserCircle,Globe,Sprout,Shield,FileText,MessageSquare,Bell,Lock,LayoutDashboard,LogOut,Send,CheckCircle2,Landmark} from 'lucide-react';
const T={English:{home:'Dashboard',services:'Government Services',apps:'My Applications',grv:'Grievances',ai:'AI Mithra',consent:'Privacy & Consent',notes:'Notifications',admin:'Admin / Official',logout:'Logout',tag:'One Platform. Multiple Government Services.',apply:'Apply',check:'Check Eligibility'},
Telugu:{home:'డ్యాష్‌బోర్డ్',services:'ప్రభుత్వ సేవలు',apps:'నా దరఖాస్తులు',grv:'ఫిర్యాదులు',ai:'ఏఐ మిత్ర',consent:'గోప్యత & సమ్మతి',notes:'నోటిఫికేషన్లు',admin:'అడ్మిన్ / అధికారి',logout:'లాగ్అవుట్',tag:'ఒకే వేదిక. అనేక ప్రభుత్వ సేవలు.',apply:'దరఖాస్తు',check:'అర్హత తనిఖీ'},
Hindi:{home:'डैशबोर्ड',services:'सरकारी सेवाएं',apps:'मेरे आवेदन',grv:'शिकायतें',ai:'एआई मित्र',consent:'गोपनीयता और सहमति',notes:'सूचनाएं',admin:'एडमिन / अधिकारी',logout:'लॉगआउट',tag:'एक मंच। अनेक सरकारी सेवाएं।',apply:'आवेदन',check:'पात्रता जांचें'},
Tamil:{home:'முகப்பு',services:'அரசு சேவைகள்',apps:'என் விண்ணப்பங்கள்',grv:'புகார்கள்',ai:'ஏஐ மித்ரா',consent:'தனியுரிமை & ஒப்புதல்',notes:'அறிவிப்புகள்',admin:'நிர்வாகம் / அதிகாரி',logout:'வெளியேறு',tag:'ஒரே தளம். பல அரசு சேவைகள்.',apply:'விண்ணப்பி',check:'தகுதி சரிபார்'},
Kannada:{home:'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',services:'ಸರ್ಕಾರಿ ಸೇವೆಗಳು',apps:'ನನ್ನ ಅರ್ಜಿಗಳು',grv:'ದೂರುಗಳು',ai:'ಎಐ ಮಿತ್ರ',consent:'ಗೌಪ್ಯತೆ & ಒಪ್ಪಿಗೆ',notes:'ಅಧಿಸೂಚನೆಗಳು',admin:'ನಿರ್ವಾಹಕ / ಅಧಿಕಾರಿ',logout:'ಲಾಗ್ ಔಟ್',tag:'ಒಂದೇ ವೇದಿಕೆ. ಹಲವು ಸರ್ಕಾರಿ ಸೇವೆಗಳು.',apply:'ಅರ್ಜಿ',check:'ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಿ'}};
const PN={English:'My Profile',Telugu:'నా ప్రొఫైల్',Hindi:'मेरी प्रोफ़ाइल',Tamil:'என் சுயவிவரம்',Kannada:'ನನ್ನ ಪ್ರೊಫೈಲ್'};
const STATUS=["Submitted","Department Received","Under Review","Action Required","Approved","Rejected"],GST=["Complaint Received","Assigned","Under Review","Action Initiated","Resolved"];
const CATS=["Agriculture","Land / Revenue","Irrigation","Crop Insurance","Roads","Other"];
const col=s=>/Approved|Eligible$|Resolved/.test(s)&&!/Not|Possibly/.test(s)?'bg-green-100 text-green-800':/Reject|Not/.test(s)?'bg-red-100 text-red-800':/Action Required|Possibly/.test(s)?'bg-amber-100 text-amber-800':'bg-sky-100 text-sky-800';
const Badge=({s})=><span className={'px-2 py-0.5 rounded-full text-xs font-semibold '+col(s)}>{s}</span>;
export default function App(){
 const [tok,setTok]=useState(localStorage.getItem('t')),[user,setUser]=useState(null),[lang,setLang]=useState('English'),[tab,setTab]=useState('home'),[auth,setAuth]=useState(null),[msg,setMsg]=useState('');
 const t=T[lang];
 const api=useCallback(async(p,o={})=>{const r=await fetch('/api'+p,{...o,headers:{'Content-Type':'application/json',...(tok?{Authorization:'Bearer '+tok}:{})},body:o.body?JSON.stringify(o.body):undefined}).catch(()=>{throw new Error('Server unreachable. Is the backend running on port 8000?')});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'Please check the form inputs');return d},[tok]);
 useEffect(()=>{if(tok)api('/me').then(setUser).catch(()=>{localStorage.removeItem('t');setTok(null)})},[tok]);
 const enter=d=>{localStorage.setItem('t',d.token);setTok(d.token);setUser(d.user);setAuth(null);setTab('home')};
 const out=()=>{localStorage.removeItem('t');setTok(null);setUser(null)};
 const Lang=<select className="rounded border px-2 py-1 text-sm text-black" value={lang} onChange={e=>setLang(e.target.value)}>{Object.keys(T).map(l=><option key={l}>{l}</option>)}</select>;
 if(!user)return auth?<Auth mode={auth} api={api} enter={enter} back={()=>setAuth(null)}/>:<Landing t={t} Lang={Lang} go={setAuth}/>;
 const staff=['official','admin'].includes(user.role);
 const nav=[['home',t.home,LayoutDashboard],['profile',PN[lang],UserCircle],['services',t.services,Landmark],['apps',t.apps,FileText],['ai',t.ai,Sprout],['grv',t.grv,MessageSquare],['consent',t.consent,Lock],['notes',t.notes,Bell],...(staff?[['admin',t.admin,Shield]]:[])];
 const P={home:Home,profile:Profile,services:Services,apps:Apps,grv:Grievances,ai:AI,consent:Consent,notes:Notes,admin:Admin}[tab];
 return <div className="min-h-screen md:flex">
  <aside className="bg-leaf-900 text-white md:w-60 md:min-h-screen p-3 flex md:flex-col gap-1 overflow-x-auto">
   <div className="font-bold text-lg px-2 py-2 flex items-center gap-2 shrink-0"><Sprout className="text-wheat"/>AgroNexus</div>
   {nav.map(([k,l,I])=><button key={k} onClick={()=>{setTab(k);setMsg('')}} className={'flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap text-left '+(tab===k?'bg-leaf-600':'hover:bg-leaf-700')}><I size={16}/>{l}</button>)}
   <button onClick={out} className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-leaf-700 md:mt-auto"><LogOut size={16}/>{t.logout}</button></aside>
  <main className="flex-1 p-4 md:p-6 max-w-5xl">
   <div className="flex justify-between items-center mb-4 gap-2"><div><div className="font-semibold">{user.name} <span className="text-xs bg-wheat/30 px-2 rounded">{user.role}</span></div><div className="text-xs text-slate-500">{t.tag}</div></div>{Lang}</div>
   <P api={api} user={user} t={t} setTab={setTab} lang={lang}/></main></div>;
}
function Landing({t,Lang,go}){
 const F=[[UserCircle,'One Farmer Profile','Securely maintain farmer information in one profile.'],[Landmark,'Unified Government Services','Access multiple government services from one platform.'],[FileText,'Application Tracking','Track submitted applications and their current status.'],[Sprout,'AI Assistance','Get multilingual assistance for farmer and government-service queries.'],[MessageSquare,'Grievance Redressal','Submit and track village-level grievances through the platform.'],[Globe,'Multilingual Access','Provide the interface and assistance in supported regional languages.']];
 return <div><header className="bg-leaf-900 text-white"><div className="max-w-5xl mx-auto p-4 flex justify-between items-center"><b className="flex gap-2"><Sprout className="text-wheat"/>AgroNexus</b>{Lang}</div>
  <div className="max-w-5xl mx-auto px-4 py-14"><h1 className="text-4xl md:text-6xl font-bold tracking-wide">AGRONEXUS</h1><p className="text-xl text-wheat mt-2">{t.tag}</p>
   <p className="mt-4 max-w-xl text-green-100">Access agricultural schemes, applications, grievances and government services through one unified digital platform.</p>
   <div className="mt-6 flex gap-3 flex-wrap"><button className="btn bg-wheat !text-black" onClick={()=>go('register')}>Get Started</button><button className="btn2 !text-white" onClick={()=>go('login')}>Login</button></div></div></header>
  <section className="max-w-5xl mx-auto p-4 py-10"><h2 className="text-2xl font-bold text-leaf-900 mb-4">AgroNexus Features</h2>
   <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{F.map(([I,h,d])=><div key={h} className="card"><I className="text-leaf-600 mb-2"/><b>{h}</b><p className="text-sm text-slate-600 mt-1">{d}</p></div>)}</div>
   <p className="text-xs text-slate-400 mt-10 text-center">Prototype for SIH 2026. Government integrations are simulated (Demo Government API), not live.</p></section></div>;
}
function Profile({user}){
 const R=[['Name',user.name],['Farmer ID',user.farmer_id||'-'],['Mobile',user.mobile],['Age',user.age],['Gender',user.gender],['Village',user.village],['District',user.district],['State',user.state],['Land area (acres)',user.land],['Soil type',user.soil],['Current crop',user.crop]];
 return <div className="space-y-3"><h2 className="text-xl font-bold">My Profile</h2><div className="card grid sm:grid-cols-2 gap-2">{R.map(([a,b])=><div key={a} className="text-sm"><span className="text-slate-500">{a}</span><div className="font-medium">{b}</div></div>)}</div><p className="text-xs text-slate-500">This one profile is reused across all government services you apply to.</p></div>;
}
function Auth({mode,api,enter,back}){
 const [f,setF]=useState({name:'',age:30,gender:'Male',mobile:'',password:'',village:'',district:'',state:'Andhra Pradesh',land:2,soil:'Alluvial',crop:'Paddy',role:'farmer'}),[err,setErr]=useState('');
 const set=k=>e=>setF({...f,[k]:e.target.value}),reg=mode==='register';
 const go=async e=>{e.preventDefault();setErr('');try{enter(await api(reg?'/auth/register':'/auth/login',{method:'POST',body:reg?{...f,age:+f.age,land:+f.land}:{mobile:f.mobile,password:f.password}}))}catch(x){setErr(x.message)}};
 const fields=reg?[['name','Name'],['age','Age','number'],['mobile','Mobile (10 digits)'],['password','Password (min 6)','password'],['village','Village'],['district','District'],['state','State'],['land','Land area (acres)','number'],['soil','Soil type'],['crop','Current crop']]:[['mobile','Mobile'],['password','Password','password']];
 return <form onSubmit={go} className="max-w-md mx-auto p-4 space-y-3"><h2 className="text-2xl font-bold">{reg?'Register':'Login'}</h2>
  {fields.map(([k,l,ty])=><label key={k} className="block text-sm">{l}<input required type={ty||'text'} className="inp" value={f[k]} onChange={set(k)}/></label>)}
  {reg&&<><label className="block text-sm">Gender<select className="inp" value={f.gender} onChange={set('gender')}><option>Male</option><option>Female</option><option>Other</option></select></label>
  <label className="block text-sm">Register as<select className="inp" value={f.role} onChange={set('role')}><option value="farmer">Farmer</option><option value="village_head">Village Head</option></select></label><p className="text-xs text-slate-500">No Aadhaar is collected. A Farmer ID is generated internally.</p></>}
  {err&&<p className="text-red-600 text-sm">{err}</p>}<button className="btn w-full">{reg?'Create account':'Login'}</button><button type="button" className="text-sm underline" onClick={back}>Back</button>
  {!reg&&<p className="text-xs text-slate-500">Demo: 9000000001 (farmer), 9000000004 (village head), 9000000005 (official), 9000000006 (admin) / Demo@123</p>}</form>;
}
const useLoad=(api,p)=>{const [d,setD]=useState(null),[e,setE]=useState('');const r=()=>api(p).then(setD).catch(x=>setE(x.message));useEffect(()=>{r()},[p]);return [d,r,e]};
const Err=({e})=>e?<p className="text-red-600 text-sm">{e}</p>:null;
function Home({api,user,t,setTab}){
 const [v]=useLoad(api,user.role==='village_head'?'/village/summary':'/me'),[msg,setMsg]=useState('');
 const vh=user.role==='village_head';
 return <div className="space-y-4"><div className="card"><h2 className="font-bold text-xl">Welcome, {user.name}</h2><p className="text-sm text-slate-600">Farmer ID: {user.farmer_id||'-'} · {user.village}, {user.district} · Crop: {user.crop} · {user.land} acres</p></div>
  {vh&&v&&<div className="grid grid-cols-3 gap-3">{[['Farmers',v.farmers],['Active grievances',v.active],['Resolved',v.resolved]].map(([a,b])=><div key={a} className="card text-center"><div className="text-2xl font-bold">{b}</div>{a}</div>)}</div>}
  {vh&&<div className="card flex gap-2"><input className="inp" placeholder="Publish village notification" value={msg} onChange={e=>setMsg(e.target.value)}/><button className="btn" onClick={()=>api('/village/notify',{method:'POST',body:{text:msg}}).then(()=>setMsg('')).catch(e=>alert(e.message))}>Publish</button></div>}
  <div className="grid sm:grid-cols-3 gap-3">{[['profile','My Profile'],['services','Government Services'],['apps','My Applications'],['grv','Grievances'],['ai','AI Mithra'],['notes','Notifications']].map(([k,l])=><button key={k} onClick={()=>setTab(k)} className="card text-left font-semibold hover:border-leaf-600">{l}</button>)}</div>
  <div className="card"><h3 className="font-semibold mb-2">Connected Government Services</h3><div className="grid sm:grid-cols-2 gap-2">{['Agriculture Department','Revenue / Land Records','Welfare & Schemes','Crop Insurance'].map(x=><div key={x} className="flex justify-between border rounded p-2 text-sm">{x}<span>🟢 Connected</span></div>)}</div></div></div>;
}
function Services({api,t,user}){
 const [el,r,e]=useLoad(api,'/eligibility'),[m,setM]=useState(''),[open,setOpen]=useState(null);
 const apply=s=>api('/applications',{method:'POST',body:{service:s}}).then(()=>setM(s+': application submitted. See My Applications.')).catch(x=>setM(x.message));
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.services}</h2><p className="text-xs text-slate-500">Rule-based eligibility engine (no AI). Departments are simulated.</p>{m&&<p className="card text-sm">{m}</p>}<Err e={e}/>
  {el?.map(s=><div key={s.scheme} className="card"><div className="flex justify-between flex-wrap gap-2"><div><b>{s.scheme}</b><div className="text-xs text-slate-500">{s.dept} Department</div></div>{open===s.scheme&&<Badge s={s.verdict}/>}</div>
   <p className="text-sm mt-1">{s.desc}</p><p className="text-sm"><b>Benefits:</b> {s.benefits}</p><p className="text-sm"><b>Documents:</b> {s.docs.join(', ')}</p>
   {open===s.scheme&&<p className="text-sm mt-2 bg-leaf-50 p-2 rounded"><b>Why:</b> {s.reason}</p>}
   <div className="flex gap-2 mt-2"><button className="btn2" onClick={()=>setOpen(open===s.scheme?null:s.scheme)}>{open===s.scheme?'Hide':'View Details'} / {t.check}</button>{user.role!=='official'&&<button className="btn" disabled={s.verdict==='Not Eligible'} onClick={()=>apply(s.scheme)}>{t.apply}</button>}</div></div>)}</div>;
}
const Timeline=({h})=><ol className="border-l-2 border-leaf-600 ml-2 mt-2 space-y-1">{h.map(([s,ts],i)=><li key={i} className="ml-3 text-sm"><b>{s}</b> <span className="text-xs text-slate-500">{new Date(ts).toLocaleString()}</span></li>)}</ol>;
function Apps({api,t,user}){
 const [a,r,e]=useLoad(api,'/applications'),[sel,setSel]=useState(null),[st,setSt]=useState('Under Review'),[rm,setRm]=useState('');
 const staff=['official','admin'].includes(user.role);
 const up=()=>api('/applications/'+sel.id,{method:'PATCH',body:{status:st,remark:rm}}).then(x=>{setSel(x);r()}).catch(x=>alert(x.message));
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.apps}</h2><Err e={e}/>{a?.length===0&&<p>No applications yet.</p>}
  {a?.map(x=><div key={x.id} onClick={()=>setSel(x)} className="card cursor-pointer hover:border-leaf-600"><div className="flex justify-between"><b>{x.service}</b><Badge s={x.status}/></div><div className="text-xs text-slate-500">{x.dept} · {x.app_id}{staff&&' · '+x.farmer_id}</div>
   {sel?.id===x.id&&<div onClick={e=>e.stopPropagation()}><Timeline h={sel.history}/>{sel.remark&&<p className="text-sm mt-1">Remark: {sel.remark}</p>}
    {staff&&<div className="flex gap-2 mt-2 flex-wrap"><select className="inp !w-auto" value={st} onChange={e=>setSt(e.target.value)}>{STATUS.map(s=><option key={s}>{s}</option>)}</select><input className="inp !w-auto flex-1" placeholder="Remarks" value={rm} onChange={e=>setRm(e.target.value)}/><button className="btn" onClick={up}>Update</button></div>}</div>}</div>)}</div>;
}
function Grievances({api,t,user}){
 const [g,r,e]=useLoad(api,'/grievances'),[f,setF]=useState({category:CATS[0],description:'',village:user.village||'',priority:'Medium'}),[m,setM]=useState('');
 const staff=['official','admin'].includes(user.role);
 const sub=async ev=>{ev.preventDefault();try{const x=await api('/grievances',{method:'POST',body:f});setM(`Submitted: ${x.gid} routed to ${x.dept} Department`);setF({...f,description:''});r()}catch(x){setM(x.message)}};
 const upd=(id,s)=>api('/grievances/'+id,{method:'PATCH',body:{status:s,remark:'Updated by official'}}).then(r).catch(x=>alert(x.message));
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.grv}</h2>
  {!staff&&<form onSubmit={sub} className="card space-y-2"><div className="grid sm:grid-cols-3 gap-2"><select className="inp" value={f.category} onChange={e=>setF({...f,category:e.target.value})}>{CATS.map(c=><option key={c}>{c}</option>)}</select><input className="inp" placeholder="Village" value={f.village} onChange={e=>setF({...f,village:e.target.value})}/><select className="inp" value={f.priority} onChange={e=>setF({...f,priority:e.target.value})}><option>Low</option><option>Medium</option><option>High</option></select></div>
   <textarea required minLength={10} className="inp" placeholder="Describe the issue (min 10 chars)" value={f.description} onChange={e=>setF({...f,description:e.target.value})}/><button className="btn">Submit grievance</button>{m&&<p className="text-sm">{m}</p>}</form>}
  <Err e={e}/>{g?.map(x=><div key={x.gid} className="card"><div className="flex justify-between"><b>{x.gid} · {x.category}</b><Badge s={x.status}/></div><p className="text-sm">{x.description}</p><p className="text-xs text-slate-500">→ {x.dept} Department · {x.village} · {x.priority}</p>
   <div className="flex gap-1 mt-2 flex-wrap">{GST.map((s,i)=><span key={s} className={'text-xs px-2 py-0.5 rounded '+(i<=GST.indexOf(x.status)?'bg-leaf-600 text-white':'bg-slate-100')}>{s}</span>)}</div>
   {staff&&<select className="inp !w-auto mt-2" value={x.status} onChange={e=>upd(x.gid,e.target.value)}>{GST.map(s=><option key={s}>{s}</option>)}</select>}</div>)}</div>;
}
function AI({api,t,lang}){
 const [c,setC]=useState([{r:'ai',x:'Namaste! I am AI Mithra. Ask about schemes, application status, documents or grievances (English/Telugu/Hindi).'}]),[q,setQ]=useState('');
 const send=async(text)=>{if(!text)return;setC(p=>[...p,{r:'me',x:text}]);setQ('');try{const d=await api('/ai/ask',{method:'POST',body:{q:text}});setC(p=>[...p,{r:'ai',x:d.answer,m:d.mode}])}catch(e){setC(p=>[...p,{r:'ai',x:'Sorry: '+e.message}])}};
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.ai}</h2><p className="text-sm text-slate-500">Your Government Service Assistant</p>
  <div className="flex gap-2 flex-wrap">{['Which schemes am I eligible for?','What is my crop insurance status?','Why is my application pending?','What documents do I need?','How can I raise a grievance?'].map(s=><button key={s} className="btn2 !text-xs" onClick={()=>send(s)}>{s}</button>)}</div>
  <div className="card space-y-2 min-h-[240px]">{c.map((m,i)=><div key={i} className={'whitespace-pre-line text-sm p-2 rounded-lg max-w-[85%] '+(m.r==='me'?'bg-leaf-600 text-white ml-auto':'bg-leaf-50')}>{m.x}{m.m&&<div className="text-[10px] opacity-60">mode: {m.m}</div>}</div>)}</div>
  <div className="flex gap-2"><input className="inp" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send(q)} placeholder="Ask AI Mithra..."/><button className="btn" onClick={()=>send(q)}><Send size={16}/></button></div></div>;
}
function Consent({api,t}){
 const [c,r,e]=useLoad(api,'/consent');
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.consent}</h2><Err e={e}/>{c?.map(x=><label key={x.key} className="card flex justify-between items-center gap-3"><span className="text-sm">{x.label}<br/><Badge s={x.granted?'Approved':'Rejected'}/> {x.granted?'Consent Granted':'Consent Revoked'}</span>
  <input type="checkbox" className="w-5 h-5" checked={x.granted} onChange={()=>api('/consent',{method:'PUT',body:{key:x.key,granted:!x.granted}}).then(r)}/></label>)}</div>;
}
function Notes({api,t}){const [n,,e]=useLoad(api,'/notifications');return <div className="space-y-2"><h2 className="text-xl font-bold">{t.notes}</h2><Err e={e}/>{n?.length===0&&<p>No notifications.</p>}{n?.map((x,i)=><div key={i} className="card text-sm">{x.text}<div className="text-xs text-slate-500">{new Date(x.ts).toLocaleString()}</div></div>)}</div>}
function Admin({api,t,user}){
 const [o,,e]=useLoad(api,'/admin/overview'),[hub]=useLoad(api,'/hub/status');
 const K=o&&[['Total Applications',o.apps],['Pending',o.pending],['Under Review',o.review],['Action Required',o.action],['Approved',o.approved],['Rejected',o.rejected],['Active Grievances',o.grv_active],['Resolved',o.grv_resolved],['SLA Breaches',o.sla],['Users',o.users]];
 return <div className="space-y-3"><h2 className="text-xl font-bold">{t.admin}</h2><Err e={e}/><p className="text-sm">Update application/grievance statuses from My Applications and Grievances.</p>
  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">{K?.map(([a,b])=><div key={a} className="card text-center"><div className="text-2xl font-bold">{b}</div><div className="text-xs">{a}</div></div>)}</div>
  <div className="card"><b>API health (simulated departments)</b>{hub?.connectors.map(c=><div key={c.dept} className="text-sm flex justify-between border-b py-1"><span>{c.dept}</span><span>{c.status} · {c.calls} calls · {c.fail_rate}% fail</span></div>)}</div>
  <div className="card"><b>Audit log</b>{o?.audit.map((a,i)=><div key={i} className="text-xs font-mono">{a.ts} {a.actor}: {a.action}</div>)}</div></div>;
}
