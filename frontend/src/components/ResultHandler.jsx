import React from "react";
import { Loader, Terminal, Link as LinkIcon, AlertTriangle, BookOpen, BarChart3, Database, Newspaper } from "lucide-react";

const ResultHandler = ({ 
    query: q, 
    index, 
    configGroups, 
    toggleTab, 
    formatUrlText, 
    formatSpecValue, 
    getEnhancedUrl, 
    getSentimentTier 
}) => {
   if (q.error) return <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-md font-inter">{q.error}</div>;

   // Show loader if absolutely no results yet and not done
   if (!q.results && q.status !== "Done") {
      return (
         <div className="glass-panel flex items-center gap-3 text-slate-400 p-5 w-auto font-inter">
            <Loader className="animate-spin" size={24} />
            <span>{q.status}</span>
         </div>
      );
   }

   // Base state
   const currentTab = q.resultTab || 'facts';
   const results = q.results || {};
   const factsData = results.facts || {};
   const researchData = results.research || {};
   const analysisData = results.analysis || {};

   // Gather all unique normalized entity names
   const entities = Array.from(new Set([
      ...Object.keys(factsData), 
      ...Object.keys(researchData), 
      ...Object.keys(analysisData)
   ]));

   // Render Facts (Table Mode)
   const renderFactsTable = () => {
      const allAspects = Array.from(new Set(Object.values(factsData).flat().map(r => r.aspect)));
      if (allAspects.length === 0) {
         return (
            <div className="p-10 text-center space-y-4">
               <Database className="mx-auto text-slate-700" size={48} />
               <p className="text-slate-500 italic">No biographical or technical facts found for this query.</p>
               {Object.keys(researchData).length > 0 && <p className="text-cyan-500 text-xs font-bold uppercase cursor-pointer hover:underline" onClick={() => toggleTab(index, 'research')}>Check Research & News Tab →</p>}
            </div>
         );
      }

      const renderedAspects = new Set();
      const rows = [];
      const isTech = q.parsed?.query_type?.startsWith("tech");
      
      let GROUPS = configGroups ? (isTech ? configGroups.tech : configGroups.general) : {};
      const groupOrder = Object.keys(GROUPS);

      groupOrder.forEach(groupName => {
         const groupKeys = GROUPS[groupName].map(k => k.toLowerCase());
         const matchingAspects = allAspects.filter(asp => {
            const lowAsp = asp.toLowerCase();
            return (groupKeys.includes(lowAsp) || lowAsp.includes(groupName.toLowerCase().split(' ')[0])) && !renderedAspects.has(asp);
         });

         if (matchingAspects.length > 0) {
            rows.push(<tr key={`header-${groupName}`} className="spec-category-header"><td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-cyan-400/80 border-none">{groupName}</td></tr>);
            matchingAspects.forEach(asp => {
               renderedAspects.add(asp);
               rows.push(renderRow(asp, factsData));
            });
         }
      });

      const otherAspects = allAspects.filter(asp => !renderedAspects.has(asp));
      if (otherAspects.length > 0) {
         rows.push(<tr key="header-other" className="spec-category-header"><td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 border-none">Additional Details</td></tr>);
         otherAspects.forEach(asp => rows.push(renderRow(asp, factsData)));
      }

      return (
         <div className="overflow-x-auto w-full px-6">
            <table className="w-full text-left border-collapse font-inter">
               <thead>
                  <tr>
                     <th className="bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] rounded-tl-xl border-b border-white/5 w-[25%]">Aspect</th>
                     {entities.map((en, i) => (
                        <th key={en} className={`bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] border-b border-white/5 ${i === entities.length - 1 ? 'rounded-tr-xl' : ''}`}>{en}</th>
                     ))}
                  </tr>
               </thead>
               <tbody>{rows}</tbody>
            </table>
         </div>
      );
   };

   const renderRow = (asp, dataMap) => {
      return (
         <tr key={asp} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
            <td className="py-4 pl-8 pr-6 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400">
               {asp}
            </td>
            {entities.map(en => {
               const item = (dataMap[en] || []).find(r => r.aspect === asp);
               return (
                  <td key={en} className="py-4 px-6 text-sm text-slate-200">
                     {item ? (
                        <div className="flex items-center gap-2">
                           {formatSpecValue(`${item.value} ${item.unit || ''}`)}
                           {item.source && <a href={item.source} target="_blank" rel="noreferrer" className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-cyan-400"><LinkIcon size={12} /></a>}
                        </div>
                     ) : '-'}
                  </td>
               );
            })}
         </tr>
      );
   };

   // Render Research/News (List Mode)
   const renderResearchList = () => {
      const allItems = Object.values(researchData).flat();
      const newsItems = allItems.filter(r => r.aspect.toLowerCase().includes("summary") || r.aspect.toLowerCase().includes("research:"));
      const detailItems = allItems.filter(r => !newsItems.includes(r));

      if (allItems.length === 0) {
         return (
            <div className="p-10 text-center space-y-4">
               <Newspaper className="mx-auto text-slate-700" size={48} />
               <p className="text-slate-500 italic">No in-depth news or research found yet.</p>
            </div>
         );
      }

      return (
         <div className="px-8 space-y-12">
            {/* Top Summaries / News Articles */}
            <div className="space-y-6">
               <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-400/80 mb-6 flex items-center gap-2">
                  <Newspaper size={14} /> Top Reported Articles
               </h4>
               {newsItems.map((s, i) => (
                  <div key={i} className="group relative bg-slate-900/40 border border-white/5 rounded-2xl p-6 transition-all hover:bg-slate-900/60 hover:border-cyan-500/20 animate-in fade-in slide-in-from-left-2">
                     <div className="flex justify-between items-start mb-4">
                        <div className="flex flex-col gap-1">
                           <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">{s.aspect.replace("Summary: ", "").replace("Research: ", "")}</span>
                           <span className="text-[10px] text-slate-500 font-medium">{formatUrlText(s.source)} {s.date ? ` • ${s.date}` : ''}</span>
                        </div>
                        <a href={s.source} target="_blank" rel="noreferrer" className="p-2 rounded-full bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                           <LinkIcon size={14} />
                        </a>
                     </div>
                     <div className="text-slate-300 text-sm leading-relaxed italic border-l-2 border-slate-700 pl-4 py-1">
                        {s.value}
                     </div>
                  </div>
               ))}
            </div>

            {/* Key Findings / Factual Details */}
            {detailItems.length > 0 && (
               <div className="bg-slate-900/20 rounded-3xl p-6 border border-white/5">
                  <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 mb-6">Key Event Details</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                     {detailItems.map((f, i) => (
                        <div key={i} className="flex flex-col gap-1 border-b border-white/[0.03] pb-4">
                           <span className="text-[9px] font-black uppercase tracking-widest text-cyan-500/60">{f.aspect}</span>
                           <span className="text-sm text-slate-200 font-medium">{f.value}</span>
                           <span className="text-[9px] text-slate-600">{formatUrlText(f.source)}</span>
                        </div>
                     ))}
                  </div>
               </div>
            )}
         </div>
      );
   };

   const renderAnalysisTab = () => {
      return (
         <div className="flex flex-col gap-10 px-6">
            {entities.map(en => {
               const items = analysisData[en] || [];
               const subjective = items.filter(r => r.type === 'subjective');
               const conflicts = items.filter(r => r.type === 'conflict');

               if (subjective.length === 0 && conflicts.length === 0) return null;

               return (
                  <div key={en} className="mb-8">
                     <h4 className="text-cyan-400 font-oswald uppercase tracking-widest mb-6 flex items-center gap-2">
                        <BarChart3 size={18} /> {en} Perspective Analysis
                     </h4>
                     
                     {conflicts.length > 0 && (
                        <div className="mb-8 space-y-4">
                           <h5 className="text-[10px] font-black uppercase tracking-widest text-red-400/80">Factual Conflicts</h5>
                           {conflicts.map((c, i) => (
                              <div key={i} className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
                                 <div className="text-[11px] font-bold text-slate-400 uppercase mb-2">{c.aspect}</div>
                                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {c.conflicting_values.map((cv, idx) => (
                                       <div key={idx} className="flex flex-col">
                                          <div className="text-sm text-slate-200">{formatSpecValue(cv.value)}</div>
                                          <div className="text-[10px] text-slate-500">{formatUrlText(cv.source)}</div>
                                       </div>
                                    ))}
                                 </div>
                              </div>
                           ))}
                        </div>
                     )}

                     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {subjective.map((r, k) => (
                           <div key={k} className={`bg-slate-900/60 border border-white/5 rounded-xl p-5 shadow-lg ${r.score >= 0 ? 'border-t-2 border-t-emerald-500' : 'border-t-2 border-t-red-500'}`}>
                              <div className="flex justify-between items-center mb-3">
                                 <span className="bg-slate-700/60 px-2 py-0.5 rounded text-[10px] font-bold uppercase text-slate-400">{r.aspect}</span>
                                 <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${r.score >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{getSentimentTier(r.score)}</span>
                              </div>
                              <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed">"{r.text}"</p>
                           </div>
                        ))}
                     </div>
                  </div>
               );
            })}
         </div>
      );
   };

   return (
      <div className="w-full animate-fade-in-up">
         <div className="glass-panel w-full max-w-5xl mx-auto transition-all duration-500 relative pb-12 overflow-hidden">
            
            {/* AI EXECUTIVE SUMMARY */}
            {q.aiSummary && (
               <div className="mx-6 mt-8 mb-4 p-6 bg-cyan-500/5 border border-cyan-500/20 rounded-2xl relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.8)]" />
                  <div className="flex items-center gap-2 mb-3">
                     <Terminal size={14} className="text-cyan-400" />
                     <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-400/80">Executive Overview</h5>
                  </div>
                  <div className="text-slate-200 text-sm leading-relaxed font-inter italic space-y-4">
                     {q.aiSummary.split('\n\n').map((paragraph, i) => (
                        <p key={i}>
                           {paragraph.split('\n').map((line, j) => {
                              const trimmed = line.trim();
                              if (trimmed.startsWith('- ') || trimmed.startsWith('•') || trimmed.match(/^\d\./)) {
                                 return <span key={j} className="block pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-cyan-500 mb-1">{trimmed.replace(/^[-•]\s*|^\d\.\s*/, '')}</span>;
                              }
                              return <span key={j} className="block mb-2">{line}</span>;
                           })}
                        </p>
                     ))}
                  </div>
               </div>
            )}

            {/* TAB NAVIGATION */}
            <div className="flex justify-center mb-10 mt-6">
               <div className="bg-slate-900/80 p-1 rounded-xl border border-white/10 flex gap-1">
                  {[
                     { id: 'facts', label: 'Facts', icon: Database },
                     { id: 'research', label: 'Research & News', icon: BookOpen },
                     { id: 'analysis', label: 'Analysis', icon: BarChart3 }
                  ].map(tab => (
                     <button
                        key={tab.id}
                        onClick={() => toggleTab(index, tab.id)}
                        className={`flex items-center gap-2 px-6 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${currentTab === tab.id ? 'bg-cyan-500 text-[#040a19] shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'text-slate-500 hover:text-slate-300'}`}
                     >
                        <tab.icon size={14} />
                        {tab.label}
                     </button>
                  ))}
               </div>
            </div>

            {/* TAB CONTENT */}
            <div className="w-full">
               {currentTab === 'facts' && <div className="animate-in fade-in slide-in-from-bottom-2">{renderFactsTable()}</div>}
               {currentTab === 'research' && <div className="animate-in fade-in slide-in-from-bottom-2">{renderResearchList()}</div>}
               {currentTab === 'analysis' && <div className="animate-in fade-in slide-in-from-bottom-2">{renderAnalysisTab()}</div>}
            </div>
         </div>
      </div>
   );
};

export default ResultHandler;
