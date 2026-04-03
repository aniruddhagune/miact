import React, { useState, useRef, useEffect, Component } from "react";
import "./App.css";
import { ArrowRight, Loader, ChevronLeft, History, Link as LinkIcon } from "lucide-react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, errorMessage: error.toString() };
  }
  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught localized rendering crash:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
         <div className="w-full bg-red-900/40 border border-red-500/50 p-6 rounded-xl shadow-lg mt-4 font-mono text-sm">
            <h3 className="text-red-400 mb-2 font-bold uppercase tracking-wider">Rendering Fault Detected</h3>
            <p className="text-slate-300 break-words">{this.state.errorMessage}</p>
         </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(240);
  const isResizing = useRef(false);

  const [activeChat, setActiveChat] = useState(0);
  const [queries, setQueries] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Sources Card
  const [showSourcesPopup, setShowSourcesPopup] = useState(false);
  const [activeSourceTab, setActiveSourceTab] = useState(null);
  const sourcesPopupRef = useRef(null);
  const sourcesToggleRef = useRef(null);

  const containerRef = useRef(null);

  // Sync sources tab with active chat
  useEffect(() => {
     const q = queries[activeChat];
     if (q && q.urls && Object.keys(q.urls).length > 0) {
         const entities = Object.keys(q.urls);
         if (!entities.includes(activeSourceTab)) {
            setActiveSourceTab(entities[0]);
         }
     } else {
         setActiveSourceTab(null);
     }
  }, [activeChat, queries]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      let newWidth = e.clientX;
      if (newWidth < 72) newWidth = 72;
      if (newWidth > 500) newWidth = 500;
      setSidebarWidth(newWidth);
      
      if (newWidth < 120) {
         setSidebarOpen(false);
      } else {
         setSidebarOpen(true);
      }
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      setIsDragging(false);
      document.body.style.cursor = 'default';
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // Close sources popup on click-outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        showSourcesPopup &&
        sourcesPopupRef.current &&
        !sourcesPopupRef.current.contains(e.target) &&
        sourcesToggleRef.current &&
        !sourcesToggleRef.current.contains(e.target)
      ) {
        setShowSourcesPopup(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showSourcesPopup]);

  const handleToggleSidebar = () => {
     if (!sidebarOpen) {
        if (sidebarWidth < 120) setSidebarWidth(240);
        setSidebarOpen(true);
     } else {
        setSidebarOpen(false);
     }
  };

  const sendQuery = async () => {
    if (!input.trim() || loading) return;

    const queryText = input;
    setLoading(true);
    setInput("");

    const newQueryIndex = queries.length;
    setQueries(prev => [...prev, {
      query_text: queryText,
      parsed: null,
      urls: null,
      results: null,
      status: "Starting connection...",
      error: null
    }]);
    
    setActiveChat(newQueryIndex);
    setShowSourcesPopup(false);

    const es = new EventSource(`http://127.0.0.1:8000/search?query=${encodeURIComponent(queryText)}&t=${Date.now()}`);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.step === "result") {
          es.close();
          setLoading(false);
          if (data.urls && Object.keys(data.urls).length > 0) {
             setShowSourcesPopup(true);
          }
        }

        setQueries(prev => {
          const next = [...prev];
          const q = { ...next[newQueryIndex] };
          
          if (data.step === "parsed") {
            q.parsed = data.parsed;
            q.status = "Parsed query...";
          } else if (data.step === "urls_extracted") {
            q.urls = data.urls;
            q.status = "Analyzing URLs...";
          } else if (data.step === "partial") {
            q.status = `Processing: ${data.url}...`;
          } else if (data.step === "result") {
            q.results = data.results;
            q.urls = data.urls || q.urls;
            q.parsed = data.parsed || q.parsed;
            q.status = "Done";
          }
          
          next[newQueryIndex] = q;
          return next;
        });
      } catch (err) {
        console.error("Error parsing SSE message:", err);
      }
    };

    es.onerror = (error) => {
      console.error("EventSource failed:", error);
      es.close();
      setLoading(false);
      setQueries(prev => {
        const next = [...prev];
        if (next[newQueryIndex].results || next[newQueryIndex].status === "Done") {
          return next;
        }
        next[newQueryIndex] = { ...next[newQueryIndex], error: "Backend communication complete or connection error.", status: "Done" };
        return next;
      });
    };
  };

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [queries]);

  const getSentimentTier = (score) => {
    if (score === null || score === undefined || score === 0) return null;
    const s = Math.abs(score);
    const polarity = score > 0 ? "Positive" : "Negative";
    if (s <= 0.25) return `Slightly ${polarity}`;
    if (s <= 0.50) return `Moderately ${polarity}`;
    if (s <= 0.75) return `Extremely ${polarity}`;
    return `Overwhelmingly ${polarity}`;
  };

  const formatUrlText = (urlStr) => {
    try {
      const u = new URL(urlStr);
      let domain = u.hostname.replace('www.', '');
      let path = u.pathname.split('/').filter(Boolean).pop() || '';
      path = path.replace(/[-_]/g, ' ').replace('.html', '').replace('.php', '');
      
      const hasNumbers = /\d.*\d/.test(path);
      if (!path || path.toLowerCase() === domain.toLowerCase() || hasNumbers || path.length > 35) {
         return `${domain.charAt(0).toUpperCase() + domain.slice(1)}`;
      }
      return `${domain.charAt(0).toUpperCase() + domain.slice(1)} - ${decodeURIComponent(path)}`;
    } catch {
      return urlStr;
    }
  };

  const formatSpecValue = (val) => {
    if (!val) return null;
    const strVal = String(val);
    // Protect thousands-separator commas: "32,999" should NOT split
    // Only split on commas that are list separators (followed by a space or after non-digit)
    const splitSafe = strVal.split(/(?<=\D),\s*|,\s+(?=\D)/);
    const parts = splitSafe.length > 1 ? splitSafe : [strVal];
    if (parts.length === 1) {
        // Single value — split major/minor on parenthetical
        const match = strVal.match(/^([^(]+)(?:\s*\(([^)]+)\))?$/);
        if (match) {
            const major = match[1].trim();
            const minor = match[2] ? `(${match[2]})` : null;
            return (
                <span>
                    <span className="text-major">{major}</span>
                    {minor && <span className="text-minor"> {minor}</span>}
                </span>
            );
        }
        return <span className="text-major">{strVal}</span>;
    }
    // Multiple parts — render as stacked
    return (
        <span className="flex flex-col gap-0.5">
            {parts.map((p, i) => {
                const m = p.trim().match(/^([^(]+)(?:\s*\(([^)]+)\))?$/);
                if (m) {
                    return (
                        <span key={i}>
                            <span className="text-major">{m[1].trim()}</span>
                            {m[2] && <span className="text-minor"> ({m[2]})</span>}
                        </span>
                    );
                }
                return <span key={i} className="text-major">{p.trim()}</span>;
            })}
        </span>
    );
  };

  // Detect aspects that should use '/' inline joining (bands, freq-style, simple lists)
  const isBandAspect = (asp) => /bands?|frequency|freq|lte|gsm|wcdma|hspa|nr|5g|4g|3g|2g/i.test(asp);

  const renderResults = (q) => {
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
            if (r.type === 'table') allObjective.push({ ...r, entity: en });
            else if (r.type === 'score') allScores.push({ ...r, entity: en });
            else if (r.type === 'subjective' && r.score !== null && r.score !== 0) allSubjective.push({ ...r, entity: en });
        });
    });

    // Frontend deduplication: remove exact (aspect, value) copies across sources
    const objSeen = new Set();
    const dedupedObjective = allObjective.filter(r => {
        const key = `${r.aspect}|||${String(r.value).toLowerCase().trim()}`;
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
       
       // Sort Subjective opinions for this entity
       const rawSubjective = allSubjective.filter(r => r.entity === en);
       
       // Prioritization logic
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

    return (
      <div className="w-full flex justify-center animate-fade-in-up">
         <div className="glass-panel w-full max-w-5xl transition-all duration-500 pb-8">
            <div className="w-full text-center pb-6">
                <h4 className="text-[28px] font-oswald text-slate-300 font-medium uppercase tracking-[0.2em] relative before:content-[''] before:absolute before:w-[60px] before:h-px before:bg-slate-600 before:right-full before:top-1/2 before:mr-4 after:content-[''] after:absolute after:w-[60px] after:h-px after:bg-slate-600 after:left-full after:top-1/2 after:ml-4 inline-block">FACTS</h4>
            </div>
            
            <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse font-inter">
                   <thead>
                     <tr>
                       <th className="bg-slate-700/50 p-3 text-slate-300 text-sm font-bold uppercase tracking-wider rounded-tl-xl border-b border-white/5 w-[20%]">Aspect</th>
                       {entities.map((en, i) => (
                          <th 
                             key={en}
                             className={`bg-slate-700/50 p-3 text-slate-300 text-sm font-bold uppercase tracking-wider border-b border-white/5 ${i===entities.length-1?'rounded-tr-xl':''}`}
                          >
                             {en}
                          </th>
                       ))}
                     </tr>
                   </thead>
                   <tbody>
                      {aspectKeys.map((asp, i) => (
                         <tr key={i} className="hover:bg-white/5 transition-colors duration-200">
                            <td className="p-4 border-b border-white/5 capitalize font-semibold text-slate-300">{asp}</td>
                            {entities.map(en => {
                               const rec = aspectMap[asp][en];
                               return (
                                  <td 
                                     key={en} 
                                     className="p-4 border-b border-white/5 font-mono text-emerald-400"
                                  >
                                      {rec ? (
                                         <div className="flex flex-col gap-1">
                                            {(() => {
                                               const raw = `${rec.value} ${rec.unit || ''}`.trim();
                                               const parts = raw.split(/(?:,\s*|\s*\+\s*)/).filter(Boolean).map(s => s.trim());
                                               // For band-like aspects, join inline with '/'
                                               if (isBandAspect(rec.aspect) || parts.length > 3) {
                                                 return (
                                                   <span className="group relative">
                                                     {formatSpecValue(parts.join(' / '))}
                                                     {rec.source && (
                                                        <a href={rec.source} target="_blank" rel="noreferrer" title={rec.source} className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 text-slate-500 hover:text-blue-400 inline-block align-middle">
                                                           <LinkIcon size={12} className="inline" />
                                                        </a>
                                                     )}
                                                   </span>
                                                 );
                                               }
                                               return parts.map((item, idx) => (
                                                   <div key={idx} className="block w-full group relative">
                                                      {formatSpecValue(item)}
                                                      {rec.source && (
                                                         <a href={rec.source} target="_blank" rel="noreferrer" title={rec.source} className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 text-slate-500 hover:text-blue-400 inline-block align-middle">
                                                            <LinkIcon size={12} className="inline" />
                                                         </a>
                                                      )}
                                                   </div>
                                               ));
                                            })()}
                                         </div>
                                      ) : '-'}
                                  </td>
                               );
                            })}
                         </tr>
                      ))}
                                          {/* Opinions Section - below table, separate layout */}
                       {allSubjective.length > 0 && (
                          <>
                             <tr>
                                <td colSpan={entities.length + 1} className="pt-10 pb-2 border-none text-center">
                                   <h4 className="text-[28px] font-oswald text-slate-300 font-medium uppercase tracking-[0.2em] relative before:content-[''] before:absolute before:w-[60px] before:h-px before:bg-slate-600 before:right-full before:top-1/2 before:mr-4 after:content-[''] after:absolute after:w-[60px] after:h-px after:bg-slate-600 after:left-full after:top-1/2 after:ml-4 inline-block">OPINIONS</h4>
                                </td>
                             </tr>
                             <tr>
                                <td colSpan={entities.length + 1} className="border-none pt-2 pb-8 px-2">
                                   {(() => {
                                      // Collect all valid scores and group cards by canonical aspect
                                      const MEANINGFUL_SCORE_ASPECTS = new Set([
                                         "camera", "cameras", "battery", "display", "screen", "performance",
                                         "build", "design", "software", "charging", "speakers", "audio",
                                         "speed", "value", "price", "overall", "gaming",
                                         "photography", "connectivity", "storage", "graphics"
                                      ]);

                                      // Build map: aspect -> { score, cards[] }
                                      const aspectScoreMap = {};
                                      entities.forEach(en => {
                                         scoreMap[en].forEach(s => {
                                            const asp = s.aspect.toLowerCase();
                                            if (!MEANINGFUL_SCORE_ASPECTS.has(asp)) return;
                                            if (!aspectScoreMap[asp]) aspectScoreMap[asp] = { value: s.value, cards: [] };
                                            else aspectScoreMap[asp].value = Math.max(aspectScoreMap[asp].value, s.value);
                                         });
                                         subjectiveMap[en].forEach(r => {
                                            const tier = getSentimentTier(r.score);
                                            if (!tier) return;
                                            const asp = r.aspect.toLowerCase();
                                            const target = aspectScoreMap[asp];
                                            if (target) target.cards.push({ ...r, entityLabel: en });
                                         });
                                      });

                                      // Unmapped cards — show in "Other" if they seem to be about something
                                      const mappedAspects = new Set(Object.keys(aspectScoreMap));
                                      const NOISE_WORDS = new Set(["it", "this", "that", "there", "here", "they", "we", "he", "she"]);
                                      const otherCards = entities.flatMap(en =>
                                         subjectiveMap[en].filter(r => {
                                            if (!getSentimentTier(r.score)) return false;
                                            if (mappedAspects.has(r.aspect.toLowerCase())) return false;
                                            // Only include if the text has at least one meaningful noun
                                            const words = r.text.toLowerCase().split(/\s+/);
                                            return words.some(w => w.length > 4 && !NOISE_WORDS.has(w));
                                         }).map(r => ({ ...r, entityLabel: en }))
                                      ).slice(0, 6);

                                      const aspectRows = Object.entries(aspectScoreMap);

                                      return (
                                         <div className="flex flex-col gap-8">
                                            {aspectRows.map(([asp, data]) => (
                                               <div key={asp} className="flex gap-6 items-start">
                                                  {/* LEFT: sub-heading + score */}
                                                  <div className="shrink-0 w-28 flex flex-col items-center pt-2">
                                                     <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 text-center">{asp}</span>
                                                     <span className={`text-[22px] font-mono font-black ${
                                                        data.value >= 7 ? 'text-emerald-400' :
                                                        data.value >= 4 ? 'text-yellow-400' : 'text-red-400'
                                                     }`}>{data.value}<span className="text-sm text-slate-500 font-bold">/10</span></span>
                                                  </div>
                                                  {/* RIGHT: horizontally scrollable cards */}
                                                  <div className="flex-1 overflow-x-auto custom-scrollbar pb-2">
                                                     <div className="flex gap-4" style={{ minWidth: 'max-content' }}>
                                                        {data.cards.length === 0 ? (
                                                           <div className="text-slate-500 italic text-sm flex items-center h-full px-2">No opinions found.</div>
                                                        ) : data.cards.map((r, k) => {
                                                           const tier = getSentimentTier(r.score);
                                                           const isPos = r.score > 0;
                                                           const isUser = r.metadata?.user_review;
                                                           return (
                                                              <div key={k} className={`w-72 shrink-0 bg-slate-900/60 border border-white/5 rounded-xl p-4 flex flex-col shadow-lg transition-transform duration-300 hover:-translate-y-1 ${
                                                                 isPos ? 'border-t-[3px] border-t-emerald-500' : 'border-t-[3px] border-t-red-500'
                                                              }`}>
                                                                 <div className="flex justify-between items-center mb-2">
                                                                    <div className="flex gap-2">
                                                                       {entities.length > 1 && r.entityLabel && (
                                                                          <span className="bg-slate-700/60 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tight text-slate-400">{r.entityLabel.split(' ').slice(-1)[0]}</span>
                                                                       )}
                                                                       {isUser && <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tighter border border-blue-500/30">User</span>}
                                                                    </div>
                                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                                                                       isPos ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                                                                    }`}>{tier}</span>
                                                                 </div>
                                                                 <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed font-inter">"{r.text}"</p>
                                                              </div>
                                                           );
                                                        })}
                                                     </div>
                                                  </div>
                                               </div>
                                            ))}

                                            {/* Other Opinions row */}
                                            {otherCards.length > 0 && (
                                               <div className="flex gap-6 items-start">
                                                  <div className="shrink-0 w-28 flex flex-col items-center pt-2">
                                                     <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 text-center">Other</span>
                                                  </div>
                                                  <div className="flex-1 overflow-x-auto custom-scrollbar pb-2">
                                                     <div className="flex gap-4" style={{ minWidth: 'max-content' }}>
                                                        {otherCards.map((r, k) => {
                                                           const tier = getSentimentTier(r.score);
                                                           const isPos = r.score > 0;
                                                           return (
                                                              <div key={k} className={`w-72 shrink-0 bg-slate-900/60 border border-white/5 rounded-xl p-4 flex flex-col shadow-lg transition-transform duration-300 hover:-translate-y-1 ${
                                                                 isPos ? 'border-t-[3px] border-t-emerald-500' : 'border-t-[3px] border-t-red-500'
                                                              }`}>
                                                                 <div className="flex justify-between items-center mb-2">
                                                                    <span className="bg-slate-800/80 px-3 py-1 rounded-full text-xs font-semibold capitalize text-slate-300">{r.aspect}</span>
                                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                                                                       isPos ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                                                                    }`}>{tier}</span>
                                                                 </div>
                                                                 <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed font-inter">"{r.text}"</p>
                                                              </div>
                                                           );
                                                        })}
                                                     </div>
                                                  </div>
                                               </div>
                                            )}
                                         </div>
                                      );
                                   })()}
                                </td>
                             </tr>
                          </>
                       )}
                   </tbody>
                </table>
            </div>
         </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden text-white font-inter bg-[radial-gradient(circle_at_top_left,#283347,#040a19)]">
      
      {/* Left Sidebar */}
      <div 
         className={`relative flex flex-col bg-[#111] z-10 pt-4 pb-0 ${isDragging ? '' : 'transition-[width] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]'}`} 
         style={{ width: sidebarOpen ? sidebarWidth : 72 }}
      >
        <div className="flex flex-col flex-1 overflow-hidden px-3">
          <div className="flex items-center overflow-hidden min-h-[30px] mb-4 pl-[8px] w-full relative">
            <button className="p-[2px] flex items-center justify-center rounded-md hover:bg-white/10 transition-colors cursor-pointer shrink-0 z-10" onClick={handleToggleSidebar}>
              {sidebarOpen ? <ChevronLeft size={26} className="text-white" /> : <History size={26} className="text-white" />}
            </button>
            <h3 
               className={`font-oswald whitespace-nowrap transition-all duration-200 font-medium uppercase tracking-widest m-0 text-center absolute left-0 right-0 pointer-events-none ${sidebarOpen && sidebarWidth > 140 ? "opacity-100" : "opacity-0"}`}
               style={{ fontSize: '20px' }}
            >
              History
            </h3>
          </div>
          
          <div className={`h-px bg-gray-600 mb-4 mx-1 transition-opacity ${sidebarOpen?'opacity-100':'opacity-50'}`}></div>
          
          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar w-full">
            {queries.map((q, i) => (
              <div
                key={i}
                className={`cursor-pointer overflow-hidden transition-all duration-300 ease-in-out font-inter w-full text-center
                  ${i === activeChat 
                     ? "bg-gray-900 border-none text-white px-3 min-h-[40px] shadow-inner flex items-center justify-center truncate" 
                     : (sidebarOpen ? "text-gray-400 hover:bg-gray-800 hover:text-white p-2 min-h-[40px] truncate flex items-center justify-center" : "text-gray-400 flex items-center justify-center p-2")
                  }`}
                onClick={() => setActiveChat(i)}
                title={q.query_text}
              >
                {sidebarOpen ? (
                    <span className="truncate w-full block">{q.query_text}</span>
                 ) : (
                    <span>&bull;</span>
                 )}
              </div>
            ))}
          </div>
        </div>

        {/* Resizer Handle */}
        <div 
           className="absolute top-0 -right-[3px] w-[6px] h-full cursor-col-resize z-20 hover:bg-blue-400/50 transition-colors"
           onMouseDown={(e) => {
             isResizing.current = true;
             setIsDragging(true);
             document.body.style.cursor = 'col-resize';
           }}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative min-w-0">
         <div ref={containerRef} className="flex-1 overflow-y-auto p-10 pb-[140px] flex flex-col items-center">
            
            {/* Absolute Centered Welcome Banner */}
            <div className={`absolute left-0 right-0 top-[35%] flex justify-center pointer-events-none px-4 text-center ${queries.length === 0 ? 'animate-welcome-in' : 'animate-welcome-out'}`}>
                  <h1 className="text-5xl md:text-7xl xl:text-[6rem] font-oswald text-white uppercase tracking-[0.1em] drop-shadow-2xl welcome-glow">
                     Welcome, Seeker
                  </h1>
            </div>
            
            {/* Session Mapping */}
            <div className="w-full flex flex-col items-center z-10">
               {queries.map((q, i) => (
                 <div key={i} className="w-full flex flex-col items-center mb-8 animate-fade-in-up">
                   <div className="px-6 py-2 rounded-full bg-[#111] border border-gray-600 font-inter text-slate-300 font-medium text-sm w-fit max-w-[95%] mb-5 shadow-[0_2px_10px_rgba(0,0,0,0.3)]">
                     {q.query_text}
                   </div>
                   <div className="w-full max-w-[1000px]">
                     <ErrorBoundary>
                       {renderResults(q)}
                     </ErrorBoundary>
                   </div>
                 </div>
               ))}
            </div>
         </div>

        {/* Floating Top-Right ! Sources Toggle Button */}
        <button 
           ref={sourcesToggleRef}
           className={`absolute top-6 right-8 w-12 h-12 flex justify-center items-center bg-[#111] rounded-full shadow-[0_5px_15px_rgba(0,0,0,0.5)] border border-[#222] transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] z-[999] hover:bg-[#222] ${!showSourcesPopup && queries[activeChat]?.urls && Object.keys(queries[activeChat].urls).length > 0 ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-75 pointer-events-none'}`}
           onClick={() => setShowSourcesPopup(true)}
        >
           <span className="font-oswald text-gray-300 font-bold text-3xl -mt-[2px]">!</span>
        </button>

        {/* Floating Sources Card (Tab interface) */}
        <div
           ref={sourcesPopupRef}
           className={`absolute top-6 right-8 w-[420px] max-h-[80vh] z-[100] flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.8)] border border-white/5 p-5 rounded-3xl bg-black/80 backdrop-blur-3xl transition-all duration-[350ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] ${showSourcesPopup && queries[activeChat]?.urls && activeSourceTab ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto' : 'opacity-0 scale-90 -translate-y-3 pointer-events-none origin-top-right'}`}
        >
            <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-2 relative">
               <h4 className="m-0 text-white font-oswald text-[28px] uppercase tracking-widest font-medium mx-auto">SOURCES</h4>
               <button onClick={() => setShowSourcesPopup(false)} className="absolute right-0 bg-transparent border-none text-slate-400 text-3xl hover:text-white cursor-pointer transition-colors leading-[0] outline-none mb-1">&times;</button>
            </div>

            {/* Entity Tabs */}
            {queries[activeChat]?.urls && (
               <>
                  {Object.keys(queries[activeChat].urls).length > 1 && (
                      <div className="flex gap-2 mb-4 overflow-x-auto custom-scrollbar border-b border-white/10">
                         {Object.keys(queries[activeChat].urls).map(en => (
                            <button 
                               key={en}
                               onClick={() => setActiveSourceTab(en)}
                               className={`whitespace-nowrap px-4 py-2 text-sm font-bold rounded-t-lg transition-all outline-none border-b-0 ${activeSourceTab === en ? 'bg-[#222]/80 text-white shadow-inner' : 'bg-black/60 text-slate-400 hover:bg-[#111] hover:text-white'}`}
                            >
                               {en}
                            </button>
                         ))}
                      </div>
                  )}

                  <div className="overflow-y-auto pr-2 custom-scrollbar">
                     <ul className="list-none p-0 m-0 ml-[4px] relative font-oswald">
                        {queries[activeChat].urls[activeSourceTab]?.urls?.map((u, i, arr) => {
                           const isLast = i === arr.length - 1;
                           return (
                              <li key={u} className="relative pl-[26px] mb-4 group flex items-center min-h-[30px]">
                                 {!isLast && <div className="absolute left-[5px] top-[24px] bottom-[-24px] w-[2px] bg-[#94a3b8] opacity-60"></div>}
                                 <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[12px] h-[12px] rounded-full shadow-[0_0_0_4px_rgba(15,23,42,1)] bg-[#94a3b8] z-10 transition-all duration-300"></div>
                                 <a href={u} target="_blank" rel="noreferrer" className="text-[#94a3b8] font-medium text-[16px] tracking-wide hover:text-white leading-relaxed break-words transition-colors duration-200 py-1 w-full inline-block">
                                    {formatUrlText(u)}
                                 </a>
                              </li>
                           );
                        })}
                     </ul>
                  </div>
               </>
            )}
        </div>

        {/* Input Bar */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-3xl flex items-center p-3 rounded-full bg-[#111] shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-white/10 z-50 transition-all duration-300 hover:shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
          <input
            className="flex-1 p-3 bg-transparent text-white font-inter border-none outline-none ml-2 text-md placeholder-slate-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendQuery();
            }}
            placeholder="Search, compare devices, or analyze news..."
            disabled={loading}
          />
          <button 
             onClick={sendQuery} 
             className="ml-2 w-12 h-12 rounded-full border-none bg-[#fff] text-[#111] hover:bg-slate-200 flex items-center justify-center cursor-pointer transition-all duration-300 active:scale-95 disabled:opacity-50 shadow-[0_0_15px_rgba(255,255,255,0.2)]"
             disabled={loading}
          >
            {loading ? <Loader className="animate-spin text-[#111]" size={24} /> : <ArrowRight className="text-[#111]" size={22} />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;