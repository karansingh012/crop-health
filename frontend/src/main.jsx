import React, { useState, useEffect, createContext, useContext } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Link, NavLink, Navigate, Outlet, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Sprout, LayoutDashboard, ScanLine, Map, History, FileText, CalendarDays, CloudSun, MessagesSquare, Settings, ArrowUpRight, ArrowRight, Plus, Leaf, LogOut, Sun, Moon, Menu, X, HelpCircle, Download, Check, Upload, ShieldCheck } from 'lucide-react';
import { api, downloadReport } from './api';
import './styles.css';
import { t, useLanguage, LanguageSwitch, translateClass } from './i18n';
const Auth = createContext();
const Notice = createContext();
const nice = s => translateClass(s);
const date = s => new Date(s).toLocaleDateString(localStorage.getItem('canopy-language') === 'hi' ? 'hi-IN' : 'en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric'
});
function App() {
  useLanguage();
  const [user, setUser] = useState(null),
    [ready, setReady] = useState(false),
    [toast, setToast] = useState('');
  useEffect(() => {
    api('/me').then(setUser).catch(() => {}).finally(() => setReady(true));
    const expire = () => setUser(null);
    window.addEventListener('session-expired', expire);
    return () => window.removeEventListener('session-expired', expire);
  }, []);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(''), 5000);
      return () => clearTimeout(t);
    }
  }, [toast]);
  return <Auth.Provider value={{
    user,
    setUser,
    ready
  }}><Notice.Provider value={setToast}><BrowserRouter><Routes><Route path="/" element={<Landing />} /><Route path="/login" element={<AuthPage />} /><Route path="/register" element={<AuthPage register />} /><Route element={<Protected />}><Route path="/app" element={<Dashboard />} /><Route path="/app/scan" element={<Scanner />} /><Route path="/app/scans/:id" element={<Result />} /><Route path="/app/fields" element={<Fields />} /><Route path="/app/history" element={<HistoryPage />} /><Route path="/app/reports" element={<HistoryPage reports />} /><Route path="/app/followups" element={<Followups />} /><Route path="/app/weather" element={<Weather />} /><Route path="/app/experts" element={<Experts />} /><Route path="/app/settings" element={<SettingsPage />} /><Route path="/app/help" element={<Help />} /></Route><Route path="*" element={<main><h1>{t("Page not found")}</h1><Link to="/">{t("Return home")}</Link></main>} /></Routes></BrowserRouter>{toast && <div className="toast" role="status">{t(toast)}</div>}</Notice.Provider></Auth.Provider>;
}
function Brand() {
  return <span className="brand"><span className="brand-icon"><Sprout size={22} /></span>canopy<span className="brand-dot">.</span></span>;
}
function Landing() {
  return <div className="landing"><header><Brand /><nav><LanguageSwitch /><Link to="/login">{t("Sign in")}</Link><Link className="button" to="/register">{t("Get started")} <ArrowUpRight size={17} /></Link></nav></header><section className="landing-hero"><div><span className="eyebrow">{t("A CLEARER PICTURE OF CROP HEALTH")}</span><h1>{t("Small observations.")}<br /><em>{t("Healthier fields.")}</em></h1><p>{t("Keep your field observations together. Explore possible disease matches, understand uncertainty, and make your next conversation with an expert more informed.")}</p><Link className="button" to="/register">{t("Start your field journal")} <ArrowRight size={18} /></Link><div className="trust"><ShieldCheck size={17} /> {t("Private records. Honest results. Expert-led decisions.")}</div></div><div className="botanical" aria-hidden="true"><div className="sun-disc" /><svg viewBox="0 0 400 450"><path d="M200 430Q160 280 230 60" fill="none" stroke="#315c3c" strokeWidth="9" />{[[198, 350, -55], [200, 260, 45], [209, 190, -55], [220, 120, 40]].map(([x, y, r], i) => <ellipse key={i} cx={x} cy={y} rx="48" ry="100" transform={`rotate(${r} ${x} ${y})`} fill={i % 2 ? '#457453' : '#73945d'} />)}</svg><div className="botanical-caption">{t("Observe. Understand. Follow through.")}</div></div></section><div className="landing-features">{[[ScanLine, t("Observe with care"), t("Save leaf images with field notes and model assessments when trained weights are available.")], [CalendarDays, t("Build a clearer history"), t("Return to your observations and schedule a follow-up at the right time.")], [MessagesSquare, t("Bring context to an expert"), t("Download a private report to support a better-informed consultation.")]].map(([Icon, title, copy]) => <article key={title}><Icon /><h3>{title}</h3><p>{copy}</p></article>)}</div><footer>{t("Canopy \xB7 A crop health research application")} <span>{t("Decision support, not a confirmed diagnosis.")}</span></footer></div>;
}
function AuthPage({
  register = false
}) {
  const {
      setUser
    } = useContext(Auth),
    nav = useNavigate(),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const session = await api(`/auth/${register ? 'register' : 'login'}`, {
        method: 'POST',
        body: data
      });
      sessionStorage.setItem('canopy-token', session.access_token);
      setUser(await api('/me'));
      nav('/app');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return <div className="auth"><div className="auth-story"><Link to="/"><Brand /></Link><h1>{t("Your field.")}<br />{t("Its story.")}<br /><em>{t("All in one place.")}</em></h1><p>{t("A thoughtful workspace for observing crop health.")}</p><Sprout size={180} strokeWidth={.6} /></div><div className="auth-form"><LanguageSwitch /><span className="eyebrow">{t("WELCOME TO CANOPY")}</span><h1>{register ? t("Start growing your records.") : t("Good to see you again.")}</h1><p>{register ? t("Create your private crop health workspace.") : t("Sign in to pick up where you left off.")}</p><form onSubmit={submit}>{register && <label>{t("Your name")}<input name="name" required maxLength={100} autoComplete="name" /></label>}<label>{t("Email address")}<input name="email" type="email" required autoComplete="email" /></label><label>{t("Password")}<input name="password" type="password" required minLength={12} maxLength={128} autoComplete={register ? 'new-password' : 'current-password'} /></label><small>{t("Use at least 12 characters.")}</small><ErrorBox text={error} /><button disabled={busy}>{busy ? t("Please wait\u2026") : register ? t("Create account") : t("Sign in")}<ArrowRight size={18} /></button></form><p>{register ? t("Already have an account?") : t("New to Canopy?")} <Link to={register ? '/login' : '/register'}>{register ? t("Sign in") : t("Create an account")}</Link></p></div></div>;
}
const navigation = [['/app', 'Overview', LayoutDashboard], ['/app/scan', 'Plant scanner', ScanLine], ['/app/fields', 'My fields', Map], ['/app/history', 'Scan history', History], ['/app/reports', 'Reports', FileText], ['/app/followups', 'Follow-ups', CalendarDays], ['/app/weather', 'Weather & context', CloudSun], ['/app/experts', 'Expert support', MessagesSquare]];
function Protected() {
  const {
      user,
      ready,
      setUser
    } = useContext(Auth),
    [open, setOpen] = useState(false),
    [dark, setDark] = useState(localStorage.getItem('canopy-theme') === 'dark'),
    notify = useContext(Notice);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    localStorage.setItem('canopy-theme', dark ? 'dark' : 'light');
  }, [dark]);
  if (!ready) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  async function logout() {
    try {
      await api('/auth/logout', {
        method: 'POST'
      });
      sessionStorage.removeItem('canopy-token');
      setUser(null);
    } catch (e) {
      notify(e.message);
    }
  }
  return <div className="shell"><aside className={open ? 'sidebar open' : 'sidebar'}><Link to="/app" onClick={() => setOpen(false)}><Brand /></Link><div className="workspace-label">{t("YOUR WORKSPACE")}</div><nav>{navigation.map(([to, title, Icon]) => <NavLink key={to} to={to} end={to === '/app'} onClick={() => setOpen(false)}><Icon size={19} />{t(title)}</NavLink>)}</nav><div className="sidebar-bottom"><NavLink to="/app/help"><HelpCircle size={18} />{t("Help & about")}</NavLink><NavLink to="/app/settings"><Settings size={18} />{t("Settings")}</NavLink><div className="account"><span className="avatar">{user.name.slice(0, 1).toUpperCase()}</span><div><strong>{user.name}</strong><small>{t("Personal workspace")}</small></div><button className="icon-btn" aria-label={t("Sign out")} onClick={logout}><LogOut size={18} /></button></div></div></aside><div className="workspace"><header className="topbar"><button className="icon-btn mobile-menu" aria-label={t("Toggle navigation")} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button><span>{t("Workspace")} <span className="muted">{t("/ Crop health")}</span></span><div><LanguageSwitch /><span className="today">{date(new Date())}</span><button className="icon-btn" aria-label={t("Toggle color theme")} onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button></div></header><main><Outlet /></main><footer className="app-footer">{t("Made for careful observation.")}<span>{t("Always confirm with a qualified agricultural expert.")}</span></footer></div></div>;
}
function ErrorBox({
  text
}) {
  return text ? <div role="alert" className="error">{t(text)}</div> : null;
}
function Loading() {
  return <div className="loading" role="status"><div className="skeleton" /><div className="skeleton" />{t("Loading your workspace\u2026")}</div>;
}
function useLoad(path) {
  const [data, setData] = useState(null),
    [error, setError] = useState(''),
    [version, setVersion] = useState(0);
  useEffect(() => {
    let live = true;
    setError('');
    api(path).then(x => live && setData(x)).catch(e => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [path, version]);
  return {
    data,
    error,
    reload: () => setVersion(v => v + 1)
  };
}
function Title({
  eyebrow = t("YOUR WORKSPACE"),
  title,
  subtitle,
  action
}) {
  return <div className="page-title"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>;
}
function Empty({
  title,
  copy,
  to,
  label,
  Icon = Leaf
}) {
  return <div className="empty"><span><Icon size={28} /></span><h3>{title}</h3><p>{copy}</p>{to && <Link className="button secondary" to={to}>{label}<ArrowRight size={16} /></Link>}</div>;
}
function Status({
  value
}) {
  return <span className={`status ${value === "classified" ? 'green' : ''}`}>{nice(value)}</span>;
}
function Dashboard() {
  const {
      user
    } = useContext(Auth),
    fields = useLoad('/fields'),
    scans = useLoad('/scans'),
    followups = useLoad('/followups'),
    health = useLoad('/health');
  return <><Title eyebrow={t("LET'S KEEP AN EYE ON THINGS")} title={t('Welcome back, {name}.', {
      name: user.name.split(' ')[0]
    })} subtitle={t("A little attention today. A clearer picture tomorrow.")} action={<Link className="button" to="/app/scan"><Plus size={18} />{t("New observation")}</Link>} /><section className="overview-hero"><div><span className="pill">{t("YOUR NEXT STEP")}</span><h2>{t("Every leaf has")}<br />{t("something to tell you.")}</h2><p>{t("Capture a clear photo, add your observations,")}<br className="desktop" /> {t("and keep your crop's story moving forward.")}</p><Link className="button cream" to="/app/scan">{t("Open plant scanner")} <ArrowUpRight size={18} /></Link></div><div className="hero-leaf" aria-hidden="true"><Leaf size={190} strokeWidth={.7} /></div></section><ErrorBox text={fields.error || scans.error || followups.error} /><div className="stats">{[[Map, t("Fields in your care"), fields.data?.length], [ScanLine, t("Recent observations"), scans.data?.length], [CalendarDays, t("Open follow-ups"), followups.data?.filter(x => !x.done).length]].map(([Icon, label, count]) => <article className="card stat" key={label}><div><span>{label}</span><Icon size={20} /></div><strong>{count ?? '—'}</strong><small>{label === t("Recent observations") ? t("Latest 100 records") : t("In your workspace")}</small></article>)}</div><div className="dashboard-grid"><section className="card"><div className="section-title"><h2>{t("Recent observations")}</h2><Link to="/app/history">{t("View all")} <ArrowUpRight size={15} /></Link></div>{scans.data?.length ? <ScanList scans={scans.data.slice(0, 4)} /> : <Empty title={t("A fresh start for your fields")} copy={t("Your observations will appear here after you upload your first plant image.")} to="/app/scan" label={t("Make an observation")} />}</section><section className="card"><div className="section-title"><h2>{t("Field notes")}</h2><Sprout size={20} /></div><div className="tip"><span className="eyebrow">{t("A BETTER PHOTO")}</span><h3>{t("Good light. Clear detail.")}</h3><p>{t("Choose natural light and a simple background. Include the whole leaf, then record any changes you've noticed.")}</p></div><div className="model-note"><span className="dot" /><div><strong>{health.data?.model === 'configured' ? t("Model checkpoint configured") : t("Research model not installed")}</strong><p>{health.data?.model === 'configured' ? t("Assessments are suggestions, not diagnoses.") : t("You can save observations now. Disease predictions require a trained checkpoint.")}</p></div></div></section></div></>;
}
function ScanList({
  scans,
  reports = false
}) {
  const notify = useContext(Notice);
  return <div className="scan-list">{scans.map(scan => <div className="scan-row" key={scan.id}><span className="scan-icon"><Leaf size={20} /></span><div><Link to={`/app/scans/${scan.id}`}><strong>{nice(scan.prediction.label) || t("Observation")}</strong></Link><small>{t("Observation #")}{scan.id} · {date(scan.created_at)}</small></div><Status value={scan.prediction.status} />{reports ? <button className="icon-btn" aria-label={t('Download report {id}',{id:scan.id})} onClick={() => downloadReport(scan.id).catch(e => notify(e.message))}><Download size={19} /></button> : <Link aria-label={t('View observation {id}',{id:scan.id})} to={`/app/scans/${scan.id}`}><ArrowUpRight size={19} /></Link>}</div>)}</div>;
}
function Scanner() {
  const fields = useLoad('/fields'),
    nav = useNavigate(),
    [file, setFile] = useState(null),
    [preview, setPreview] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  async function submit(e) {
    e.preventDefault();
    if (!file) {
      setError(t("Choose a leaf image first."));
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError(t("Choose an image smaller than 8 MB."));
      return;
    }
    setBusy(true);
    setError('');
    const form = new FormData(e.currentTarget);
    if (!form.get('field_id')) form.delete('field_id');
    try {
      const scan = await api('/scans', {
        method: 'POST',
        body: form
      });
      nav(`/app/scans/${scan.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return <><Title eyebrow={t("OBSERVE WITH CARE")} title={t("Plant scanner")} subtitle={t("A clear image is the first step toward a useful observation.")} /><div className="two-column"><form className="card padded" onSubmit={submit}><label className="upload-zone">{preview ? <img src={preview} alt={t("Selected plant image")} /> : <><span className="upload-icon"><ScanLine size={34} /></span><h2>{t("A closer look at your crop")}</h2><p>{t("Choose a leaf photo to get started")}</p><span className="button secondary">{t("Browse images")} <Upload size={16} /></span></>}<input aria-label={t("Plant image")} name="file" type="file" accept="image/jpeg,image/png,image/webp" required onChange={e => setFile(e.target.files[0])} /><small>{t("JPEG, PNG or WebP \xB7 Up to 8 MB")}</small></label><label>{t("Field (optional)")}<select name="field_id"><option value="">{t("Unassigned observation")}</option>{fields.data?.map(f => <option value={f.id} key={f.id}>{f.name} · {f.crop}</option>)}</select></label><label>{t("What have you noticed?")}<textarea name="notes" maxLength={2000} placeholder={t("For example: yellow spots on older leaves, first noticed two days ago\u2026")} /></label><ErrorBox text={error || fields.error} /><button disabled={busy}>{busy ? t("Saving and assessing\u2026") : t("Save & assess image")}<ArrowRight size={18} /></button></form><aside><section className="card padded"><span className="eyebrow">{t("BEFORE YOU CAPTURE")}</span><h2>{t("Give the details room.")}</h2><ol className="capture-tips"><li>{t("Use even, natural light.")}</li><li>{t("Keep the leaf in focus and fill the frame.")}</li><li>{t("Include notes about the plant and surrounding conditions.")}</li></ol></section><div className="notice"><ShieldCheck /><p>{t("Predictions are possible class matches. Without trained weights, Canopy saves your image and notes without generating a disease result.")}</p></div></aside></div></>;
}
function PrivateImage({
  id
}) {
  const [url, setUrl] = useState('');
  useEffect(() => {
    let active = true,
      object;
    api(`/scans/${id}/image`, {
      blob: true
    }).then(blob => {
      object = URL.createObjectURL(blob);
      if (active) setUrl(object);
    }).catch(() => {});
    return () => {
      active = false;
      if (object) URL.revokeObjectURL(object);
    };
  }, [id]);
  return url ? <img className="result-image" src={url} alt={t('Plant observation {id}',{id:id})} /> : <div className="image-placeholder">{t("Image unavailable or loading")}</div>;
}
function Result() {
  const modelHealth=useLoad('/health');
  const nav = useNavigate();
  const {
      id
    } = useParams(),
    {
      data: scan,
      error
    } = useLoad(`/scans/${id}`),
    notify = useContext(Notice),
    [due, setDue] = useState(''),
    [busy, setBusy] = useState(false);
  if (error) return <ErrorBox text={error} />;
  if (!scan) return <Loading />;
  const p = scan.prediction;
  async function follow(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api('/followups', {
        method: 'POST',
        body: {
          scan_id: scan.id,
          ...(due ? {
            due_at: new Date(due).toISOString()
          } : {})
        }
      });
      notify(t("Follow-up scheduled"));
    } catch (e) {
      notify(e.message);
    } finally {
      setBusy(false);
    }
  }
  return <><Title eyebrow={`${t('Observation #')}${id} · ${date(scan.created_at)}`} title={t("Your crop observation")} subtitle={t("A record to return to, and a starting point for expert advice.")} action={<button className="secondary" onClick={() => downloadReport(id).catch(e => notify(e.message))}><Download size={18} />{t("Download report")}</button>} /><div className="two-column"><section className="card padded"><PrivateImage id={id} /><h3>{t("Field notes")}</h3><p>{scan.notes || t("No notes recorded.")}</p><Link to={scan.field_id ? `/app/history?field=${scan.field_id}` : '/app/history'}>{t("Compare field observations")} <ArrowUpRight size={15} /></Link></section><div><section className="card padded"><Status value={p.status} /><h2>{nice(p.label)}</h2>{p.score != null && <div className="score"><strong>{(p.score * 100).toFixed(1)}%</strong><span>{t("Model score \xB7 uncalibrated")}</span></div>}<p>{p.status==='model_unavailable'&&modelHealth.data?.model==='configured'?t('This record predates model setup. Assess this image again to create a new result.'):t(p.message)}</p>{p.research_note&&<div className="notice">{t(p.research_note)}</div>}<button className="secondary" disabled={busy} onClick={async () => {
            setBusy(true);
            try {
              const next = await api(`/scans/${id}/reanalyze`, {
                method: 'POST'
              });
              nav(`/app/scans/${next.id}`);
              notify(t('Image reassessed'));
            } catch (e) {
              notify(e.message);
            } finally {
              setBusy(false);
            }
          }}>{t('Assess this image again')}</button>{p.quality?.map(x => <div className="notice" key={x}>{t(x)}</div>)}{p.score_interpretation && <small>{t(p.score_interpretation)}</small>}<hr /><h3>{t("Guidance")}</h3><p>{t(p.guidance?.symptoms)}</p><p>{t(p.guidance?.care)}</p>{p.guidance?.source && <a href={p.guidance.source} target="_blank" rel="noreferrer">{t("Agricultural reference \u2197")}</a>}{p.guidance?.warnings.map(x => <p className="muted" key={x}>{t(x)}</p>)}{p.ood_warning && <p>{t(p.ood_warning)}</p>}<Link className="button secondary" to="/app/experts">{t("Explore expert support")} <ArrowUpRight size={16} /></Link></section><form className="card padded followup-form" onSubmit={follow}><h3>{t("Check back in")}</h3><label>{t("Follow-up date (leave empty for 7 days)")}<input type="datetime-local" value={due} onChange={e => setDue(e.target.value)} /></label><button disabled={busy}>{t("Schedule follow-up")} <CalendarDays size={16} /></button></form></div></div></>;
}
function Fields() {
  const {
      data,
      error,
      reload
    } = useLoad('/fields'),
    [editing, setEditing] = useState(null),
    [show, setShow] = useState(false),
    [busy, setBusy] = useState(false),
    [formError, setFormError] = useState(''),
    notify = useContext(Notice);
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setFormError('');
    const body = Object.fromEntries(new FormData(e.currentTarget));
    body.area = Number(body.area);
    try {
      await api(editing ? `/fields/${editing.id}` : '/fields', {
        method: editing ? 'PATCH' : 'POST',
        body
      });
      setShow(false);
      setEditing(null);
      reload();
      notify(t("Field saved"));
    } catch (e) {
      setFormError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function remove(f) {
    if (!window.confirm(t('Delete {name}? Its observations will be kept as unassigned records.', {
      name: f.name
    }))) return;
    try {
      await api(`/fields/${f.id}`, {
        method: 'DELETE'
      });
      reload();
      notify(t("Field deleted"));
    } catch (e) {
      notify(e.message);
    }
  }
  return <><Title title={t("My fields")} subtitle={t("A place for every crop and the observations that matter.")} action={<button onClick={() => {
      setEditing(null);
      setShow(true);
    }}><Plus size={18} />{t("Add field")}</button>} /><ErrorBox text={error} />{show && <form className="card padded field-form" key={editing?.id || 'new'} onSubmit={save}><div className="section-title"><h2>{editing ? t("Edit field") : t("Add a field")}</h2><button type="button" className="icon-btn" aria-label={t("Close field form")} onClick={() => setShow(false)}><X /></button></div><div className="form-grid"><label>{t("Field name")}<input name="name" defaultValue={editing?.name} required maxLength={100} /></label><label>{t("Crop")}<input name="crop" defaultValue={editing?.crop} required maxLength={100} /></label><label>{t("Area (hectares)")}<input name="area" type="number" min="0.001" max="10000000" step="any" defaultValue={editing?.area} required /></label><label>{t("Location (optional)")}<input name="location" defaultValue={editing?.location} maxLength={200} /></label></div><ErrorBox text={formError} /><button disabled={busy}>{busy ? t("Saving\u2026") : t("Save field")}</button></form>}{!data ? <Loading /> : data.length ? <div className="field-grid">{data.map(f => <article className="card field-card" key={f.id}><div className="field-art"><Sprout size={46} strokeWidth={1} /><span>{f.crop}</span></div><div className="padded"><h2>{f.name}</h2><p>{f.area} {t("ha \xB7")} {f.location || t("Location not set")}</p><Link to={`/app/history?field=${f.id}`}>{t("View observations")} <ArrowUpRight size={16} /></Link><div className="field-actions"><button className="secondary" onClick={() => {
              setEditing(f);
              setShow(true);
            }}>{t("Edit")}</button><button className="text-btn" onClick={() => remove(f)}>{t("Delete")}</button></div></div></article>)}</div> : <section className="card"><Empty Icon={Map} title={t("Room to grow")} copy={t("Add your first field using the button above. Give it a name, crop and approximate area.")} /></section>}</>;
}
function HistoryPage({
  reports = false
}) {
  const [params] = useSearchParams(),
    [offset, setOffset] = useState(0);
  const {
    data,
    error
  } = useLoad(`/scans?limit=100&offset=${offset}${params.get('field') ? `&field_id=${params.get('field')}` : ''}`);
  const [compare, setCompare] = useState([]);
  return <><Title title={reports ? t("Reports") : t("Scan history")} subtitle={reports ? t("Private, downloadable records of your crop observations.") : t("Look back at your observations and compare what you recorded.")} /><ErrorBox text={error} />{!data ? <Loading /> : data.length ? <section className="card"><ScanList scans={data} reports={reports} /></section> : <section className="card"><Empty title={t("No observations here yet")} copy={t("Save a plant image and your notes to start your field history.")} to="/app/scan" label={t("Make an observation")} /></section>}<div className="pagination"><button className="secondary" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 100))}>{t("Previous")}</button><span>{t("Page")} {offset / 100 + 1}</span><button className="secondary" disabled={!data || data.length < 100} onClick={() => setOffset(offset + 100)}>{t("Next")}</button></div>{!reports && data?.length > 1 && <section className="card padded"><h2>{t("Compare two observations")}</h2><p>{t("Choose records from the same field. Changes in class or score alone do not establish progression or recovery.")}</p><div className="form-grid">{[0, 1].map(i => <label key={i}>{i === 0 ? t("Earlier observation") : t("Later observation")}<select value={compare[i] || ''} onChange={e => setCompare(v => {
            const next = [...v];
            next[i] = e.target.value;
            return next;
          })}><option value="">{t("Choose an observation")}</option>{data.map(s => <option key={s.id} value={s.id}>#{s.id} · {date(s.created_at)} {t("\xB7 Field")} {s.field_id || t("unassigned")}</option>)}</select></label>)}</div>{compare[0] && compare[1] && <div className="form-grid">{compare.map((id, i) => {
          const s = data.find(x => String(x.id) === id);
          return s && <article key={i}><PrivateImage id={id} /><h3>{nice(s.prediction.label)}</h3><p>{s.notes || t("No notes")}</p><Status value={s.prediction.status} /></article>;
        })}</div>}</section>}</>;
}
function Followups() {
  const {
      data,
      error,
      reload
    } = useLoad('/followups'),
    notify = useContext(Notice);
  async function change(id, options) {
    try {
      await api(`/followups/${id}`, options);
      reload();
      notify(t("Follow-up updated"));
    } catch (e) {
      notify(e.message);
    }
  }
  return <><Title title={t("Follow-up monitoring")} subtitle={t("Small check-ins, connected to the original observation.")} /><ErrorBox text={error} />{!data ? <Loading /> : data.length ? <section className="card">{data.map(f => <div className="scan-row" key={f.id}><CalendarDays size={22} /><div><Link to={`/app/scans/${f.scan_id}`}><strong>{t("Observation #")}{f.scan_id}</strong></Link><small>{t('Due')} {date(f.due_at)}{!f.done && new Date(f.due_at) < new Date() ? t(" \xB7 Overdue") : ''}</small></div><button className="secondary" onClick={() => change(f.id, {
          method: 'PATCH',
          body: {
            done: !f.done
          }
        })}>{f.done ? <><Check size={16} />{t("Completed")}</> : t("Mark complete")}</button><button className="icon-btn" aria-label={t('Delete follow-up {id}',{id:f.id})} onClick={() => change(f.id, {
          method: 'DELETE'
        })}><X size={17} /></button></div>)}</section> : <section className="card"><Empty Icon={CalendarDays} title={t("Nothing on the calendar yet")} copy={t("Open an observation to schedule a follow-up. Reminders appear here when you return to Canopy.")} to="/app/history" label={t("Browse observations")} /></section>}<div className="notice">{t("Follow-ups are in-app records. Email and push notifications are not enabled.")}</div></>;
}
function Weather() {
  const lang = useLanguage(),
    [data, setData] = useState(null),
    [places, setPlaces] = useState(null),
    [selected, setSelected] = useState(null),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  async function search(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setPlaces(null);
    setData(null);
    setSelected(null);
    try {
      const query = new FormData(e.currentTarget).get('place');
      setPlaces(await api(`/locations?q=${encodeURIComponent(query)}&language=${lang}`));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function fetchWeather(place) {
    setBusy(true);
    setError('');
    setData(null);
    setSelected(place);
    try {
      setData(await api(`/weather?latitude=${place.latitude}&longitude=${place.longitude}`));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function locate() {
    setError('');
    if (!navigator.geolocation) {
      setError(t("Your browser cannot share location. Search for a city or village instead."));
      return;
    }
    setBusy(true);
    navigator.geolocation.getCurrentPosition(position => fetchWeather({
      name: t('Your current location'),
      latitude: position.coords.latitude,
      longitude: position.coords.longitude
    }), () => {
      setBusy(false);
      setError(t("Location permission was denied or unavailable. Search for a city or village instead."));
    }, {
      enableHighAccuracy: false,
      timeout: 12000,
      maximumAge: 300000
    });
  }
  return <><Title title={t("Weather & crop context")} subtitle={t("Search by city or village, or use your device location.")} /><form className="card padded" onSubmit={search}><label>{t("City, village or postal code")}<input name="place" minLength={2} maxLength={120} required placeholder={t("For example: Lucknow or \u0932\u0916\u0928\u090A")} /></label><div className="weather-actions"><button disabled={busy}>{busy ? t("Please wait\u2026") : t("Search places")}<CloudSun size={18} /></button><button className="secondary" type="button" disabled={busy} onClick={locate}>{t("Use my location")}</button></div><small>{t("Your location is requested only when you choose this option.")}</small><ErrorBox text={error} /></form>{places && <section className="card padded place-results"><h2>{t("Choose your location")}</h2>{places.length ? places.map(place => <button type="button" className="secondary place-choice" key={place.id} disabled={busy} onClick={() => fetchWeather(place)}><strong>{place.name}</strong><span>{[place.region, place.country].filter(Boolean).join(', ')}</span><ArrowRight size={17} /></button>) : <p>{t("No places found. Try a nearby city, district or postal code.")}</p>}</section>}{busy && <Loading />}{data && <><h2 className="weather-location">{selected?.name}{selected?.region ? ` · ${selected.region}` : ''}</h2><div className="stats">{[[t("Temperature"), 'temperature_2m'], [t("Relative humidity"), 'relative_humidity_2m'], [t("Precipitation"), 'precipitation']].map(([label, key]) => <article className="card stat" key={key}><span>{label}</span><strong>{data.current[key]}<small>{data.units[key]}</small></strong></article>)}</div><section className="card padded"><h2>{t("Conditions in context")}</h2>{data.context.map(x => <p key={x}>{t(x)}</p>)}<small>{t('Model estimate at')} {new Date(data.current.time + 'Z').toLocaleString(lang === 'hi' ? 'hi-IN' : 'en-IN')} · <a href={data.source_url} target="_blank" rel="noreferrer">{data.source}</a></small></section></>}<div className="notice">{t("Weather observations alone cannot establish infection. Local leaf wetness, crop variety and field conditions also matter.")}</div></>;
}
function Experts() {
  const {
    data,
    error
  } = useLoad('/experts');
  return <><Title title={t("Expert support")} subtitle={t("Bring your observations to someone who knows your local crops.")} /><ErrorBox text={error} /><section className="card padded"><MessagesSquare size={36} /><h2>{data?.configured ? data.name : t("Connect with local expertise")}</h2><p>{data?.configured ? t("Download an observation report, review its contents, and attach it to your email.") : t("No expert contact has been configured for this installation. Ask your local agricultural extension service or a qualified crop specialist for support.")}</p>{data?.configured && <a className="button" href={`mailto:${encodeURIComponent(data.email)}?subject=Crop%20health%20consultation`}>{t("Compose email")} <ArrowUpRight size={18} /></a>}<Link className="button secondary" to="/app/reports">{t("Choose a report")} <FileText size={18} /></Link><p className="muted">{t("Sharing is your choice. Canopy does not send reports automatically.")}</p></section></>;
}
function SettingsPage() {
  const {
      user,
      setUser
    } = useContext(Auth),
    notify = useContext(Notice),
    [busy, setBusy] = useState(false);
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    try {
      setUser(await api('/me', {
        method: 'PATCH',
        body: Object.fromEntries(new FormData(e.currentTarget))
      }));
      notify(t("Profile updated"));
    } catch (e) {
      notify(e.message);
    } finally {
      setBusy(false);
    }
  }
  return <><Title title={t("Profile & settings")} subtitle={t("Make this workspace your own.")} /><form className="card padded narrow" onSubmit={save}><label>{t("Display name")}<input name="name" defaultValue={user.name} required maxLength={100} /></label><label>{t("Email address")}<input value={user.email} disabled /></label><p>{t("Change the color theme using the sun or moon button in the top bar.")}</p><button disabled={busy}>{t("Save changes")}</button></form></>;
}
function Help() {
  return <><Title title={t("Help & about")} subtitle={t("Understand what Canopy can tell you, and what it cannot.")} /><section className="card padded narrow">{[[t("How do I start?"), t("Add a field, then upload a clear plant image in Plant scanner. You can save images and notes even when a trained model is unavailable.")], [t("What does the model score mean?"), t("It is an uncalibrated softmax score. It is not the probability that a plant has a disease. Predictions remain uncertain until a validation-based threshold is available.")], [t("Is this a diagnosis?"), t("No. Similar diseases, poor image quality and unsupported crops can all lead to errors. Consult an agricultural expert, especially when symptoms are severe.")], [t("Where are my records?"), t("Fields, observations and follow-ups belong to your signed-in account. Reports and images require authentication.")], [t("Research behind the application"), t("The project compares CNN, ViT and fused CNN\u2013ViT models. PlantVillage training and compatible PlantDoc evaluation must be run before making performance claims.")], [t("How do reminders work?"), t("Schedule one from an observation page. It appears under Follow-ups. This version does not send email or push notifications.")]].map(([title, text]) => <article key={title}><h3>{title}</h3><p>{text}</p></article>)}</section></>;
}
createRoot(document.getElementById('root')).render(<App />);
