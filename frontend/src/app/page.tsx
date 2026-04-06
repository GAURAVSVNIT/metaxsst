'use client';

import React, { useState, useEffect } from 'react';
import {
  Shield, FileText, Search, Activity, Flag, AlertCircle,
  X, Play, RefreshCw, BarChart3, Binary, Layers, Zap,
  BookOpen, Send, ChevronRight, Bookmark, Eye
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import { resetEnv, stepEnv, fetchTasks, Observation } from '@/lib/api';

// ─── tiny utility ─────────────────────────────────────────────────────────────
function cn(...c: (string | boolean | undefined | null)[]) {
  return c.filter(Boolean).join(' ');
}

// ─── severity config ───────────────────────────────────────────────────────────
const SEV: Record<string, { ring: string; text: string; dot: string }> = {
  low:      { ring: 'border-emerald-500/30 bg-emerald-500/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  medium:   { ring: 'border-amber-500/30   bg-amber-500/10',   text: 'text-amber-400',   dot: 'bg-amber-400' },
  high:     { ring: 'border-orange-500/30  bg-orange-500/10',  text: 'text-orange-400',  dot: 'bg-orange-400' },
  critical: { ring: 'border-red-500/30     bg-red-500/10',     text: 'text-red-400',     dot: 'bg-red-500 animate-pulse' },
};

function Sev({ s }: { s: string }) {
  const c = SEV[s] ?? SEV.medium;
  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border', c.ring, c.text)}>
      <span className={cn('w-1.5 h-1.5 rounded-full', c.dot)} />
      {s}
    </span>
  );
}

// ─── recursive document renderer ──────────────────────────────────────────────
function DocContent({ v, depth = 0 }: { v: any; depth?: number }) {
  if (v === null || v === undefined) return <span className="text-[#404a62] italic text-sm">—</span>;
  if (typeof v === 'boolean') return <span className={v ? 'text-emerald-400 font-semibold' : 'text-red-400 font-semibold'}>{v ? '✓ Yes' : '✗ No'}</span>;
  if (typeof v === 'number') return <span className="text-sky-300 font-mono">{v.toLocaleString()}</span>;
  if (typeof v === 'string') return <span className="text-[#c8d8f0] leading-relaxed">{v}</span>;

  if (Array.isArray(v)) {
    return (
      <div className="mt-2 space-y-2.5">
        {v.map((item, i) => (
          <div key={i} className="p-4 rounded-xl bg-white/[0.025] border border-white/[0.05]">
            <p className="text-[9px] font-black text-[#404a62] uppercase tracking-[0.2em] mb-3">#{i + 1}</p>
            <DocContent v={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  const entries = Object.entries(v);
  return (
    <div className="grid gap-x-6 gap-y-4" style={{ gridTemplateColumns: depth === 0 ? 'repeat(auto-fill, minmax(180px,1fr))' : '1fr' }}>
      {entries.map(([k, val]) => {
        const isComplex = typeof val === 'object' && val !== null;
        return (
          <div key={k} className={cn('flex flex-col gap-1.5', isComplex && 'col-span-full')}>
            <span className="text-[9px] font-black text-[#404a62] uppercase tracking-[0.2em]">{k.replace(/_/g, ' ')}</span>
            {isComplex ? (
              <div className="p-4 rounded-xl bg-white/[0.025] border border-white/[0.04]">
                <DocContent v={val} depth={depth + 1} />
              </div>
            ) : (
              <div className="text-sm font-mono">
                <DocContent v={val} depth={depth + 1} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── stat pill ─────────────────────────────────────────────────────────────────
function Stat({ label, val, dim }: { label: string; val: string; dim?: boolean }) {
  return (
    <div className="flex flex-col items-end gap-0.5">
      <span className="text-[9px] font-black text-[#404a62] uppercase tracking-widest">{label}</span>
      <span className={cn('text-sm font-black tabular-nums', dim ? 'text-[#8899bb]' : 'text-white')}>{val}</span>
    </div>
  );
}

// ─── tab button ────────────────────────────────────────────────────────────────
function Tab({ label, icon, active, onClick, badge }: { label: string; icon: React.ReactNode; active: boolean; onClick: () => void; badge?: number }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'relative flex items-center gap-2 px-6 py-4 text-xs font-bold uppercase tracking-widest transition-colors duration-150',
        active ? 'text-white' : 'text-[#404a62] hover:text-[#8899bb]'
      )}
    >
      {icon}
      {label}
      {badge !== undefined && (
        <span className="ml-1 px-1.5 py-0.5 rounded-md bg-[#111827] text-[#404a62] text-[10px] font-black">{badge}</span>
      )}
      {active && <motion.div layoutId="tab-ul" className="absolute bottom-0 inset-x-0 h-px bg-[#4f8eff]" />}
    </button>
  );
}

// ─── field ─────────────────────────────────────────────────────────────────────
function Field({ label, placeholder, type = 'text', value, textarea, onChange }: {
  label: string; placeholder?: string; type?: string; value?: string; textarea?: boolean; onChange: (v: string) => void;
}) {
  const base = 'w-full bg-[#03040a] border border-white/[0.07] rounded-xl text-sm text-[#c8d8f0] placeholder:text-[#2a3448] focus:border-[#4f8eff]/50 outline-none transition-colors font-mono';
  return (
    <label className="flex flex-col gap-2">
      <span className="text-[10px] font-black text-[#404a62] uppercase tracking-widest">{label}</span>
      {textarea
        ? <textarea onChange={e => onChange(e.target.value)} placeholder={placeholder} className={cn(base, 'px-4 py-3 h-28 resize-none leading-relaxed')} />
        : <input type={type} onChange={e => onChange(e.target.value)} placeholder={placeholder} value={value} className={cn(base, 'px-4 py-3')} />
      }
    </label>
  );
}

// ─── section label ─────────────────────────────────────────────────────────────
function Label({ children }: { children: React.ReactNode }) {
  return <h3 className="text-[10px] font-black text-[#404a62] uppercase tracking-[0.22em] mb-3">{children}</h3>;
}

// ══════════════════════════════════════════════════════════════════════════════
// LANDING PAGE
// ══════════════════════════════════════════════════════════════════════════════
function Landing({ tasks, onStart }: { tasks: Record<string, any>; onStart: (id: string) => void }) {
  const diff: Record<string, { color: string; border: string; glow: string; badge: string }> = {
    easy:   { color: 'text-emerald-400', border: 'hover:border-emerald-500/40', glow: 'hover:shadow-emerald-900/30', badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25' },
    medium: { color: 'text-amber-400',   border: 'hover:border-amber-500/40',   glow: 'hover:shadow-amber-900/30',   badge: 'bg-amber-500/15   text-amber-400   border-amber-500/25' },
    hard:   { color: 'text-red-400',     border: 'hover:border-red-500/40',     glow: 'hover:shadow-red-900/30',     badge: 'bg-red-500/15     text-red-400     border-red-500/25' },
  };

  return (
    <div className="min-h-screen bg-[#03040a] flex flex-col items-center justify-center p-12 relative overflow-hidden">
      {/* Ambient glow backdrop */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-blue-600/[0.04] rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[400px] h-[300px] bg-indigo-600/[0.03] rounded-full blur-3xl" />
      </div>
      {/* Grid lines */}
      <div className="absolute inset-0 opacity-[0.025]" style={{ backgroundImage: 'linear-gradient(#4f8eff 1px,transparent 1px),linear-gradient(to right,#4f8eff 1px,transparent 1px)', backgroundSize: '64px 64px' }} />

      <div className="relative z-10 w-full max-w-4xl">
        {/* Badge */}
        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="flex justify-center mb-10">
          <span className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-[#4f8eff]/10 border border-[#4f8eff]/20 text-[#4f8eff] text-xs font-bold uppercase tracking-[0.22em]">
            <Shield size={12} /> OpenEnv · Simulation Engine v1.0
          </span>
        </motion.div>

        {/* Hero text */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className="text-center text-[64px] font-black leading-none tracking-tighter mb-6"
          style={{ background: 'linear-gradient(135deg, #f0f4ff 0%, #8899bb 60%, #404a62 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
        >
          Identify Fraud.<br />Protect the Public.
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.16 }} className="text-center text-base text-[#8899bb] max-w-xl mx-auto leading-relaxed mb-14">
          Analyze government records, trace shell company structures, and build FCA cases in a deterministic simulation environment.
        </motion.p>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-10">
          <div className="flex-1 h-px bg-white/[0.05]" />
          <span className="text-[10px] font-black text-[#2a3448] uppercase tracking-[0.3em]">Choose Investigation</span>
          <div className="flex-1 h-px bg-white/[0.05]" />
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {Object.entries(tasks).map(([id, meta]: [string, any], i) => {
            const d = diff[meta.difficulty] ?? diff.medium;
            return (
              <motion.div
                key={id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.07, type: 'spring', stiffness: 220, damping: 24 }}
                onClick={() => onStart(id)}
                className={cn(
                  'group flex flex-col bg-[#080c18] border border-white/[0.06] rounded-2xl p-7 cursor-pointer transition-all duration-300 hover:-translate-y-1.5 hover:shadow-2xl',
                  d.border, d.glow
                )}
              >
                <span className={cn('self-start px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border mb-6', d.badge)}>
                  {meta.difficulty}
                </span>
                <h3 className={cn('text-xl font-black uppercase tracking-tight mb-3 transition-colors group-hover:text-white text-[#c8d8f0]')}>
                  {id.replace(/_/g, ' ')}
                </h3>
                <p className="text-sm text-[#8899bb] leading-relaxed mb-8 flex-1 line-clamp-4">{meta.description}</p>
                <div className="flex items-center justify-between text-[10px] text-[#2a3448] font-bold uppercase tracking-widest mb-5 pt-5 border-t border-white/[0.05]">
                  <span>{meta.num_documents} docs</span>
                  <span>{meta.max_steps} steps max</span>
                </div>
                <button className="w-full py-3.5 rounded-xl bg-white text-black text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 group-hover:bg-[#4f8eff] group-hover:text-white transition-all duration-200">
                  <Play size={12} fill="currentColor" /> Initialize
                </button>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════════════════════════════════════════════
export default function SimulationPage() {
  const [tasks, setTasks]               = useState<any>({});
  const [session, setSession]           = useState<Observation | null>(null);
  const [loading, setLoading]           = useState(false);
  const [docId, setDocId]               = useState<string | null>(null);
  const [tab, setTab]                   = useState<'docs' | 'actions'>('docs');
  const [buf, setBuf]                   = useState<{ docs: string[]; ents: string[] }>({ docs: [], ents: [] });
  const [form, setForm]                 = useState({ finding_type: 'duplicate_billing', defendant: '', amount_at_risk: 0, legal_basis: '31 U.S.C. §3729', evidence: [] as string[], reasoning: '' });

  useEffect(() => {
    fetchTasks().then(setTasks).catch(() => toast.error("Can't reach backend — is it running on :7860?"));
  }, []);

  const dispatch = async (action: any) => {
    if (!session) return;
    setLoading(true);
    try {
      const r = await stepEnv(action);
      setSession(r.observation);
      r.observation.last_action_error
        ? toast.error(r.observation.last_action_error)
        : toast.success(r.observation.last_action_result || 'Done');
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Action failed');
    } finally { setLoading(false); }
  };

  const start = async (id: string) => {
    setLoading(true);
    try {
      const d = await resetEnv(id);
      setSession(d); setDocId(null); setBuf({ docs: [], ents: [] });
      toast.success(`Started: ${id.replace(/_/g, ' ')}`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to connect');
    } finally { setLoading(false); }
  };

  const readDoc = (id: string) => { dispatch({ action_type: 'read_document', document_id: id }); setDocId(id); };
  const toggleBufDoc = (id: string) => setBuf(p => ({ ...p, docs: p.docs.includes(id) ? p.docs.filter(d => d !== id) : [...p.docs, id] }));
  const addEnt = (e: string) => {
    if (!e || e.length < 2) return;
    setBuf(p => ({ ...p, ents: p.ents.includes(e) ? p.ents : [...p.ents, e] }));
    toast.success(`Added: "${e}"`, { icon: '🔍' });
  };

  if (!session) return <Landing tasks={tasks} onStart={start} />;

  const pct = Math.min(100, Math.round(session.cumulative_reward * 100));

  return (
    <div className="h-screen w-screen flex flex-col bg-[#03040a] text-[#f0f4ff] overflow-hidden" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <Toaster position="top-right" toastOptions={{ style: { background: '#080c18', color: '#c8d8f0', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '14px', fontSize: '13px', padding: '12px 16px' } }} />

      {/* ══ HEADER ══ */}
      <header className="h-14 shrink-0 border-b flex items-center px-6 justify-between z-50 relative" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(8,12,24,0.96)', backdropFilter: 'blur(20px)' }}>
        {/* Left brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-[#4f8eff]/20 border border-[#4f8eff]/30 flex items-center justify-center">
            <Shield size={16} className="text-[#4f8eff]" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase tracking-widest text-[#2a3448]">OpenEnv</span>
            <span className="text-xs text-[#2a3448]">/</span>
            <span className="text-xs font-bold text-[#4f8eff] uppercase tracking-widest">{session.task_id.replace(/_/g, ' ')}</span>
          </div>
        </div>

        {/* Right stats */}
        <div className="flex items-center gap-7">
          {/* Progress arc-ish */}
          <div className="hidden md:flex items-center gap-7">
            <Stat label="Steps" val={`${session.steps_taken} / ${session.steps_taken + session.steps_remaining}`} dim />
            <Stat label="Reward" val={`+${session.cumulative_reward.toFixed(3)}`} />
            <div className="flex flex-col items-end gap-1">
              <span className="text-[9px] font-black text-[#404a62] uppercase tracking-widest">Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 rounded-full bg-[#111827] overflow-hidden">
                  <motion.div className="h-full rounded-full" style={{ background: pct > 60 ? '#27c27b' : '#4f8eff' }} animate={{ width: `${pct}%` }} transition={{ duration: 0.5, ease: 'easeOut' }} />
                </div>
                <span className="text-sm font-black tabular-nums text-white">{pct}%</span>
              </div>
            </div>
          </div>
          <div className="w-px h-6" style={{ background: 'rgba(255,255,255,0.06)' }} />
          <button onClick={() => setSession(null)} className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest text-[#404a62] border transition-all duration-150 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <RefreshCw size={12} /> Reset
          </button>
        </div>
      </header>

      {/* ══ BODY ══ */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── SIDEBAR ── */}
        <aside className="w-80 shrink-0 flex flex-col border-r overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.05)', background: '#04060f' }}>
          <div className="flex-1 overflow-y-auto p-6 space-y-8">

            {/* Objective */}
            <section>
              <Label>Task Objective</Label>
              <div className="p-4 rounded-xl border-l-2 border-[#4f8eff] bg-[#4f8eff]/[0.04]" style={{ borderTop: '1px solid rgba(79,142,255,0.1)', borderRight: '1px solid rgba(79,142,255,0.1)', borderBottom: '1px solid rgba(79,142,255,0.1)' }}>
                <p className="text-sm text-[#8899bb] leading-relaxed italic">{session.task_description}</p>
              </div>
            </section>

            {/* Internal Signals */}
            {session.detected_signals.length > 0 && (
              <section>
                <Label>Internal Signals</Label>
                <div className="space-y-3">
                  {session.detected_signals.map((sig, i) => (
                    <div key={i} className="p-4 rounded-xl border" style={{ background: '#080c18', borderColor: 'rgba(255,255,255,0.06)' }}>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-xs font-bold text-[#c8d8f0] leading-tight">{sig.signal_type.replace(/_/g, ' ')}</span>
                        <Sev s={sig.severity} />
                      </div>
                      <p className="text-xs text-[#404a62] leading-relaxed">{sig.description}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Investigation Buffer */}
            <section>
              <div className="flex items-center justify-between mb-3">
                <Label>Investigation Buffer</Label>
                {(buf.docs.length > 0 || buf.ents.length > 0) && (
                  <button onClick={() => setBuf({ docs: [], ents: [] })} className="text-[10px] font-bold text-[#2a3448] hover:text-red-400 transition-colors uppercase tracking-widest mb-3">clear</button>
                )}
              </div>

              {/* Docs */}
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[9px] font-black text-[#2a3448] uppercase tracking-[0.2em]">Reference Docs</span>
                  <span className="text-[9px] font-black text-[#2a3448] px-1.5 py-0.5 rounded bg-[#111827]">{buf.docs.length}</span>
                </div>
                {buf.docs.length === 0
                  ? <p className="text-xs text-[#2a3448] italic pl-0.5">No documents selected</p>
                  : <div className="space-y-1.5">
                      {buf.docs.map(id => (
                        <div key={id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#4f8eff]/10 border border-[#4f8eff]/20">
                          <span className="text-xs font-mono text-[#4f8eff] truncate">{id}</span>
                          <button onClick={() => toggleBufDoc(id)} className="ml-2 text-[#2a3448] hover:text-red-400 shrink-0 transition-colors"><X size={11} /></button>
                        </div>
                      ))}
                    </div>
                }
              </div>

              {/* Entities */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[9px] font-black text-[#2a3448] uppercase tracking-[0.2em]">Identified Entities</span>
                  <span className="text-[9px] font-black text-[#2a3448] px-1.5 py-0.5 rounded bg-[#111827]">{buf.ents.length}</span>
                </div>
                {buf.ents.length === 0
                  ? <p className="text-xs text-[#2a3448] italic pl-0.5">Double-click text in reader to add</p>
                  : <div className="space-y-1.5">
                      {buf.ents.map(n => (
                        <div key={n} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#27c27b]/10 border border-[#27c27b]/20">
                          <span className="text-xs text-[#27c27b] truncate">{n}</span>
                          <button onClick={() => setBuf(p => ({ ...p, ents: p.ents.filter(x => x !== n) }))} className="ml-2 text-[#2a3448] hover:text-red-400 shrink-0 transition-colors"><X size={11} /></button>
                        </div>
                      ))}
                    </div>
                }
              </div>
            </section>
          </div>

          {/* Action Result */}
          {(session.last_action_result || session.last_action_error) && (
            <div className="shrink-0 mx-4 mb-4 p-3.5 rounded-xl border text-xs" style={{ background: session.last_action_error ? 'rgba(239,68,68,0.06)' : 'rgba(39,194,123,0.06)', borderColor: session.last_action_error ? 'rgba(239,68,68,0.2)' : 'rgba(39,194,123,0.2)' }}>
              <p className={session.last_action_error ? 'text-red-400' : 'text-[#27c27b]'} style={{ wordBreak: 'break-word' }}>
                {session.last_action_error || session.last_action_result}
              </p>
            </div>
          )}
        </aside>

        {/* ── CENTER ── */}
        <main className="flex-1 flex flex-col min-w-0" style={{ background: '#040810' }}>
          {/* Tab bar */}
          <div className="shrink-0 flex border-b items-center px-2" style={{ borderColor: 'rgba(255,255,255,0.05)', background: '#04060f' }}>
            <Tab label="Records Repository" icon={<BookOpen size={13} />} active={tab === 'docs'} onClick={() => setTab('docs')} badge={session.available_documents.length} />
            <Tab label="Action Terminal" icon={<Zap size={13} />} active={tab === 'actions'} onClick={() => setTab('actions')} />
            {loading && (
              <div className="ml-auto mr-4 flex items-center gap-2 text-[11px] font-bold text-[#4f8eff] uppercase tracking-widest">
                <span className="w-1.5 h-1.5 rounded-full bg-[#4f8eff] animate-pulse" /> Processing
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-7">
            <AnimatePresence mode="wait">
              {tab === 'docs' && (
                <motion.div key="docs" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  {session.available_documents.map(doc => (
                    <DocCard key={doc.doc_id} doc={doc} active={docId === doc.doc_id} inBuf={buf.docs.includes(doc.doc_id)} onRead={() => readDoc(doc.doc_id)} onBuf={() => toggleBufDoc(doc.doc_id)} />
                  ))}
                </motion.div>
              )}
              {tab === 'actions' && (
                <motion.div key="actions" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                  <Actions buf={buf} form={form} setForm={setForm} dispatch={dispatch} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        {/* ── READER ── */}
        <AnimatePresence>
          {docId && (
            <motion.aside
              initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
              className="w-[400px] shrink-0 flex flex-col border-l shadow-2xl"
              style={{ borderColor: 'rgba(255,255,255,0.06)', background: '#04060f' }}
            >
              {/* Reader header */}
              <div className="shrink-0 flex items-center gap-3 px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)', background: '#03040a' }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'rgba(79,142,255,0.12)', border: '1px solid rgba(79,142,255,0.2)' }}>
                  <FileText size={16} className="text-[#4f8eff]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-black uppercase tracking-widest text-white truncate">{docId}</p>
                  <p className="text-[10px] text-[#2a3448] mt-0.5">Double-click text to capture entity</p>
                </div>
                <button onClick={() => setDocId(null)} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/[0.05] transition-colors shrink-0">
                  <X size={15} className="text-[#404a62]" />
                </button>
              </div>

              {/* Hint */}
              <div className="shrink-0 mx-5 mt-4 px-4 py-3 rounded-xl flex items-center gap-3" style={{ background: 'rgba(79,142,255,0.06)', border: '1px solid rgba(79,142,255,0.12)' }}>
                <Eye size={13} className="text-[#4f8eff] shrink-0" />
                <p className="text-[11px] text-[#4f8eff] leading-snug">Double-click any word to add it to your investigative buffer.</p>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5" onDoubleClick={() => { const s = window.getSelection()?.toString().trim(); if (s && s.length > 1) addEnt(s); }}>
                {session.read_documents[docId]
                  ? <DocContent v={session.read_documents[docId]} />
                  : <div className="h-32 flex flex-col items-center justify-center text-[#2a3448]">
                      <FileText size={28} className="mb-3" />
                      <p className="text-sm">Loading…</p>
                    </div>
                }
              </div>

              {/* Footer */}
              <div className="shrink-0 p-5 border-t" style={{ borderColor: 'rgba(255,255,255,0.05)', background: '#03040a' }}>
                <button
                  onClick={() => toggleBufDoc(docId)}
                  className={cn(
                    'w-full py-3 rounded-xl text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2 transition-all duration-200',
                    buf.docs.includes(docId)
                      ? 'bg-[#4f8eff]/20 border border-[#4f8eff]/40 text-[#4f8eff]'
                      : 'border text-[#404a62] hover:border-[#4f8eff]/30 hover:text-[#4f8eff]'
                  )}
                  style={!buf.docs.includes(docId) ? { borderColor: 'rgba(255,255,255,0.07)' } : {}}
                >
                  <Binary size={13} />
                  {buf.docs.includes(docId) ? '✓ In Reference Buffer' : 'Add to Reference Buffer'}
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* ══ STATUS BAR ══ */}
      <footer className="h-7 shrink-0 border-t px-6 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-[#2a3448]" style={{ borderColor: 'rgba(255,255,255,0.04)', background: '#03040a' }}>
        <div className="flex items-center gap-5">
          <span className="flex items-center gap-1.5"><Activity size={9} className="text-[#27c27b] animate-pulse" /> System Online</span>
          <span>·</span>
          <span>API: 127.0.0.1:7860</span>
        </div>
        <span className="text-[#2a3448]">Difficulty: <span className="text-[#404a62]">{session.difficulty}</span></span>
      </footer>
    </div>
  );
}

// ═════════════════════════════════════════
// DOC CARD
// ═════════════════════════════════════════
function DocCard({ doc, active, inBuf, onRead, onBuf }: { doc: any; active: boolean; inBuf: boolean; onRead: () => void; onBuf: () => void }) {
  return (
    <div
      className={cn(
        'group flex gap-4 p-5 rounded-2xl border transition-all duration-200 cursor-pointer',
        active ? 'border-[#4f8eff]/40' : 'hover:border-white/10',
        doc.is_read ? 'bg-[#080c18]' : 'bg-[#060912] hover:bg-[#080c18]'
      )}
      style={{ borderColor: active ? undefined : 'rgba(255,255,255,0.05)' }}
    >
      {/* Icon */}
      <div onClick={onRead} className={cn('w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-colors', doc.is_read ? 'bg-[#4f8eff]/15 text-[#4f8eff]' : 'bg-white/[0.04] text-[#404a62] group-hover:text-[#8899bb]')}>
        <FileText size={19} />
      </div>

      {/* Text */}
      <div className="flex-1 min-w-0 cursor-pointer" onClick={onRead}>
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-[9px] font-black text-[#2a3448] uppercase tracking-[0.2em]">{doc.doc_type.replace(/_/g, ' ')}</span>
          {doc.is_read && <span className="px-1.5 py-0.5 rounded bg-[#4f8eff]/15 text-[#4f8eff] text-[9px] font-black uppercase tracking-widest">Read</span>}
          {active && <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[#8899bb] text-[9px] font-black uppercase tracking-widest">Viewing</span>}
        </div>
        <h4 className="text-sm font-bold text-[#c8d8f0] mb-1 leading-snug group-hover:text-white transition-colors line-clamp-2">{doc.title}</h4>
        <p className="text-[11px] font-mono text-[#2a3448] mb-2">{doc.doc_id}</p>
        <p className="text-xs text-[#404a62] leading-relaxed line-clamp-2">{doc.preview}</p>
      </div>

      {/* Buffer btn */}
      <button
        onClick={e => { e.stopPropagation(); onBuf(); }}
        className={cn(
          'w-9 h-9 flex items-center justify-center rounded-xl border shrink-0 mt-0.5 transition-all duration-200',
          inBuf ? 'bg-[#4f8eff] border-[#4f8eff] text-white' : 'text-[#2a3448] hover:text-[#4f8eff] hover:border-[#4f8eff]/40'
        )}
        style={!inBuf ? { borderColor: 'rgba(255,255,255,0.06)' } : {}}
        title={inBuf ? 'Remove from buffer' : 'Add to buffer'}
      >
        <Bookmark size={14} fill={inBuf ? 'currentColor' : 'none'} />
      </button>
    </div>
  );
}

// ═════════════════════════════════════════
// ACTION TERMINAL
// ═════════════════════════════════════════
function Actions({ buf, form, setForm, dispatch }: { buf: { docs: string[]; ents: string[] }; form: any; setForm: any; dispatch: (a: any) => void }) {
  const acts = [
    { icon: <Flag size={22} />, label: 'Flag Duplicates', desc: 'Mark two or more docs as duplicate billing claims', color: '#f97316',
      go: () => buf.docs.length < 2 ? toast.error('Select ≥2 docs in the Records tab first') : dispatch({ action_type: 'flag_duplicate', entity_ids: buf.docs }) },
    { icon: <Search size={22} />, label: 'Trace Ownership', desc: 'Follow entity chain from child to parent company', color: '#4f8eff',
      go: () => buf.ents.length < 2 ? toast.error('Add 2 entities via the document reader') : dispatch({ action_type: 'trace_ownership', entity_ids: buf.ents }) },
    { icon: <AlertCircle size={22} />, label: 'Flag Shell Co.', desc: 'Mark selected entity as a potential shell company', color: '#a855f7',
      go: () => buf.ents.length < 1 ? toast.error('Add an entity from the reader first') : dispatch({ action_type: 'flag_shell_company', entity_ids: [buf.ents[0]] }) },
    { icon: <BarChart3 size={22} />, label: 'Overbilling Audit', desc: 'Flag a provider for systematic over-billing', color: '#ef4444',
      go: () => buf.ents.length < 1 ? toast.error('Select a provider entity from the reader') : dispatch({ action_type: 'flag_overbilling', entity_ids: [buf.ents[0]] }) },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-black uppercase italic tracking-tighter text-white mb-1">Investigative Protocols</h2>
        <p className="text-sm text-[#404a62]">Deploy countermeasures using your buffered evidence</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {acts.map((a, i) => (
          <button key={i} onClick={a.go} className="group text-left flex flex-col gap-5 p-6 rounded-2xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl" style={{ background: '#080c18', borderColor: 'rgba(255,255,255,0.06)' }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = a.color + '44')}
            onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)')}
          >
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center transition-colors" style={{ background: a.color + '15', color: a.color }}>
              {a.icon}
            </div>
            <div>
              <p className="text-sm font-bold text-[#c8d8f0] mb-1 group-hover:text-white transition-colors">{a.label}</p>
              <p className="text-xs text-[#404a62] leading-snug">{a.desc}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.05)' }} />
        <span className="text-[10px] font-black text-[#2a3448] uppercase tracking-[0.25em] flex items-center gap-2"><Layers size={9} /> Formal Submission</span>
        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.05)' }} />
      </div>

      {/* Form */}
      <div className="p-7 rounded-2xl relative overflow-hidden" style={{ background: '#080c18', border: '1px solid rgba(39,194,123,0.15)' }}>
        <div className="absolute left-0 top-8 bottom-8 w-0.5 rounded-full" style={{ background: 'linear-gradient(to bottom, transparent, #27c27b, transparent)' }} />
        <h4 className="text-sm font-black uppercase tracking-widest text-white mb-7 flex items-center gap-3">
          <Send size={14} className="text-[#27c27b]" /> Professional Finding Submission
        </h4>
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Defendant" placeholder="e.g. MedCorp LLC" onChange={v => setForm({ ...form, defendant: v })} />
            <Field label="Amount at Risk ($)" type="number" placeholder="0.00" onChange={v => setForm({ ...form, amount_at_risk: parseFloat(v) })} />
          </div>
          <Field label="Legal Basis" placeholder="31 U.S.C. §3729" value={form.legal_basis} onChange={v => setForm({ ...form, legal_basis: v })} />
          <Field label="Evidence (auto-populated from buffer)" value={buf.docs.join(', ')} onChange={v => setForm({ ...form, evidence: v.split(',').map((s: string) => s.trim()) })} />
          <Field label="Reasoning & Justification" textarea placeholder="Detail how the evidence reflects a systematic fraud pattern…" onChange={v => setForm({ ...form, reasoning: v })} />
          <button
            onClick={() => dispatch({ action_type: 'submit_finding', ...form, evidence: buf.docs })}
            className="w-full py-4 rounded-xl text-sm font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-200 hover:brightness-110 active:scale-[0.99]"
            style={{ background: 'linear-gradient(135deg, #1a7a52, #27c27b)', color: '#fff', boxShadow: '0 0 30px rgba(39,194,123,0.15)' }}
          >
            <Shield size={16} /> Submit Formal Complaint
          </button>
        </div>
      </div>
    </div>
  );
}
