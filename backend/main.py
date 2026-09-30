import os, hashlib, secrets, json, time, datetime as dt, urllib.request
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import jwt

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./agronexus.db"), connect_args={"check_same_thread": False})
Session = sessionmaker(engine); Base = declarative_base()
now = lambda: dt.datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); name = Column(String); role = Column(String, default="farmer")
    mobile = Column(String, unique=True); pw = Column(String); farmer_id = Column(String); age = Column(Integer)
    gender = Column(String); village = Column(String); district = Column(String); state = Column(String)
    land = Column(Float); soil = Column(String); crop = Column(String)
class Scheme(Base):  # scheme + rule columns
    __tablename__ = "schemes"
    id = Column(Integer, primary_key=True); name = Column(String); dept = Column(String); desc = Column(Text)
    docs = Column(String); benefits = Column(String); states = Column(String); crops = Column(String)
    min_land = Column(Float); max_land = Column(Float); min_age = Column(Integer)
class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True); app_id = Column(String); farmer_id = Column(String); service = Column(String)
    dept = Column(String); status = Column(String); history = Column(Text); remark = Column(String, default=""); updated = Column(DateTime, default=now)
class Grievance(Base):
    __tablename__ = "grievances"
    id = Column(Integer, primary_key=True); gid = Column(String); farmer_id = Column(String); category = Column(String)
    description = Column(Text); village = Column(String); priority = Column(String); dept = Column(String)
    status = Column(String, default="Complaint Received"); remark = Column(String, default=""); created = Column(DateTime, default=now)
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True); farmer_id = Column(String); text = Column(String); ts = Column(DateTime, default=now)
class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True); farmer_id = Column(String); key = Column(String); granted = Column(Boolean, default=True); ts = Column(DateTime, default=now)
class AuditLog(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True); ts = Column(DateTime, default=now); actor = Column(String); action = Column(String)

STATUS = ["Submitted", "Department Received", "Under Review", "Action Required", "Approved", "Rejected"]
GSTAT = ["Complaint Received", "Assigned", "Under Review", "Action Initiated", "Resolved"]
SERVICES = {"Farmer Welfare Scheme": "Welfare", "Crop Insurance": "Insurance", "Soil Health Service": "Agriculture",
            "Agricultural Subsidy": "Agriculture", "Land Record Verification": "Revenue", "Irrigation Support": "Water Resources"}
ROUTE = {"Agriculture": "Agriculture", "Land / Revenue": "Revenue", "Irrigation": "Water Resources", "Crop Insurance": "Insurance", "Roads": "Rural Development", "Other": "Agriculture"}
DEPTS = ["Agriculture", "Revenue", "Welfare", "Insurance", "Water Resources"]
# each simulated department uses its OWN response field names; normalize() unifies them
FIELDMAP = {"Agriculture": ("ref", "state", "upd"), "Revenue": ("applicationNo", "currentStatus", "modified"),
            "Insurance": ("claimId", "stage", "updatedAt"), "Welfare": ("id", "status", "ts"), "Water Resources": ("reqNo", "phase", "when")}
STATS = defaultdict(lambda: {"calls": 0, "fail": 0, "ms": 0.0}); LASTSYNC = {}

def hpw(p, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 100000).hex()
def chk(p, h): return hpw(p, h.split("$")[0]) == h
def log(db, actor, action): db.add(AuditLog(actor=actor, action=action)); db.commit()
def note(db, fid, text): db.add(Notification(farmer_id=fid, text=text)); db.commit()

app = FastAPI(title="AgroNexus API", description="Prototype. Government APIs under /api/gov are SIMULATED (Demo Government API).")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def telemetry(req: Request, call_next):
    t = time.time(); r = await call_next(req); p = req.url.path.split("/")
    if len(p) > 3 and p[2] == "gov":
        d = p[3].title() if p[3] != "water" else "Water Resources"; s = STATS[d]
        s["calls"] += 1; s["ms"] += (time.time() - t) * 1000; s["fail"] += r.status_code >= 400; LASTSYNC[d] = now().isoformat()
    return r

def get_db():
    db = Session()
    try: yield db
    finally: db.close()
bearer = HTTPBearer(auto_error=False)
def cur(c=Depends(bearer), db=Depends(get_db)):
    if not c: raise HTTPException(401, "Please log in first")
    try: u = db.get(User, int(jwt.decode(c.credentials, SECRET, algorithms=["HS256"])["sub"]))
    except Exception: raise HTTPException(401, "Session expired, please log in again")
    if not u: raise HTTPException(401, "Unknown user")
    return u
def need(*roles):
    def f(u=Depends(cur)):
        if u.role not in roles: raise HTTPException(403, "Not allowed for your role")
        return u
    return f
staff = need("official", "admin")
pub = lambda u: {k: getattr(u, k) for k in ["id", "name", "role", "mobile", "farmer_id", "age", "gender", "village", "district", "state", "land", "soil", "crop"]}

class Reg(BaseModel):
    name: str = Field(min_length=2, max_length=60); age: int = Field(ge=18, le=100); gender: str; mobile: str = Field(pattern=r"^\d{10}$")
    password: str = Field(min_length=6); village: str; district: str; state: str; land: float = Field(gt=0, le=500); soil: str; crop: str
    role: str = "farmer"
class Login(BaseModel): mobile: str; password: str
def token(u): return {"token": jwt.encode({"sub": str(u.id), "exp": now() + dt.timedelta(hours=12)}, SECRET, algorithm="HS256"), "user": pub(u)}

@app.post("/api/auth/register", tags=["auth"])
def register(b: Reg, db=Depends(get_db)):
    if db.query(User).filter_by(mobile=b.mobile).first(): raise HTTPException(400, "Mobile already registered")
    d = b.model_dump(); pw = d.pop("password"); d["role"] = "village_head" if d["role"] == "village_head" else "farmer"
    u = User(**d, pw=hpw(pw), farmer_id=f"AGN-{secrets.randbelow(900000) + 100000}"); db.add(u); db.commit()
    log(db, u.farmer_id, "Farmer registered"); note(db, u.farmer_id, "Welcome to AgroNexus! Your Farmer ID is " + u.farmer_id)
    return token(u)
@app.post("/api/auth/login", tags=["auth"])
def login(b: Login, db=Depends(get_db)):
    u = db.query(User).filter_by(mobile=b.mobile).first()
    if not u or not chk(b.password, u.pw): raise HTTPException(401, "Invalid mobile or password")
    log(db, u.farmer_id or u.name, "Login"); return token(u)
@app.get("/api/me", tags=["auth"])
def me(u=Depends(cur)): return pub(u)

def eligibility(u, db):
    out = []
    for s in db.query(Scheme).all():
        fails, maybe = [], []
        if u.state not in s.states.split(","): fails.append(f"scheme is for {s.states}, you are registered in {u.state}")
        if u.age < s.min_age: fails.append(f"minimum age is {s.min_age}")
        if u.land < s.min_land or u.land > s.max_land: fails.append(f"landholding {u.land} acres is outside {s.min_land}-{s.max_land} acres")
        if s.crops != "*" and u.crop.lower() not in s.crops.lower().split(","): maybe.append(f"your crop '{u.crop}' is not in the listed crops ({s.crops}); verify with the department")
        v = "Not Eligible" if fails else "Possibly Eligible" if maybe else "Eligible"
        why = ("Rule check failed: " + "; ".join(fails)) if fails else ("Needs verification: " + "; ".join(maybe)) if maybe else \
            f"Farmer is registered in {u.state}, meets the age rule and holds {u.land} acres within the required range, with an eligible crop."
        out.append({"scheme": s.name, "dept": s.dept, "desc": s.desc, "verdict": v, "reason": why, "docs": s.docs.split(","), "benefits": s.benefits})
    return out
@app.get("/api/eligibility", tags=["services"])
def elig(u=Depends(cur), db=Depends(get_db)):
    log(db, u.farmer_id, "Scheme eligibility checked"); return eligibility(u, db)

def new_app(db, fid, service, status="Submitted", ago=0):
    d = SERVICES[service]; a = Application(app_id=f"{d[:3].upper()}-{secrets.randbelow(90000) + 10000}", farmer_id=fid, service=service, dept=d, status=status)
    a.history = json.dumps([[s, (now() - dt.timedelta(days=ago)).isoformat()] for s in STATUS[:STATUS.index(status) + 1] if s != "Rejected"] if status != "Rejected" else [["Submitted", now().isoformat()], ["Rejected", now().isoformat()]])
    db.add(a); db.commit(); return a
ser = lambda a: {"id": a.id, "app_id": a.app_id, "farmer_id": a.farmer_id, "service": a.service, "dept": a.dept, "status": a.status, "history": json.loads(a.history), "remark": a.remark, "last_updated": a.updated.isoformat()}
class Apply(BaseModel): service: str
@app.post("/api/applications", tags=["applications"])
def apply(b: Apply, u=Depends(cur), db=Depends(get_db)):
    if b.service not in SERVICES: raise HTTPException(400, "Unknown service")
    if db.query(Application).filter_by(farmer_id=u.farmer_id, service=b.service).filter(Application.status.notin_(["Approved", "Rejected"])).first():
        raise HTTPException(400, "You already have an active application for this service")
    a = new_app(db, u.farmer_id, b.service); log(db, u.farmer_id, f"Applied: {b.service}"); note(db, u.farmer_id, f"Your {b.service} application {a.app_id} was submitted."); return ser(a)
@app.get("/api/applications", tags=["applications"])
def apps(u=Depends(cur), db=Depends(get_db)):
    q = db.query(Application)
    if u.role not in ("official", "admin"): q = q.filter_by(farmer_id=u.farmer_id)
    return [ser(a) for a in q.order_by(Application.id.desc()).all()]
class Upd(BaseModel): status: str; remark: str = ""
@app.patch("/api/applications/{i}", tags=["applications"])
def upd_app(i: int, b: Upd, u=Depends(staff), db=Depends(get_db)):
    a = db.get(Application, i)
    if not a or b.status not in STATUS: raise HTTPException(400, "Invalid application or status")
    h = json.loads(a.history); h.append([b.status, now().isoformat()]); a.history = json.dumps(h); a.status = b.status; a.remark = b.remark; a.updated = now(); db.commit()
    note(db, a.farmer_id, f"Your {a.service} application moved to {b.status}." + (" Additional document required." if b.status == "Action Required" else ""))
    log(db, u.name, f"Application {a.app_id} -> {b.status}"); return ser(a)

class Grv(BaseModel): category: str; description: str = Field(min_length=10); village: str; priority: str = "Medium"
gser = lambda g: {"gid": g.gid, "farmer_id": g.farmer_id, "category": g.category, "description": g.description, "village": g.village, "priority": g.priority, "dept": g.dept, "status": g.status, "remark": g.remark, "created": g.created.isoformat()}
@app.post("/api/grievances", tags=["grievances"])
def add_grv(b: Grv, u=Depends(need("farmer", "village_head")), db=Depends(get_db)):
    if b.category not in ROUTE: raise HTTPException(400, "Unknown category")
    g = Grievance(gid=f"GRV-{1000 + db.query(Grievance).count() + 25}", farmer_id=u.farmer_id, category=b.category, description=b.description, village=b.village, priority=b.priority, dept=ROUTE[b.category])
    db.add(g); db.commit(); note(db, u.farmer_id, f"Grievance {g.gid} routed to {g.dept} Department."); log(db, u.farmer_id, f"Grievance {g.gid} filed"); return gser(g)
@app.get("/api/grievances", tags=["grievances"])
def grvs(u=Depends(cur), db=Depends(get_db)):
    q = db.query(Grievance)
    if u.role == "farmer": q = q.filter_by(farmer_id=u.farmer_id)
    elif u.role == "village_head": q = q.filter_by(village=u.village)
    return [gser(g) for g in q.order_by(Grievance.id.desc()).all()]
@app.patch("/api/grievances/{gid}", tags=["grievances"])
def upd_grv(gid: str, b: Upd, u=Depends(staff), db=Depends(get_db)):
    g = db.query(Grievance).filter_by(gid=gid).first()
    if not g or b.status not in GSTAT: raise HTTPException(400, "Invalid grievance or status")
    g.status = b.status; g.remark = b.remark; db.commit(); note(db, g.farmer_id, f"Grievance {gid}: {b.status}" + (" - action has been initiated." if b.status == "Action Initiated" else "")); log(db, u.name, f"Grievance {gid} -> {b.status}"); return gser(g)

@app.get("/api/notifications", tags=["notifications"])
def notes(u=Depends(cur), db=Depends(get_db)):
    return [{"text": n.text, "ts": n.ts.isoformat()} for n in db.query(Notification).filter_by(farmer_id=u.farmer_id).order_by(Notification.id.desc()).limit(50)]
class Pub(BaseModel): text: str = Field(min_length=3)
@app.post("/api/village/notify", tags=["village"])
def vnotify(b: Pub, u=Depends(need("village_head")), db=Depends(get_db)):
    for f in db.query(User).filter_by(village=u.village, role="farmer"): db.add(Notification(farmer_id=f.farmer_id, text=f"[{u.village} Village Head] {b.text}"))
    db.commit(); return {"ok": True}
@app.get("/api/village/summary", tags=["village"])
def vsum(u=Depends(need("village_head")), db=Depends(get_db)):
    g = db.query(Grievance).filter_by(village=u.village).all()
    return {"farmers": db.query(User).filter_by(village=u.village, role="farmer").count(), "active": sum(x.status != "Resolved" for x in g), "resolved": sum(x.status == "Resolved" for x in g)}

CONSENTS = {"land": "Share land information with Agriculture Department", "crop": "Share crop information with Welfare Department", "application": "Share application information with relevant government services"}
@app.get("/api/consent", tags=["consent"])
def get_c(u=Depends(cur), db=Depends(get_db)):
    r = {c.key: c.granted for c in db.query(Consent).filter_by(farmer_id=u.farmer_id)}
    return [{"key": k, "label": v, "granted": r.get(k, True)} for k, v in CONSENTS.items()]
class Cons(BaseModel): key: str; granted: bool
@app.put("/api/consent", tags=["consent"])
def put_c(b: Cons, u=Depends(cur), db=Depends(get_db)):
    if b.key not in CONSENTS: raise HTTPException(400, "Unknown consent")
    c = db.query(Consent).filter_by(farmer_id=u.farmer_id, key=b.key).first() or Consent(farmer_id=u.farmer_id, key=b.key)
    c.granted = b.granted; c.ts = now(); db.add(c); db.commit(); log(db, u.farmer_id, f"Consent {'granted' if b.granted else 'revoked'}: {b.key}"); return {"ok": True}

# ---------- Demo Government API (simulated) ----------
gov = lambda d: None
def own(u, fid):
    if u.role == "farmer" and u.farmer_id != fid: raise HTTPException(403, "Cannot access another farmer's data")
def farmer(db, fid):
    f = db.query(User).filter_by(farmer_id=fid).first()
    if not f: raise HTTPException(404, "Farmer not found")
    return f
def consented(db, fid, key): 
    c = db.query(Consent).filter_by(farmer_id=fid, key=key).first(); return c.granted if c else True
@app.get("/api/gov/agriculture/profile/{fid}", tags=["Demo Government API"])
def g_agri(fid: str, u=Depends(cur), db=Depends(get_db)):
    own(u, fid); f = farmer(db, fid); log(db, u.name, "Farmer profile accessed")
    return {"source": "Demo Government API - Agriculture", "farmerName": f.name, "cropGrown": f.crop, "acres": f.land if consented(db, fid, "crop") else None}
@app.get("/api/gov/land/{fid}", tags=["Demo Government API"])
def g_land(fid: str, u=Depends(cur), db=Depends(get_db)):
    own(u, fid); f = farmer(db, fid); log(db, u.name, "Land record verified")
    if not consented(db, fid, "land"): raise HTTPException(403, "Farmer has revoked land-data consent")
    return {"source": "Demo Government API - Revenue", "survey_no": f"{f.state[:2].upper()}/{f.id * 37}/A", "extent_ac": f.land, "verified": True}
@app.get("/api/gov/schemes/{fid}", tags=["Demo Government API"])
def g_sch(fid: str, u=Depends(cur), db=Depends(get_db)): own(u, fid); return eligibility(farmer(db, fid), db)
@app.get("/api/gov/insurance/{fid}", tags=["Demo Government API"])
def g_ins(fid: str, u=Depends(cur), db=Depends(get_db)):
    own(u, fid); f = farmer(db, fid); a = db.query(Application).filter_by(farmer_id=fid, service="Crop Insurance").first()
    return {"source": "Demo Government API - Insurance", "crop": f.crop, "sum_insured_inr": int(f.land * 40000), "application_status": a.status if a else "Not applied"}
def normalize(a):
    ref, st, up = FIELDMAP[a.dept]; raw = {ref: a.app_id, st: a.status, up: a.updated.isoformat()}
    return {"raw_from_department": raw, "normalized": {"service_id": a.service, "department": a.dept, "status": raw[st], "application_id": raw[ref], "last_updated": raw[up],
            "required_action": "Upload additional document" if a.status == "Action Required" else "None"}}
@app.get("/api/gov/applications/{fid}", tags=["Demo Government API"])
def g_apps(fid: str, u=Depends(cur), db=Depends(get_db)):
    own(u, fid); log(db, u.name, "Application status retrieved")
    return [normalize(a) for a in db.query(Application).filter_by(farmer_id=fid)]
@app.post("/api/gov/grievances", tags=["Demo Government API"])
def g_grv(b: Grv, u=Depends(cur), db=Depends(get_db)): return add_grv(b, u, db)
@app.get("/api/hub/status", tags=["hub"])
def hub(u=Depends(cur), db=Depends(get_db)):
    out = []
    for d in DEPTS:
        s = STATS[d]; out.append({"dept": d, "status": "Healthy", "calls": s["calls"], "fail_rate": round(100 * s["fail"] / s["calls"], 1) if s["calls"] else 0,
                                  "avg_ms": round(s["ms"] / s["calls"], 1) if s["calls"] else 0, "last_sync": LASTSYNC.get(d, "not yet")})
    return {"label": "Prototype Integration - simulated departmental APIs", "connectors": out,
            "unified": [normalize(a) for a in db.query(Application).filter_by(farmer_id=u.farmer_id)] if u.farmer_id else []}
@app.get("/api/admin/overview", tags=["admin"])
def admin(u=Depends(staff), db=Depends(get_db)):
    A = db.query(Application).all(); G = db.query(Grievance).all(); c = lambda s: sum(a.status == s for a in A)
    sla = sum(g.status != "Resolved" and (now() - g.created).days >= 7 for g in G)
    return {"apps": len(A), "pending": c("Submitted") + c("Department Received"), "review": c("Under Review"), "action": c("Action Required"), "approved": c("Approved"), "rejected": c("Rejected"),
            "grv_active": sum(g.status != "Resolved" for g in G), "grv_resolved": sum(g.status == "Resolved" for g in G), "sla": sla, "users": db.query(User).count(),
            "audit": [{"ts": a.ts.strftime("%H:%M:%S"), "actor": a.actor, "action": a.action} for a in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(25)]}

class Ask(BaseModel): q: str = Field(min_length=2, max_length=500)
@app.post("/api/ai/ask", tags=["ai"])
def ask(b: Ask, u=Depends(cur), db=Depends(get_db)):
    el = eligibility(u, db); A = db.query(Application).filter_by(farmer_id=u.farmer_id).all(); q = b.q.lower()
    ctx = {"profile": pub(u), "eligibility": [(e["scheme"], e["verdict"]) for e in el], "applications": [(a.service, a.status, a.remark) for a in A]}
    key = os.getenv("GEMINI_API_KEY")
    if key:
        try:
            body = json.dumps({"contents": [{"parts": [{"text": "You are AI Mithra, an assistant for Indian farmers using AgroNexus (a prototype with simulated data). Answer ONLY from this data, briefly, in the user's language.\nDATA: " + json.dumps(ctx) + "\nQUESTION: " + b.q}]}]}).encode()
            r = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}", body, {"Content-Type": "application/json"})
            return {"mode": "gemini", "answer": json.load(urllib.request.urlopen(r, timeout=15))["candidates"][0]["content"]["parts"][0]["text"]}
        except Exception: pass
    has = lambda *w: any(x in q for x in w)
    if has("eligible", "scheme", "అర్హ", "योजना", "पात्र"): ans = "Based on your prototype profile:\n" + "\n".join(f"- {s}: {v}" for s, v in ctx["eligibility"])
    elif has("insurance", "బీమా", "बीमा"): a = [x for x in A if x.service == "Crop Insurance"]; ans = f"Your Crop Insurance application is '{a[0].status}'." if a else "You have not applied for Crop Insurance yet. Open Government Services and click Apply."
    elif has("pending", "why", "status", "స్థితి", "स्थिति"): ans = "\n".join(f"- {s}: {st}" + (f" (remark: {r})" if r else "") for s, st, r in ctx["applications"]) or "You have no applications yet."
    elif has("document", "పత్ర", "दस्तावेज"): ans = "Common documents: Land record, Bank details, Farmer ID (" + u.farmer_id + "). See each service for its exact list."
    elif has("grievance", "complaint", "ఫిర్యాదు", "शिकायत"): ans = "Open Grievance Redressal, choose a category, describe the issue and submit. It is auto-routed to the right department and you get a GRV ID to track."
    else: ans = "I can help with scheme eligibility, application status, documents and grievances. Try: 'Which schemes am I eligible for?'"
    return {"mode": "demo", "answer": ans + "\n\n(Demo mode: answers come from this prototype's simulated data, not live government systems.)"}

def seed():
    Base.metadata.create_all(engine); db = Session()
    if db.query(User).count(): return
    P = "Demo@123"
    for i, (n, ag, g, v, d, st, l, s, c) in enumerate([("Ravi Kumar", 42, "Male", "Denduluru", "Eluru", "Andhra Pradesh", 3, "Alluvial", "Paddy"), ("Lakshmi Devi", 38, "Female", "Guntur Rural", "Guntur", "Andhra Pradesh", 5, "Black", "Chilli"),
                                                        ("Srinivas Reddy", 47, "Male", "Warangal Rural", "Warangal", "Telangana", 4, "Black", "Cotton")]):
        db.add(User(name=n, age=ag, gender=g, village=v, district=d, state=st, land=l, soil=s, crop=c, mobile=f"900000000{i + 1}", pw=hpw(P), farmer_id=f"AGN-10000{i + 1}"))
    db.add(User(name="Suresh (Village Head)", role="village_head", age=52, gender="Male", village="Denduluru", district="Eluru", state="Andhra Pradesh", land=1, soil="-", crop="-", mobile="9000000004", pw=hpw(P), farmer_id="AGN-VH0001"))
    db.add(User(name="Officer Anitha", role="official", age=40, gender="Female", village="-", district="Eluru", state="Andhra Pradesh", land=1, soil="-", crop="-", mobile="9000000005", pw=hpw(P), farmer_id=None))
    db.add(User(name="System Admin", role="admin", age=35, gender="Male", village="-", district="-", state="-", land=1, soil="-", crop="-", mobile="9000000006", pw=hpw(P), farmer_id=None))
    AP, ALL = "Andhra Pradesh,Telangana", "Andhra Pradesh,Telangana"
    for r in [("Farmer Welfare Scheme", "Welfare", "Income support for small and marginal farmers", "Land record,Bank details,Farmer ID", "Rs 6,000 per year (demo)", AP, "*", 0.5, 5, 18),
              ("Crop Insurance", "Insurance", "Insurance cover against crop loss", "Land record,Bank details,Sowing declaration", "Sum insured up to Rs 40,000/acre (demo)", ALL, "paddy,chilli,cotton,groundnut", 0.5, 50, 18),
              ("Soil Health Service", "Agriculture", "Free soil testing and nutrient advice", "Farmer ID,Land record", "Soil health card", ALL, "*", 0.1, 100, 18),
              ("Agricultural Subsidy", "Agriculture", "Input subsidy for seeds and micro-irrigation", "Land record,Bank details,Farmer ID", "Up to 50% subsidy (demo)", "Andhra Pradesh", "paddy,chilli,groundnut", 1, 4, 18),
              ("Land Record Verification", "Revenue", "Digital verification of land ownership", "Pattadar passbook,Farmer ID", "Verified land certificate", ALL, "*", 0.1, 500, 18),
              ("Irrigation Support", "Water Resources", "Canal water allocation and pump-set support", "Land record,Farmer ID", "Priority water allocation", ALL, "paddy,cotton,chilli", 1, 10, 18)]:
        db.add(Scheme(name=r[0], dept=r[1], desc=r[2], docs=r[3], benefits=r[4], states=r[5], crops=r[6], min_land=r[7], max_land=r[8], min_age=r[9]))
    db.commit()
    new_app(db, "AGN-100001", "Crop Insurance", "Under Review", 5); new_app(db, "AGN-100001", "Land Record Verification", "Approved", 9); new_app(db, "AGN-100001", "Agricultural Subsidy", "Action Required", 3)
    new_app(db, "AGN-100002", "Farmer Welfare Scheme", "Department Received", 2); new_app(db, "AGN-100003", "Irrigation Support", "Under Review", 4)
    for i, (f, c, d, s) in enumerate([("AGN-100001", "Irrigation", "Canal water not reaching our fields for two weeks.", "Action Initiated"), ("AGN-100002", "Land / Revenue", "Survey number mismatch in the land record.", "Assigned"), ("AGN-100001", "Roads", "Approach road to fields damaged by rains.", "Resolved")]):
        db.add(Grievance(gid=f"GRV-{1024 + i}", farmer_id=f, category=c, description=d, village="Denduluru" if f.endswith("1") else "Guntur Rural", priority="High", dept=ROUTE[c], status=s, created=now() - dt.timedelta(days=10 if i == 2 else 2)))
    db.add(Notification(farmer_id="AGN-100001", text="Your Crop Insurance application moved to Under Review.")); db.add(Notification(farmer_id="AGN-100001", text="Grievance GRV-1024: Action has been initiated.")); db.commit(); db.close()
seed()
