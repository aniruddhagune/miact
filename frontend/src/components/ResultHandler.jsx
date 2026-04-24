import React from "react";
import { Loader, Terminal, Link as LinkIcon, AlertTriangle } from "lucide-react";

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

   if (!q.results && q.status !== "Done") {
      return (
         <div className="glass-panel flex items-center gap-3 text-slate-400 p-5 w-auto font-inter">
            <Loader className="animate-spin" size={24} />
            <span>{q.status}</span>
         </div>
      );
   }

   if (!q.results) return null;

   const allObjective = [];
   const allSubjective = [];
   const allScores = [];
   const entities = Object.keys(q.results);

   entities.forEach(en => {
      const records = q.results[en];
      records.forEach(r => {
         if (r.type === 'table' || r.type === 'conflict') allObjective.push({ ...r, entity: en });
         else if (r.type === 'score') allScores.push({ ...r, entity: en });
         else if (r.type === 'subjective' && r.score !== null && r.score !== 0) allSubjective.push({ ...r, entity: en });
      });
   });

   const objSeen = new Set();
   const dedupedObjective = allObjective.filter(r => {
      const key = `${r.aspect}|||${String(r.value || '').toLowerCase().trim()}|||${r.type}`;
      if (objSeen.has(key)) return false;
      objSeen.add(key);
      return true;
   });
   const aspectMap = {};
   dedupedObjective.forEach(r => {
      if (!aspectMap[r.aspect]) aspectMap[r.aspect] = {};
      aspectMap[r.aspect][r.entity] = r;
   });
   const aspectKeys = Object.keys(aspectMap);

   const scoreMap = {};
   const subjectiveMap = {};
   entities.forEach(en => {
      scoreMap[en] = [];
      const rawSubjective = allSubjective.filter(r => r.entity === en);
      const TANGIBLE_TERMS = ["feel", "build", "performance", "speed", "camera", "battery", "display", "screen", "price", "value"];
      const factAspects = Object.keys(aspectMap);

      const sorted = rawSubjective.sort((a, b) => {
         const aAsp = a.aspect.toLowerCase();
         const bAsp = b.aspect.toLowerCase();
         const aIsFact = factAspects.includes(aAsp);
         const bIsFact = factAspects.includes(bAsp);
         if (aIsFact !== bIsFact) return aIsFact ? -1 : 1;
         const aIsTangible = TANGIBLE_TERMS.some(t => aAsp.indexOf(t) !== -1);
         const bIsTangible = TANGIBLE_TERMS.some(t => bAsp.indexOf(t) !== -1);
         if (aIsTangible !== bIsTangible) return aIsTangible ? -1 : 1;
         return 0;
      });
      subjectiveMap[en] = sorted;
   });

   allScores.forEach(r => scoreMap[r.entity].push(r));
   const currentTab = q.resultTab || 'facts';

   const getAspectLabel = (asp, entity) => {
      const item = aspectMap[asp][entity];
      const multiPerspective = ["ai highlights", "summary", "brief summary", "updates"];
      if (multiPerspective.includes(asp.toLowerCase()) && item?.source) {
         let label = `${asp} (${formatUrlText(item.source)})`;
         if (item.date) {
            label += ` - ${item.date}`;
         }
         return label;
      }
      return asp;
   };

   return (
      <div className="w-full animate-fade-in-up">
         <div className="glass-panel w-full max-w-5xl mx-auto transition-all duration-500 relative pb-12 overflow-hidden">
            
            {/* AI SUMMARY SECTION */}
            {q.aiSummary && (
               <div className="mx-6 mt-8 mb-4 p-6 bg-cyan-500/5 border border-cyan-500/20 rounded-2xl relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.8)]" />
                  <div className="flex items-center gap-2 mb-3">
                     <Terminal size={14} className="text-cyan-400" />
                     <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-400/80">AI Executive Summary</h5>
                  </div>
                  <p className="text-slate-200 text-sm leading-relaxed font-inter italic">
                     {q.aiSummary}
                  </p>
               </div>
            )}

            <div className="flex justify-center mb-10">
               <div className="pill-container">
                  <div className="pill-indicator" style={{ transform: `translateX(${currentTab === 'facts' ? '0' : '100%'})` }} />
                  <button onClick={() => toggleTab(index, 'facts')} className={`pill-button ${currentTab === 'facts' ? 'active' : 'inactive'}`}>Facts</button>
                  <button onClick={() => toggleTab(index, 'opinions')} className={`pill-button ${currentTab === 'opinions' ? 'active' : 'inactive'}`}>Opinions</button>
               </div>
            </div>

            <div className="w-full">
               {currentTab === 'facts' ? (
                  <div key="facts-panel" className="w-full animate-fade-in-up">
                     <div className="overflow-x-auto w-full px-6">
                        <table className="w-full text-left border-collapse font-inter">
                           <thead>
                              <tr>
                                 <th className="bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] rounded-tl-xl border-b border-white/5 w-[20%]">Aspect</th>
                                 {entities.map((en, i) => (
                                    <th key={en} className={`bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] border-b border-white/5 ${i === entities.length - 1 ? 'rounded-tr-xl' : ''}`}>{en}</th>
                                 ))}
                              </tr>
                           </thead>
                           <tbody>
                              {(() => {
                                 const rows = [];
                                 const renderedAspects = new Set();
                                 const isTech = q.parsed?.query_type?.startsWith("tech");
                                 const isNews = q.parsed?.mode === "news";
                                 
                                 let GROUPS = configGroups ? (isTech ? configGroups.tech : configGroups.general) : {};
                                 if (isNews && configGroups?.news) GROUPS = configGroups.news;
                                 
                                 const groupOrder = Object.keys(GROUPS);

                                 groupOrder.forEach(groupName => {
                                    const groupKeys = GROUPS[groupName];
                                    const matchingAspects = aspectKeys.filter(asp => (groupKeys.includes(asp.toLowerCase()) || asp.toLowerCase().includes(groupName.toLowerCase().split(' ')[0])) && !renderedAspects.has(asp));
                                    if (matchingAspects.length > 0) {
                                       rows.push(<tr key={`header-${groupName}`} className="spec-category-header"><td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-cyan-400/80 border-none">{groupName}</td></tr>);
                                       matchingAspects.forEach(asp => {
                                          renderedAspects.add(asp);
                                          rows.push(
                                             <tr key={asp} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                                                <td className="py-4 pl-8 pr-6 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400 w-1/4">
                                                   {getAspectLabel(asp, entities[0])}
                                                </td>
                                                {entities.map(en => (
                                                   <td key={en} className="py-4 px-6 text-sm text-slate-200">
                                                      {aspectMap[asp][en] ? (
                                                         aspectMap[asp][en].type === 'conflict' ? (
                                                            <div className="flex flex-col gap-2 p-2 bg-red-500/5 border border-red-500/20 rounded-lg">
                                                               <div className="flex items-center gap-2 text-red-400 font-bold text-[10px] uppercase tracking-wider">
                                                                  <AlertTriangle size={12} /> Conflict Detected
                                                               </div>
                                                               <div className="flex flex-col gap-1">
                                                                  {aspectMap[asp][en].conflicting_values.map((cv, idx) => (
                                                                     <div key={idx} className="flex items-center justify-between gap-4 group/cv">
                                                                        <span className="text-slate-300 text-xs">{formatSpecValue(cv.value)}</span>
                                                                        <a href={cv.source} target="_blank" rel="noreferrer" className="text-[10px] text-slate-500 hover:text-cyan-400 transition-colors bg-white/5 px-1.5 py-0.5 rounded">
                                                                           {formatUrlText(cv.source)}
                                                                        </a>
                                                                     </div>
                                                                  ))}
                                                               </div>
                                                            </div>
                                                         ) : (
                                                            <div className="flex items-center gap-2 group/cell">
                                                               {formatSpecValue(`${aspectMap[asp][en].value} ${aspectMap[asp][en].unit || ''}`)}
                                                               {aspectMap[asp][en].source && (
                                                                  <a href={getEnhancedUrl(aspectMap[asp][en].source, `${asp} ${aspectMap[asp][en].value}`)} target="_blank" rel="noreferrer" className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-cyan-400"><LinkIcon size={12} /></a>
                                                               )}
                                                            </div>
                                                         )
                                                      ) : '-'}
                                                   </td>

                                                ))}
                                             </tr>
                                          );
                                       });
                                    }
                                 });

                                 const otherAspects = aspectKeys.filter(asp => !renderedAspects.has(asp));
                                 if (otherAspects.length > 0) {
                                    rows.push(<tr key="header-other" className="spec-category-header"><td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 border-none">Additional Details</td></tr>);
                                    otherAspects.forEach(asp => {
                                       rows.push(
                                          <tr key={asp} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                                             <td className="py-4 pl-8 pr-6 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400 w-1/4">
                                                {getAspectLabel(asp, entities[0])}
                                             </td>
                                             {entities.map(en => (
                                                <td key={en} className="py-4 px-6 text-sm text-slate-200">
                                                   {aspectMap[asp][en] ? (
                                                      aspectMap[asp][en].type === 'conflict' ? (
                                                         <div className="flex flex-col gap-2 p-2 bg-red-500/5 border border-red-500/20 rounded-lg">
                                                            <div className="flex items-center gap-2 text-red-400 font-bold text-[10px] uppercase tracking-wider">
                                                               <AlertTriangle size={12} /> Conflict Detected
                                                            </div>
                                                            <div className="flex flex-col gap-1">
                                                               {aspectMap[asp][en].conflicting_values.map((cv, idx) => (
                                                                  <div key={idx} className="flex items-center justify-between gap-4 group/cv">
                                                                     <span className="text-slate-300 text-xs">{formatSpecValue(cv.value)}</span>
                                                                     <a href={cv.source} target="_blank" rel="noreferrer" className="text-[10px] text-slate-500 hover:text-cyan-400 transition-colors bg-white/5 px-1.5 py-0.5 rounded">
                                                                        {formatUrlText(cv.source)}
                                                                     </a>
                                                                  </div>
                                                               ))}
                                                            </div>
                                                         </div>
                                                      ) : formatSpecValue(`${aspectMap[asp][en].value} ${aspectMap[asp][en].unit || ''}`)
                                                   ) : '-'}
                                                </td>
                                             ))}
                                          </tr>
                                       );
                                    });
                                 }
                                 return rows;
                              })()}
                           </tbody>
                        </table>
                     </div>
                  </div>
               ) : (
                  <div key="opinions-panel" className="w-full animate-fade-in-up px-4">
                     <div className="flex flex-col gap-10">
                        {entities.map(en => (
                           <div key={en} className="mb-8">
                              <h4 className="text-cyan-400 font-oswald uppercase tracking-widest mb-4 px-4">{en} Impressions</h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 px-4">
                                 {subjectiveMap[en].map((r, k) => (
                                    <div key={k} className={`opinion-card bg-slate-900/60 border border-white/5 rounded-xl p-5 flex flex-col shadow-lg transition-transform hover:-translate-y-1 ${r.score >= 0 ? 'border-t-2 border-t-emerald-500' : 'border-t-2 border-t-red-500'}`}>
                                       <div className="flex justify-between items-center mb-3">
                                          <span className="bg-slate-700/60 px-2 py-0.5 rounded text-[10px] font-bold uppercase text-slate-400">{r.aspect}</span>
                                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${r.score >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{getSentimentTier(r.score)}</span>
                                       </div>
                                       <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed flex-1">"{r.text}"</p>
                                    </div>
                                 ))}
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
               )}
            </div>
         </div>
      </div>
   );
};

export default ResultHandler;
