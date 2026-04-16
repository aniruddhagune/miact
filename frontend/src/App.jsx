import React, { useState, useEffect, useRef, useLayoutEffect, Component } from "react";
import "./App.css";
import { ArrowRight, Loader, ChevronLeft, History, Link as LinkIcon, Terminal } from "lucide-react";

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
   const [debugMode, setDebugMode] = useState(false);

   // Sources Card
   const [showSourcesPopup, setShowSourcesPopup] = useState(false);
   const [activeSourceTab, setActiveSourceTab] = useState(null);
   const sourcesPopupRef = useRef(null);
   const sourcesToggleRef = useRef(null);

   const containerRef = useRef(null);

   // Initialize Debug Mode from backend
   useEffect(() => {
     const fetchDebugMode = async () => {
       try {
         const response = await fetch("http://127.0.0.1:8000/api/debug");
         const data = await response.json();
         setDebugMode(data.debug);
       } catch (err) {
         console.error("Failed to fetch initial debug mode:", err);
       }
     };
     fetchDebugMode();
   }, []);

   const handleToggleDebug = async () => {
     const newDebugState = !debugMode;
     try {
       const response = await fetch("http://127.0.0.1:8000/api/debug", {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ debug: newDebugState }),
       });
       const data = await response.json();
       setDebugMode(data.debug);
       alert(`Debug mode ${data.debug ? "enabled" : "disabled"}. Check the console or server logs.`);
     } catch (err) {
       alert("Failed to toggle debug mode.");
     }
   };

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

   const handleClearCache = async () => {
     if (!window.confirm("Are you sure you want to clear the entire local database cache? This cannot be undone.")) return;
     try {
       const response = await fetch("http://127.0.0.1:8000/clear-db", { method: "POST" });
       const data = await response.json();
       if (data.status === "success") {
         alert("Cache cleared successfully!");
         setQueries([]);
         setActiveChat(0);
       } else {
         alert("Error clearing cache: " + data.message);
       }
     } catch (err) {
       alert("Failed to connect to backend to clear cache.");
     }
   };

   useEffect(() => {
     const handleMouseMove = (e) => {         if (!isResizing.current) return;
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

   const toggleTab = (queryIndex, tab) => {
      const updated = [...queries];
      updated[queryIndex].resultTab = tab;
      setQueries(updated);
   };

   // Attached Sources Logic: Sync activeChat with the visible result container
   useEffect(() => {
      const observer = new IntersectionObserver(
         (entries) => {
            entries.forEach((entry) => {
               if (entry.isIntersecting && entry.intersectionRatio > 0.4) {
                  const index = parseInt(entry.target.getAttribute('data-index'));
                  if (!isNaN(index)) {
                     setActiveChat(index);
                  }
               }
            });
         },
         { threshold: [0.1, 0.4, 0.7], rootMargin: '-10% 0px -20% 0px' }
      );

      const containers = document.querySelectorAll('.result-container');
      containers.forEach((el) => observer.observe(el));

      return () => observer.disconnect();
   }, [queries]);

   const getEnhancedUrl = (url, text) => {
      if (!url || !text) return url;
      try {
         const cleanText = text.replace(/["]/g, '').replace(/[\n\r]/g, ' ').trim();
         const words = cleanText.split(/\s+/).filter(w => w.length > 0);
         
         let fragment = "";
         if (words.length > 6) {
            const start = words.slice(0, 3).join(' ');
            const end = words.slice(-3).join(' ');
            fragment = `text=${encodeURIComponent(start)},${encodeURIComponent(end)}`;
         } else {
            fragment = `text=${encodeURIComponent(cleanText.substring(0, 80))}`;
         }

         if (url.includes(':~:text=')) return url;
         
         // The spec uses :~: as the fragment directive delimiter
         // If a hash already exists: URL#hash:~:text=...
         // If no hash exists: URL#:~:text=...
         if (url.includes('#')) {
            return `${url}:~:${fragment}`;
         }
         return `${url}#:~:${fragment}`;
      } catch {
         return url;
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
         error: null,
         resultTab: 'facts' // Default tab
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
     if (containerRef.current && loading) {
       containerRef.current.scrollTop = containerRef.current.scrollHeight;
     }
   }, [queries, loading]);
    const getSentimentTier = (score) => {
      if (score === null || score === undefined) return null;
      const s = Math.abs(score);
      const polarity = score >= 0 ? "Positive" : "Negative";
      // Inclusive threshold for user concerns
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
      
      // Automatic URL detection for fields like "Website"
      if (strVal.startsWith('http')) {
        return (
          <a href={strVal} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline break-all">
            {strVal.replace(/^https?:\/\//, '')}
          </a>
        );
      }

      const splitSafe = strVal.split(/(?<=\D),\s*|,\s+(?=\D)/);
      const parts = splitSafe.length > 1 ? splitSafe : [strVal];
      if (parts.length === 1) {
        const match = strVal.match(/^([^(]+)(?:\s*\(([^)]+)\))?$/);
        if (match) {
          return (
            <span>
              <span className="text-major">{match[1].trim()}</span>
              {match[2] && <span className="text-minor"> ({match[2]})</span>}
            </span>
          );
        }
        return <span className="text-major">{strVal}</span>;
      }
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

      return (
         <div className="w-full animate-fade-in-up">
            <div className="glass-panel w-full max-w-5xl mx-auto transition-all duration-500 relative pb-12 overflow-hidden">
               {/* Unified Pill Toggle Button */}
               <div className="flex justify-center mb-10">
                  <div className="pill-container">
                     <div
                        className="pill-indicator"
                        style={{
                           transform: `translateX(${currentTab === 'facts' ? '0' : '100%'})`
                        }}
                     />
                     <button
                        onClick={() => toggleTab(queries.indexOf(q), 'facts')}
                        className={`pill-button ${currentTab === 'facts' ? 'active' : 'inactive'}`}
                     >
                        Facts
                     </button>
                     <button
                        onClick={() => toggleTab(queries.indexOf(q), 'opinions')}
                        className={`pill-button ${currentTab === 'opinions' ? 'active' : 'inactive'}`}
                     >
                        Opinions
                     </button>
                  </div>
               </div>

               <div className="w-full">
                  {currentTab === 'facts' ? (
                     /* PANEL 1: FACTS */
                     <div key="facts-panel" className="w-full animate-fade-in-up">
                        <div className="overflow-x-auto w-full">
                           <table className="w-full text-left border-collapse font-inter">
                              <thead>
                                 <tr>
                                    <th className="bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] rounded-tl-xl border-b border-white/5 w-[20%]">Aspect</th>
                                    {entities.map((en, i) => (
                                       <th key={en} className={`bg-slate-700/30 p-4 text-slate-300 text-sm font-oswald font-medium uppercase tracking-[0.2em] border-b border-white/5 ${i === entities.length - 1 ? 'rounded-tr-xl' : ''}`}>
                                          {en}
                                       </th>
                                    ))}
                                 </tr>
                              </thead>
                              <tbody>
                                 {(() => {
                                    const rows = [];
                                    const renderedAspects = new Set();
                                    
                                    const isTech = q.parsed?.query_type?.startsWith("tech");
                                    
                                    const GROUPS = isTech ? {
                                       "Dates": ["announced", "status", "released", "release_date", "announcement_date"],
                                       "Core": ["os", "chipset", "cpu", "gpu", "platform", "system on chip", "processor", "graphics"],
                                       "Memory": ["card slot", "internal", "ram", "memory", "storage"],
                                       "Connectivity": ["wlan", "bluetooth", "positioning", "nfc", "radio", "usb", "connectivity", "wi-fi", "wifi"],
                                       "Display": ["type", "size", "resolution", "protection", "refresh rate", "screen", "display", "nits"]
                                    } : {
                                       "Personal Info": ["born", "died", "birth", "death", "spouse", "children", "nationality", "age"],
                                       "Background": ["education", "alma mater", "religion", "residence", "parents"],
                                       "Professional": ["career", "known for", "office", "political party", "occupation", "role", "years active"],
                                       "Legal Info": ["enacted by", "date enacted", "date effective", "citation", "territorial extent", "status", "jurisdiction"],
                                       "Works": ["books", "writings", "notable works", "publications", "awards", "achievements"]
                                    };

                                    const groupOrder = Object.keys(GROUPS);

                                    groupOrder.forEach(groupName => {
                                       const groupKeys = GROUPS[groupName];
                                       const matchingAspects = aspectKeys.filter(asp => (groupKeys.includes(asp.toLowerCase()) || asp.toLowerCase().includes(groupName.toLowerCase().split(' ')[0])) && !renderedAspects.has(asp));
                                       
                                       if (matchingAspects.length > 0) {
                                          rows.push(
                                             <tr key={`header-${groupName}`} className="spec-category-header">
                                                <td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-cyan-400/80 border-none">
                                                   {groupName}
                                                </td>
                                             </tr>
                                          );
                                          matchingAspects.forEach(asp => {
                                             renderedAspects.add(asp);
                                             rows.push(
                                                <tr key={asp} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                                                   <td className="py-4 pl-8 pr-6 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400 w-1/4">{asp}</td>
                                                   {entities.map(en => {
                                                      const rec = aspectMap[asp][en];
                                                      return (
                                                         <td key={en} className="py-4 px-6 text-sm text-slate-200">
                                                            {rec ? (
                                                               <div className="flex items-center gap-2 group/cell">
                                                                  {formatSpecValue(`${rec.value} ${rec.unit || ''}`)}
                                                                  {rec.source && (
                                                                     <a href={getEnhancedUrl(rec.source, `${asp} ${rec.value}`)} target="_blank" rel="noreferrer" className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-cyan-400">
                                                                        <LinkIcon size={12} />
                                                                     </a>
                                                                  )}
                                                               </div>
                                                            ) : '-'}
                                                         </td>
                                                      );
                                                   })}
                                                </tr>
                                             );
                                          });
                                       }
                                    });

                                    // Other
                                    const otherAspects = aspectKeys.filter(asp => !renderedAspects.has(asp));
                                    if (otherAspects.length > 0) {
                                       rows.push(
                                          <tr key="header-other" className="spec-category-header">
                                             <td colSpan={entities.length + 1} className="pt-8 pb-3 px-6 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 border-none">
                                                Additional Details
                                             </td>
                                          </tr>
                                       );
                                       otherAspects.forEach(asp => {
                                          rows.push(
                                             <tr key={asp} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                                                <td className="py-4 pl-8 pr-6 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400 w-1/4">{asp}</td>
                                                {entities.map(en => {
                                                   const rec = aspectMap[asp][en];
                                                   return (
                                                      <td key={en} className="py-4 px-6 text-sm text-slate-200">
                                                         {rec ? (
                                                            <div className="flex items-center gap-2 group/cell">
                                                               {formatSpecValue(`${rec.value} ${rec.unit || ''}`)}
                                                               {rec.source && (
                                                                  <a href={getEnhancedUrl(rec.source, `${asp} ${rec.value}`)} target="_blank" rel="noreferrer" className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-cyan-400">
                                                                     <LinkIcon size={12} />
                                                                  </a>
                                                               )}
                                                            </div>
                                                         ) : '-'}
                                                      </td>
                                                   );
                                                })}
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
                     /* PANEL 2: OPINIONS */
                     <div key="opinions-panel" className="w-full animate-fade-in-up px-4">
                        {(() => {
                           const MEANINGFUL_SCORE_ASPECTS = new Set([
                              "camera", "cameras", "battery", "display", "screen", "performance",
                              "build", "design", "software", "charging", "speakers", "audio",
                              "speed", "value", "price", "overall", "gaming", "photography", "dates", "core", "connectivity"
                           ]);

                           const aspectScoreMap = {};
                           entities.forEach(en => {
                              scoreMap[en].forEach(s => {
                                 const asp = s.aspect.toLowerCase();
                                 if (!MEANINGFUL_SCORE_ASPECTS.has(asp)) return;
                                 if (!aspectScoreMap[asp]) aspectScoreMap[asp] = { value: s.value, cards: [] };
                                 else aspectScoreMap[asp].value = Math.max(aspectScoreMap[asp].value, s.value);
                              });
                              subjectiveMap[en].forEach(r => {
                                 if (!getSentimentTier(r.score)) return;
                                 const asp = r.aspect.toLowerCase();
                                 const target = aspectScoreMap[asp];
                                 if (target) target.cards.push({ ...r, entityLabel: en });
                              });
                           });

                           const otherCards = entities.flatMap(en =>
                              subjectiveMap[en].filter(r => {
                                 if (!getSentimentTier(r.score)) return false;
                                 const asp = r.aspect.toLowerCase();
                                 if (aspectScoreMap[asp]) return false;
                                 return r.text.length > 20;
                              }).map(r => ({ ...r, entityLabel: en }))
                           ).slice(0, 8);

                           const aspectRows = Object.entries(aspectScoreMap);

                           return (
                              <div className="flex flex-col gap-10">
                                 {aspectRows.map(([asp, data]) => (
                                    <div key={asp} className="flex opinion-row items-center gap-8">
                                       <div className="shrink-0 w-28 flex flex-col items-center justify-center">
                                          <span className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 text-center">{asp}</span>
                                          <span className={`text-[24px] font-mono font-black ${data.value >= 7 ? 'text-emerald-400' : data.value >= 4 ? 'text-yellow-400' : 'text-red-400'}`}>
                                             {data.value}<span className="text-sm text-slate-500 font-bold">/10</span>
                                          </span>
                                       </div>
                                       <div className="flex-1 overflow-x-auto custom-scrollbar pb-2">
                                          <div className="flex gap-4" style={{ minWidth: 'max-content' }}>
                                             {data.cards.map((r, k) => {
                                                const tier = getSentimentTier(r.score);
                                                const isPos = r.score >= 0;
                                                const isPro = r.metadata?.is_professional;
                                                const sentimentClass = isPos ? 'border-t-2 border-t-emerald-500' : 'border-t-2 border-t-red-500';
                                                return (
                                                   <div key={k} className={`opinion-card w-72 shrink-0 bg-slate-900/60 border border-white/5 rounded-xl p-5 flex flex-col shadow-lg transition-transform hover:-translate-y-1 ${sentimentClass} ${isPro ? 'professional' : ''}`}>
                                                      <div className="flex justify-between items-center mb-3">
                                                         <span className="bg-slate-700/60 px-2 py-0.5 rounded text-[10px] font-bold uppercase text-slate-400">{r.entityLabel?.split(' ').pop()}</span>
                                                         <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${isPos ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{tier}</span>
                                                      </div>
                                                      <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed flex-1">"{r.text}"</p>
                                                      {(() => {
                                                         const cardUrl = r.metadata?.url || (queries[activeChat]?.urls && queries[activeChat].urls[r.entityLabel]?.urls?.[0]);
                                                         if (!cardUrl) return null;
                                                         return (
                                                            <a href={getEnhancedUrl(cardUrl, r.text)} target="_blank" rel="noreferrer" className="mt-4 self-end p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all">
                                                               <LinkIcon size={14} />
                                                            </a>
                                                         );
                                                      })()}
                                                   </div>
                                                );
                                             })}
                                          </div>
                                       </div>
                                    </div>
                                 ))}
                                 {otherCards.length > 0 && (
                                    <div className="flex opinion-row items-center gap-8">
                                       <div className="shrink-0 w-28 flex flex-col items-center justify-center">
                                          <span className="text-xs font-bold uppercase tracking-widest text-slate-400 text-center">Other</span>
                                       </div>
                                       <div className="flex-1 overflow-x-auto custom-scrollbar pb-2">
                                          <div className="flex gap-4" style={{ minWidth: 'max-content' }}>
                                             {otherCards.map((r, k) => (
                                                <div key={k} className={`opinion-card w-72 shrink-0 bg-slate-900/60 border border-white/5 rounded-xl p-5 flex flex-col shadow-lg transition-transform hover:-translate-y-1 ${r.score > 0 ? 'border-t-2 border-t-emerald-500' : 'border-t-2 border-t-red-500'}`}>
                                                   <div className="flex justify-between items-center mb-3">
                                                      <span className="bg-slate-800/80 px-3 py-1 rounded-full text-xs font-semibold capitalize text-slate-300">{r.aspect}</span>
                                                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${r.score > 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{getSentimentTier(r.score)}</span>
                                                   </div>
                                                   <p className="m-0 text-[13px] text-slate-300 italic leading-relaxed flex-1">"{r.text}"</p>
                                                   {queries[activeChat]?.urls && queries[activeChat].urls[r.entityLabel]?.urls?.[0] && (
                                                      <a href={queries[activeChat].urls[r.entityLabel].urls[0]} target="_blank" rel="noreferrer" className="mt-4 self-end p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-500 hover:text-white transition-all">
                                                         <LinkIcon size={14} />
                                                      </a>
                                                   )}
                                                </div>
                                             ))}
                                          </div>
                                       </div>
                                    </div>
                                 )}
                              </div>
                           );
                        })()}
                     </div>
                  )}
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

               <div className={`h-px bg-gray-600 mb-4 mx-1 transition-opacity ${sidebarOpen ? 'opacity-100' : 'opacity-50'}`}></div>

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

               {/* Debug and Clear Cache Buttons at Bottom */}
               <div className="p-3 border-t border-white/5 mt-auto space-y-2">
                  <button
                     onClick={handleToggleDebug}
                     className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg transition-all duration-300 font-inter text-xs font-bold uppercase tracking-widest ${sidebarOpen
                        ? (debugMode ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]" : "bg-slate-800/40 text-slate-500 border border-white/5 hover:bg-slate-800/60")
                        : (debugMode ? "text-cyan-400" : "text-slate-600 hover:text-slate-400")
                        }`}
                     title={debugMode ? "Disable Debug Mode" : "Enable Debug Mode"}
                  >
                     {sidebarOpen ? (
                        <>
                           <Terminal size={14} />
                           <span>Debug: {debugMode ? "ON" : "OFF"}</span>
                        </>
                     ) : (
                        <Terminal size={20} />
                     )}
                  </button>

                  <button
                     onClick={handleClearCache}
                     className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg transition-all duration-300 font-inter text-xs font-bold uppercase tracking-widest ${sidebarOpen
                        ? "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20"
                        : "text-red-500/40 hover:text-red-500"
                        }`}
                     title="Clear Local Database Cache"
                  >
                     {sidebarOpen ? (
                        <>
                           <span>Clear Cache</span>
                        </>
                     ) : (
                        <span>&times;</span>
                     )}
                  </button>
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
                  <h1 className="text-5xl md:text-7xl xl:text-[6rem] font-oswald text-white uppercase tracking-[0.1em] drop-shadow-2xl">
                     MIACT
                  </h1>
               </div>

               {/* Session Mapping */}
               <div className="w-full flex flex-col items-center z-10">
                  {queries.map((q, i) => (
                     <div key={i} data-index={i} className="result-container result-container-stable w-full flex flex-col items-center mb-16 animate-fade-in-up">
                        <div className="px-6 py-2 rounded-full bg-[#111] border border-gray-600 font-inter text-slate-300 font-medium text-sm w-fit max-w-[95%] mb-5 shadow-[0_2px_10_rgba(0,0,0,0.3)]">
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
               className={`absolute top-6 right-8 w-[420px] max-h-[80vh] z-[100] flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.8)] border border-white/5 p-6 rounded-3xl glass-popup transition-all duration-[350ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] ${showSourcesPopup && queries[activeChat]?.urls && activeSourceTab ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto' : 'opacity-0 scale-90 -translate-y-3 pointer-events-none origin-top-right'}`}
            >
               <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-3 relative">
                  <h4 className="m-0 text-white font-oswald text-2xl uppercase tracking-[0.25em] font-medium mx-auto">SOURCES</h4>
                  <button onClick={() => setShowSourcesPopup(false)} className="absolute right-0 bg-transparent border-none text-slate-500 text-3xl hover:text-white cursor-pointer transition-colors leading-[0] outline-none pb-1">&times;</button>
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
                        <div className="timeline-list">
                           {(() => {
                              const sourceList = queries[activeChat].urls[activeSourceTab]?.urls || [];
                              const verified = sourceList.filter(u => u.includes("gsmarena.com") || u.includes("wikipedia.org"));
                              const secondary = sourceList.filter(u => !u.includes("gsmarena.com") && !u.includes("wikipedia.org"));

                              return (
                                 <>
                                    {verified.length > 0 && (
                                       <div className="mb-8 mt-2">
                                          <span className="text-[12px] font-black uppercase tracking-[0.3em] text-emerald-400 mb-6 block relative before:content-[''] before:absolute before:w-10 before:h-[1px] before:bg-emerald-900/50 before:top-1/2 before:left-full before:ml-3">Official Specs</span>
                                          {verified.map((u, i) => (
                                             <div key={u} className="timeline-item group">
                                                <div className="timeline-bullet bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.5)] transition-transform group-hover:scale-125"></div>
                                                {i < verified.length - 1 && <div className="timeline-line"></div>}
                                                <a href={u} target="_blank" rel="noreferrer" className="text-slate-200 font-medium text-[16px] tracking-wide hover:text-white leading-relaxed break-all transition-colors duration-200 block">
                                                   {formatUrlText(u)}
                                                </a>
                                             </div>
                                          ))}
                                       </div>
                                    )}

                                    {secondary.length > 0 && (
                                       <div className="mt-12">
                                          <span className="text-[12px] font-black uppercase tracking-[0.3em] text-slate-500 mb-6 block relative before:content-[''] before:absolute before:w-10 before:h-[1px] before:bg-slate-800 before:top-1/2 before:left-full before:ml-3">Secondary Mentions</span>
                                          {secondary.map((u, i) => (
                                             <div key={u} className="timeline-item group">
                                                <div className="timeline-bullet bg-slate-600 transition-all duration-300 group-hover:bg-slate-400 group-hover:scale-110"></div>
                                                {i < secondary.length - 1 && <div className="timeline-line"></div>}
                                                <a href={u} target="_blank" rel="noreferrer" className="text-slate-400 font-medium text-[14px] tracking-wide hover:text-slate-200 leading-relaxed break-all transition-colors duration-200 block">
                                                   {formatUrlText(u)}
                                                </a>
                                             </div>
                                          ))}
                                       </div>
                                    )}
                                 </>
                              );
                           })()}
                        </div>
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
