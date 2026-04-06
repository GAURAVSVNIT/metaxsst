'use client';

import React, { useState, useEffect } from 'react';
import {
  Shield, FileText, Search, Activity, Flag, AlertCircle,
  X, RefreshCw, BarChart3, Bookmark, Eye, ArrowRight,
  Target, History, Database, Layers, Send, Inbox
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import { resetEnv, stepEnv, fetchTasks, Observation, FraudSignal } from '@/lib/api';

// --- Utility ---
function cn(...c: (string | boolean | undefined | null)[]) {
  return c.filter(Boolean).join(' ');
}

// --- Components ---

function Badge({ variant, children }: { variant: string, children: React.ReactNode }) {
  const styles: Record<string, string> = {
    easy: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    medium: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    hard: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    neutral: 'bg-white/5 text-zinc-400 border-white/10'
  };
  const activeStyle = styles[variant.toLowerCase()] || styles.neutral;
  
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border', activeStyle)}>
      {children}
    </span>
  );
}

// --- Landing Page ---

function Landing({ tasks, onStart }: { tasks: Record<string, any>; onStart: (id: string) => void }) {
  return (
    <div className="min-h-screen bg-black flex flex-col overflow-y-auto selection:bg-white/20">
      <div className="max-w-6xl mx-auto px-6 py-24 w-full flex-1 flex flex-col">
        <header className="mb-16">
          <div className="w-12 h-12 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center mb-6">
            <Shield size={24} className="text-white" />
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-white mb-4 leading-tight">Fraud Detection <br/>Simulation Environment</h1>
          <p className="text-zinc-500 max-w-2xl text-lg relative font-medium">Select an investigative scenario. Each protocol provides specific document artifacts and procedural constraints.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(tasks).map(([id, meta]: [string, any], i) => (
            <motion.div
              key={id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => onStart(id)}
              className="group flex flex-col bg-[#0a0a0a] border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all cursor-pointer hover:bg-[#0f0f0f]"
            >
              <div className="flex items-center justify-between mb-8">
                <Badge variant={meta.difficulty}>{meta.difficulty}</Badge>
                <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                  <ArrowRight size={14} className="text-zinc-400 group-hover:text-white transition-colors" />
                </div>
              </div>
              
              <h3 className="text-lg font-medium text-white mb-3 tracking-tight capitalize leading-tight">
                {id.replace(/_/g, ' ')}
              </h3>
              
              <p className="text-sm text-zinc-400 mb-8 flex-1 leading-relaxed">
                {meta.description}
              </p>
              
              <div className="flex items-center justify-between border-t border-white/10 pt-5 mt-auto">
                <div className="flex items-center gap-6 text-xs text-zinc-500 font-medium">
                  <span className="flex items-center gap-2"><Database size={14} /> {meta.num_documents} Artifacts</span>
                  <span className="flex items-center gap-2"><Activity size={14} /> {meta.max_steps} Steps</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Main Simulation App ---

export default function SimulationPage() {
  const [tasks, setTasks]               = useState<any>({});
  const [session, setSession]           = useState<Observation | null>(null);
  const [loading, setLoading]           = useState(false);
  const [docId, setDocId]               = useState<string | null>(null);
  const [view, setView]                 = useState<'repo' | 'ops'>('repo');
  const [buffer, setBuffer]             = useState<{ docs: string[]; entities: string[] }>({ docs: [], entities: [] });
  const [form, setForm]                 = useState({ 
    finding_type: 'duplicate_billing', 
    defendant: '', 
    amount_at_risk: 0, 
    legal_basis: '', 
    evidence: [] as string[], 
    reasoning: '' 
  });

  useEffect(() => {
    fetchTasks().then(setTasks).catch(() => toast.error("Connection failed. Check API."));
  }, []);

  const dispatchAction = async (action: any) => {
    if (!session) return;
    setLoading(true);
    try {
      const r = await stepEnv(action);
      setSession(r.observation);
      if (r.observation.last_action_error) {
        toast.error(r.observation.last_action_error, { icon: '⚠️' });
      } else {
        toast.success(r.observation.last_action_result || 'Action registered');
      }
    } catch (e: any) {
      toast.error('System Error');
    } finally { setLoading(false); }
  };

  const startInvestigation = async (id: string) => {
    setLoading(true);
    try {
      const d = await resetEnv(id);
      setSession(d); 
      setDocId(null); 
      setBuffer({ docs: [], entities: [] });
      toast.success(`Protocol started: ${id.replace(/_/g, ' ')}`);
    } catch (e: any) {
      toast.error('Initialization failed');
    } finally { setLoading(false); }
  };

  if (!session) return <Landing tasks={tasks} onStart={startInvestigation} />;

  const progress = Math.min(100, Math.round(session.cumulative_reward * 100));

  return (
    <div className="h-screen w-screen flex flex-col bg-black text-white font-sans overflow-hidden selection:bg-white/20">
      <Toaster position="bottom-right" toastOptions={{ 
        style: { background: '#111', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', fontSize: '13px', borderRadius: '8px' } 
      }} />

      {/* Header */}
      <header className="h-14 shrink-0 border-b border-white/10 flex items-center justify-between px-6 bg-black z-20">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
             <Shield size={16} className="text-zinc-400" />
             <span className="font-semibold text-sm tracking-tight capitalize">{session.task_id.replace(/_/g, ' ')}</span>
          </div>
          <div className="h-4 w-[1px] bg-white/10" />
          <span className="text-xs text-zinc-500 font-medium">Steps: {session.steps_taken} / {session.steps_taken + session.steps_remaining}</span>
          <span className="text-xs text-zinc-500 font-medium flex items-center gap-2">
            Reward: <span className={cn('px-2 py-0.5 rounded bg-white/5 font-mono', progress > 50 ? 'text-emerald-400' : 'text-zinc-300')}>{progress}%</span>
          </span>
        </div>
        <div className="flex items-center gap-4">
          {loading && <RefreshCw size={14} className="animate-spin text-zinc-500" />}
          <button onClick={() => setSession(null)} className="text-xs font-medium text-zinc-400 hover:text-white transition-colors">Exit Simulation</button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Sidebar: Intelligence & Evidence */}
        <aside className="w-80 shrink-0 border-r border-white/10 bg-[#050505] flex flex-col overflow-y-auto custom-scrollbar">
          
          <div className="p-6 border-b border-white/5">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3 flex items-center gap-2"><Target size={14} /> Objective</h3>
            <p className="text-sm text-zinc-300 leading-relaxed font-medium">{session.task_description}</p>
          </div>

          <div className="p-6 flex-1 flex flex-col gap-8">
            {/* Document Evidence */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Document Evidence</h3>
                <span className="text-[10px] font-mono text-zinc-600 bg-white/5 px-1.5 rounded">{buffer.docs.length}</span>
              </div>
              {buffer.docs.length === 0 ? (
                <div className="p-4 border border-dashed border-white/10 rounded-xl text-center">
                  <p className="text-xs text-zinc-600 font-medium tracking-tight">No documents captured.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {buffer.docs.map(id => (
                    <div key={id} className="flex items-center justify-between p-2.5 rounded-lg bg-[#0f0f0f] border border-white/5 group">
                      <span className="text-xs font-mono text-zinc-300 truncate pr-4">{id}</span>
                      <button onClick={() => setBuffer(p => ({ ...p, docs: p.docs.filter(d => d !== id) }))} className="text-zinc-600 hover:text-rose-400"><X size={14} /></button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Entity Evidence */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Entity Cache</h3>
                <span className="text-[10px] font-mono text-zinc-600 bg-white/5 px-1.5 rounded">{buffer.entities.length}</span>
              </div>
              {buffer.entities.length === 0 ? (
                <div className="p-4 border border-dashed border-white/10 rounded-xl text-center">
                   <p className="text-xs text-zinc-600 font-medium tracking-tight">Highlight text in reader to capture.</p>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {buffer.entities.map(ent => (
                    <div key={ent} className="flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-md bg-white/5 border border-white/10 group">
                      <span className="text-xs font-medium text-zinc-200">{ent}</span>
                      <button onClick={() => setBuffer(p => ({ ...p, entities: p.entities.filter(x => x !== ent) }))} className="text-zinc-600 hover:text-rose-400"><X size={12} /></button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Signals */}
            {session.detected_signals.length > 0 && (
              <div>
                 <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2"><AlertCircle size={14} /> Signals</h3>
                 <div className="space-y-3">
                    {session.detected_signals.map((sig, i) => (
                      <div key={i} className="p-4 rounded-xl bg-[#0f0f0f] border border-white/5">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold capitalize text-zinc-300 tracking-tight">{sig.signal_type.replace(/_/g, ' ')}</span>
                          <span className={cn('w-2 h-2 rounded-full', sig.severity === 'high' || sig.severity === 'critical' ? 'bg-rose-500' : 'bg-amber-500')} />
                        </div>
                        <p className="text-xs text-zinc-500 font-medium leading-relaxed">{sig.description}</p>
                      </div>
                    ))}
                 </div>
              </div>
            )}
            
            {/* Clear button bottom */}
            {(buffer.docs.length > 0 || buffer.entities.length > 0) && (
              <button 
                onClick={() => setBuffer({ docs: [], entities: [] })}
                className="mt-auto py-3 text-xs font-medium text-zinc-500 hover:text-rose-400 bg-white/5 rounded-xl transition-colors"
              >
                Clear all evidence
              </button>
            )}

          </div>
        </aside>

        {/* Center Canvas */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#0a0a0a] relative">
          
          {/* Tab Switcher */}
          <div className="flex items-center border-b border-white/10 px-8 bg-black shrink-0">
             <button 
               onClick={() => setView('repo')} 
               className={cn('px-4 py-4 text-sm font-medium border-b-2 transition-all mr-6', view === 'repo' ? 'border-white text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300')}
             >
               Records Repository
             </button>
             <button 
               onClick={() => setView('ops')} 
               className={cn('px-4 py-4 text-sm font-medium border-b-2 transition-all', view === 'ops' ? 'border-white text-white' : 'border-transparent text-zinc-500 hover:text-zinc-300')}
             >
               Determination Terminal
             </button>
          </div>

          <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
             {view === 'repo' && (
               <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-6 max-w-7xl">
                 {session.available_documents.map((doc) => {
                   const inBuffer = buffer.docs.includes(doc.doc_id);
                   const isRead = doc.is_read;
                   return (
                     <div 
                       key={doc.doc_id}
                       className="group flex flex-col p-6 rounded-2xl bg-[#0f0f0f] border border-white/5 hover:border-white/15 transition-all"
                     >
                       <div className="flex justify-between items-start mb-6">
                         <Badge variant={isRead ? 'easy' : 'neutral'}>{doc.doc_type.replace(/_/g, ' ')}</Badge>
                         <button 
                           onClick={() => setBuffer(p => ({ ...p, docs: inBuffer ? p.docs.filter(d => d !== doc.doc_id) : [...p.docs, doc.doc_id] }))}
                           className={cn('p-2 rounded-lg transition-colors', inBuffer ? 'bg-white text-black' : 'bg-white/5 text-zinc-500 hover:text-white')}
                         >
                           <Bookmark size={14} fill={inBuffer ? 'currentColor' : 'none'} />
                         </button>
                       </div>
                       
                       <h4 className="text-base font-medium text-white tracking-tight mb-2 leading-snug">{doc.title}</h4>
                       
                       <div className="mb-6">
                         <p className="text-xs text-zinc-500 font-medium leading-relaxed line-clamp-2">&quot;{doc.preview}&quot;</p>
                       </div>
                       
                       <button
                         onClick={() => { dispatchAction({ action_type: 'read_document', document_id: doc.doc_id }); setDocId(doc.doc_id); }}
                         className="mt-auto w-full py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-semibold text-white transition-colors"
                       >
                         Open Record
                       </button>
                     </div>
                   );
                 })}
               </div>
             )}

             {view === 'ops' && (
               <div className="max-w-4xl space-y-12 pb-20">
                 {/* Quick Actions */}
                 <div>
                   <h2 className="text-sm font-semibold text-white mb-4">Immediate Actions</h2>
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <ActionBtn icon={Flag} label="Flag Duplicate Claims" sub="Requires ≥2 records in evidence" 
                        onClick={() => buffer.docs.length < 2 ? toast.error('Requires ≥2 records') : dispatchAction({ action_type: 'flag_duplicate', entity_ids: buffer.docs })} />
                      <ActionBtn icon={Search} label="Trace Ownership Structure" sub="Requires 2 entities in cache" 
                        onClick={() => buffer.entities.length < 2 ? toast.error('Requires 2 entities') : dispatchAction({ action_type: 'trace_ownership', entity_ids: buffer.entities })} />
                      <ActionBtn icon={AlertCircle} label="Flag as Shell Company" sub="Requires 1 entity (the company)" 
                        onClick={() => buffer.entities.length < 1 ? toast.error('Requires target entity') : dispatchAction({ action_type: 'flag_shell_company', entity_ids: [buffer.entities[0]] })} />
                      <ActionBtn icon={BarChart3} label="Submit Overbilling Audit" sub="Requires 1 entity (the provider)" 
                        onClick={() => buffer.entities.length < 1 ? toast.error('Requires target entity') : dispatchAction({ action_type: 'flag_overbilling', entity_ids: [buffer.entities[0]] })} />
                   </div>
                 </div>

                 {/* Formal Determination Form */}
                 <div className="p-8 rounded-2xl bg-[#0f0f0f] border border-white/5">
                   <div className="flex items-center gap-4 mb-8">
                      <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                        <Send size={18} className="text-white" />
                      </div>
                      <div>
                        <h2 className="text-lg font-medium text-white tracking-tight">Final Resolution</h2>
                        <p className="text-xs text-zinc-500 font-medium mt-0.5">Submit comprehensive legal finding to conclude case.</p>
                      </div>
                   </div>

                   <div className="grid gap-6 mb-6">
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                           <label className="block text-xs font-medium text-zinc-400 mb-2">Subject Entity</label>
                           <input value={form.defendant} onChange={e => setForm({...form, defendant: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-sm focus:border-white/30 outline-none transition-colors" placeholder="e.g. MedSupply Corp" />
                        </div>
                        <div>
                           <label className="block text-xs font-medium text-zinc-400 mb-2">Liability Amount ($)</label>
                           <input type="number" value={form.amount_at_risk} onChange={e => setForm({...form, amount_at_risk: parseFloat(e.target.value)})} className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-sm focus:border-white/30 outline-none transition-colors" placeholder="0.00" />
                        </div>
                      </div>
                      
                      <div>
                         <label className="block text-xs font-medium text-zinc-400 mb-2">Statutory Basis</label>
                         <input value={form.legal_basis} onChange={e => setForm({...form, legal_basis: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-sm focus:border-white/30 outline-none transition-colors" placeholder="e.g. 31 U.S.C. §3729" />
                      </div>

                      <div>
                         <label className="block text-xs font-medium text-zinc-400 mb-2">Legal Justification</label>
                         <textarea rows={4} value={form.reasoning} onChange={e => setForm({...form, reasoning: e.target.value})} className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-sm focus:border-white/30 outline-none transition-colors resize-none" placeholder="Provide finding logic based on evidence..." />
                      </div>
                   </div>

                   <button 
                     disabled={loading}
                     onClick={() => dispatchAction({ action_type: 'submit_finding', ...form, evidence: buffer.docs })}
                     className="w-full py-3.5 bg-white text-black font-semibold text-sm rounded-lg hover:bg-zinc-200 transition-colors disabled:opacity-50"
                   >
                     Submit Finding
                   </button>
                 </div>
               </div>
             )}
          </div>
        </main>

        {/* Slide-over Reader Overlay */}
        <AnimatePresence>
          {docId && (
            <>
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                onClick={() => setDocId(null)}
                className="absolute inset-0 bg-black/40 z-30 backdrop-blur-sm"
              />
              <motion.div
                initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                className="absolute top-0 right-0 bottom-0 w-[560px] bg-[#0d0d0d] border-l border-white/10 z-40 flex flex-col shadow-2xl"
              >
                <header className="h-14 shrink-0 border-b border-white/10 flex items-center justify-between px-6">
                  <span className="font-mono text-sm tracking-tight text-white">{docId}</span>
                  <button onClick={() => setDocId(null)} className="text-zinc-500 hover:text-white transition-colors p-1"><X size={18} /></button>
                </header>

                <div 
                  className="flex-1 overflow-y-auto p-8 custom-scrollbar text-zinc-300"
                  onDoubleClick={() => {
                     const s = window.getSelection()?.toString().trim();
                     if (s && s.length > 2) {
                       setBuffer(p => ({ ...p, entities: p.entities.includes(s) ? p.entities : [...p.entities, s] }));
                       toast.success('Indexed entity');
                     }
                  }}
                >
                  <div className="mb-8 p-4 rounded-xl bg-white/5 border border-white/10 flex gap-3 text-sm text-zinc-400">
                    <Eye size={18} className="shrink-0 mt-0.5" />
                    <p>Highlight text and double-click to capture it into your entity evidence cache.</p>
                  </div>
                  
                  {session.read_documents[docId] ? (
                    <JsonDisplay data={session.read_documents[docId]} />
                  ) : (
                    <div className="py-20 flex justify-center"><RefreshCw size={24} className="animate-spin text-zinc-700" /></div>
                  )}
                </div>

                <div className="p-6 border-t border-white/10 bg-[#0d0d0d]">
                  <button 
                    onClick={() => {
                       const inBuf = buffer.docs.includes(docId);
                       setBuffer(p => ({ ...p, docs: inBuf ? p.docs.filter(d => d !== docId) : [...p.docs, docId] }));
                    }}
                    className={cn(
                      'w-full py-3 rounded-lg text-sm font-semibold transition-colors border',
                      buffer.docs.includes(docId) 
                        ? 'bg-white text-black border-white' 
                        : 'bg-transparent text-white border-white/20 hover:border-white/40'
                    )}
                  >
                    {buffer.docs.includes(docId) ? 'Remove Record from Evidence' : 'Add Record to Evidence'}
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Subcomponent for Ops actions
function ActionBtn({ icon: Icon, label, sub, onClick }: any) {
  return (
    <button onClick={onClick} className="flex items-start gap-4 p-5 rounded-xl bg-[#0f0f0f] border border-white/5 hover:border-white/15 transition-all text-left group">
      <div className="p-2.5 bg-white/5 rounded-lg text-white group-hover:bg-white/10 transition-colors">
        <Icon size={18} />
      </div>
      <div>
        <h4 className="text-sm font-medium text-white tracking-tight mb-1">{label}</h4>
        <p className="text-xs text-zinc-500 font-medium">{sub}</p>
      </div>
    </button>
  );
}

// Subcomponent to cleanly render nested doc JSON data
function JsonDisplay({ data, depth = 0 }: any) {
  if (data === null || data === undefined) return <span className="text-zinc-600 font-mono text-sm">null</span>;
  if (typeof data === 'boolean') return <span className="text-zinc-300 font-mono text-sm">{data ? 'true' : 'false'}</span>;
  if (typeof data === 'number') return <span className="text-white font-mono text-sm">{data}</span>;
  if (typeof data === 'string') return <span className="text-zinc-200 text-[15px] leading-relaxed selection:bg-white/20">{data}</span>;

  if (Array.isArray(data)) {
    return (
      <div className="space-y-4">
        {data.map((item, i) => (
          <div key={i} className="pl-4 border-l-2 border-white/10">
            <JsonDisplay data={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {Object.entries(data).map(([key, val]) => {
        const complex = typeof val === 'object' && val !== null;
        return (
          <div key={key}>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-widest mb-2 font-mono">{key}</div>
            <div className={cn(complex && 'pl-4 border-l border-white/10 mt-2')}>
              <JsonDisplay data={val} depth={depth + 1} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
