import React, { useState, useEffect, useRef, useLayoutEffect, Component } from "react";
import "./App.css";
import { ArrowRight, Loader, ChevronLeft, History, Link as LinkIcon, Terminal, Settings, Check, AlertTriangle } from "lucide-react";
import ResultHandler from "./components/ResultHandler";

class ErrorBoundary extends Component {
   constructor(props) {
      super(props);
      this.state = { hasError: false, errorMessage: "" };
   }
   static getDerivedStateFromError(error) {
      return { hasError: true, errorMessage: error.toString() };
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
   const [configGroups, setConfigGroups] = useState(null);

   // Debug Settings
   const [showDebugMenu, setShowDebugMenu] = useState(false);
   const [debugSettings, setDebugSettings] = useState({
      services: ["*"],
      log_all: true,
      available_services: []
   });

   // Sources Card
   const [showSourcesPopup, setShowSourcesPopup] = useState(false);
   const [activeSourceTab, setActiveSourceTab] = useState(null);
   const sourcesPopupRef = useRef(null);
   const sourcesToggleRef = useRef(null);
   const debugMenuRef = useRef(null);

   const containerRef = useRef(null);

   // Initialize settings from backend
   useEffect(() => {
     const initApp = async () => {
       try {
         // Fetch Debug Settings
         const debugResp = await fetch("http://127.0.0.1:8000/api/debug/settings");
         const debugData = await debugResp.json();
         setDebugMode(debugData.debug);
         setDebugSettings({
            services: debugData.services,
            log_all: debugData.log_all,
            available_services: debugData.available_services
         });

         // Fetch Unified Config
         const configResp = await fetch("http://127.0.0.1:8000/api/config/groups");
         const configData = await configResp.json();
         setConfigGroups(configData);
       } catch (err) {
         console.error("Failed to initialize app settings:", err);
       }
     };
     initApp();
   }, []);

   const updateBackendDebug = async (newMode, newServices, newLogAll) => {
      try {
         await fetch("http://127.0.0.1:8000/api/debug/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
               debug: newMode,
               services: newServices,
               log_all: newLogAll
            }),
         });
      } catch (err) {
         console.error("Failed to update debug settings:", err);
      }
   };

   const handleToggleDebug = async () => {
     const newDebugState = !debugMode;
     setDebugMode(newDebugState);
     await updateBackendDebug(newDebugState, debugSettings.services, debugSettings.log_all);
   };

   const toggleService = (service) => {
      let nextServices;
      if (service === "*") {
         nextServices = ["*"];
      } else {
         const current = debugSettings.services.filter(s => s !== "*");
         if (current.includes(service)) {
            nextServices = current.filter(s => s !== service);
            if (nextServices.length === 0) nextServices = ["*"];
         } else {
            nextServices = [...current, service];
         }
      }
      const nextSettings = { ...debugSettings, services: nextServices };
      setDebugSettings(nextSettings);
      updateBackendDebug(debugMode, nextServices, debugSettings.log_all);
   };

   const toggleLogAll = () => {
      const nextLogAll = !debugSettings.log_all;
      setDebugSettings({ ...debugSettings, log_all: nextLogAll });
      updateBackendDebug(debugMode, debugSettings.services, nextLogAll);
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

   // Close popups on click-outside
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
         if (
            showDebugMenu &&
            debugMenuRef.current &&
            !debugMenuRef.current.contains(e.target)
         ) {
            setShowDebugMenu(false);
         }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
   }, [showSourcesPopup, showDebugMenu]);

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

   const getSentimentTier = (score) => {
      if (score === null || score === undefined) return null;
      const s = Math.abs(score);
      const polarity = score >= 0 ? "Positive" : "Negative";
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
      if (strVal.startsWith('http')) {
         return (
            <a href={strVal} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline break-all">
               {strVal.replace(/^https?:\/\//, '')}
            </a>
         );
      }
      
      // Don't split long paragraphs (likely news summaries or descriptions)
      if (strVal.length > 120) {
         return <span className="text-major leading-relaxed block py-1">{strVal}</span>;
      }

      const splitSafe = strVal.split(/(?<=\D),\s*|,\s+(?=\D)/);
      const parts = splitSafe.length > 1 ? splitSafe : [strVal];
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
         if (url.includes('#')) {
            return `${url}:~:${fragment}`;
         }
         return `${url}#:~:${fragment}`;
      } catch {
         return url;
      }
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

   const sendQuery = async () => {      if (!input.trim() || loading) return;

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
                  q.status = `Processing: ${data.url.substring(0, 30)}...`;
               } else if (data.step === "partial_result") {
                  q.results = {
                     facts: { ...(q.results?.facts || {}), ...data.results.facts },
                     research: { ...(q.results?.research || {}), ...data.results.research },
                     analysis: { ...(q.results?.analysis || {}), ...data.results.analysis }
                  };
                  q.urls = data.urls || q.urls;
                  q.status = "Receiving updates...";
               } else if (data.step === "ai_summary") {
                  q.aiSummary = data.summary;
                  q.status = "Generated AI Insight";
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

   return (
      <div className="flex h-screen w-screen overflow-hidden text-white font-inter bg-[radial-gradient(circle_at_top_left,#283347,#040a19)]">
         {/* Left Sidebar */}
         <div className={`relative flex flex-col bg-[#111] z-10 pt-4 pb-0 ${isDragging ? '' : 'transition-[width] duration-300'}`} style={{ width: sidebarOpen ? sidebarWidth : 72 }}>
            <div className="flex flex-col flex-1 overflow-hidden px-3">
               <div className="flex items-center mb-4 pl-2 w-full relative">
                  <button className="p-1 rounded-md hover:bg-white/10" onClick={handleToggleSidebar}>{sidebarOpen ? <ChevronLeft size={24} /> : <History size={24} />}</button>
                  <h3 className={`font-oswald uppercase tracking-widest m-0 text-center absolute left-0 right-0 pointer-events-none transition-opacity ${sidebarOpen && sidebarWidth > 140 ? 'opacity-100' : 'opacity-0'}`}>History</h3>
               </div>
               <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
                  {queries.map((q, i) => <div key={i} className={`cursor-pointer p-2 rounded truncate ${i === activeChat ? 'bg-gray-900 text-white' : 'text-gray-500'}`} onClick={() => setActiveChat(i)}>{sidebarOpen ? q.query_text : '•'}</div>)}
               </div>
               
               {/* Bottom Buttons */}
               <div className="p-3 border-t border-white/5 space-y-2 relative">
                  {/* Debug Menu Popup */}
                  {showDebugMenu && sidebarOpen && (
                     <div ref={debugMenuRef} className="absolute bottom-full left-3 right-3 bg-[#1a1a1a] border border-white/10 rounded-xl p-4 shadow-2xl z-[100] mb-2 animate-in fade-in slide-in-from-bottom-2">
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">Service Filters</h4>
                        <div className="grid grid-cols-2 gap-2 mb-4">
                           <button onClick={() => toggleService("*")} className={`text-[9px] font-bold p-1.5 rounded border transition-all ${debugSettings.services.includes("*") ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400' : 'bg-white/5 border-white/5 text-slate-500'}`}>ALL SERVICES</button>
                           {debugSettings.available_services.map(s => (
                              <button key={s} onClick={() => toggleService(s)} className={`text-[9px] font-bold p-1.5 rounded border transition-all flex items-center justify-between ${debugSettings.services.includes(s) ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400' : 'bg-white/5 border-white/5 text-slate-500'}`}>
                                 {s} {debugSettings.services.includes(s) && <Check size={10} />}
                              </button>
                           ))}
                        </div>
                        <div className="flex items-center justify-between pt-2 border-t border-white/5">
                           <span className="text-[9px] font-bold text-slate-500 uppercase">Log All To File</span>
                           <button onClick={toggleLogAll} className={`w-8 h-4 rounded-full relative transition-colors ${debugSettings.log_all ? 'bg-cyan-600' : 'bg-slate-700'}`}>
                              <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${debugSettings.log_all ? 'left-4.5' : 'left-0.5'}`} />
                           </button>
                        </div>
                     </div>
                  )}

                  <div className="flex gap-1">
                     <button onClick={handleToggleDebug} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg transition-all text-xs font-bold uppercase tracking-widest ${debugMode ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40" : "bg-slate-800/40 text-slate-500 border border-white/5"}`}>
                        <Terminal size={14} /> {sidebarOpen && `Debug: ${debugMode ? "ON" : "OFF"}`}
                     </button>
                     {sidebarOpen && (
                        <button onClick={() => setShowDebugMenu(!showDebugMenu)} className={`p-2 rounded-lg border transition-all ${showDebugMenu ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400' : 'bg-slate-800/40 border-white/5 text-slate-500'}`}>
                           <Settings size={14} />
                        </button>
                     )}
                  </div>
                  <button onClick={handleClearCache} className="w-full py-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 text-xs font-bold uppercase tracking-widest hover:bg-red-500/20">{sidebarOpen ? "Clear Cache" : "×"}</button>
               </div>
            </div>
            <div className="absolute top-0 -right-[3px] w-[6px] h-full cursor-col-resize hover:bg-blue-400/50" onMouseDown={() => { isResizing.current = true; setIsDragging(true); }} />
         </div>

         {/* Main Content Area */}
         <div className="flex-1 flex flex-col relative min-w-0">
            <div ref={containerRef} className="flex-1 overflow-y-auto p-10 pb-[140px] flex flex-col items-center">

               {/* Absolute Centered Welcome Banner */}
               <div className={`absolute left-0 right-0 top-[35%] flex justify-center pointer-events-none px-4 text-center ${queries.length === 0 ? 'opacity-100' : 'opacity-0'}`}>
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
                              <ResultHandler 
                                 query={q} 
                                 index={i} 
                                 configGroups={configGroups} 
                                 toggleTab={toggleTab} 
                                 formatUrlText={formatUrlText} 
                                 formatSpecValue={formatSpecValue} 
                                 getEnhancedUrl={getEnhancedUrl} 
                                 getSentimentTier={getSentimentTier} 
                              />
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
