import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { ArrowRight, Loader, PanelLeftClose, PanelLeftOpen } from "lucide-react";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(240);
  const isResizing = useRef(false);

  const [activeChat, setActiveChat] = useState(0);
  const [queries, setQueries] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [currentSources, setCurrentSources] = useState(null); 
  const containerRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      let newWidth = e.clientX;
      if (newWidth < 72) newWidth = 72;
      if (newWidth > 500) newWidth = 500;
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = 'default';
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const sendQuery = async () => {
    if (!input.trim() || loading) return;

    const queryText = input;
    setLoading(true);
    setInput("");
    setCurrentSources(null);

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

    const es = new EventSource(`http://127.0.0.1:8000/search?query=${encodeURIComponent(queryText)}`);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.step === "result") {
          es.close();
          setLoading(false);
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
            
            if (q.urls && Object.keys(q.urls).length > 0) {
               const firstEntity = Object.keys(q.urls)[0];
               setCurrentSources({ entity: firstEntity, urls: q.urls[firstEntity].urls });
            }
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
      if (!path || path.toLowerCase() === domain.toLowerCase()) {
         return `${domain.charAt(0).toUpperCase() + domain.slice(1)}`;
      }
      return `${domain.charAt(0).toUpperCase() + domain.slice(1)} - ${decodeURIComponent(path)}`;
    } catch {
      return urlStr;
    }
  };

  const renderResults = (q) => {
    if (q.error) return <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-md">{q.error}</div>;

    if (!q.results && q.status !== "Done") {
      return (
        <div className="glass-panel flex items-center gap-3 text-slate-400 p-5 w-auto">
          <Loader className="animate-spin" size={24} />
          <span>{q.status}</span>
        </div>
      );
    }
    
    if (!q.results) return null;

    const allObjective = [];
    const allSubjective = [];
    const entities = Object.keys(q.results);

    entities.forEach(en => {
        const records = q.results[en];
        records.forEach(r => {
            if (r.type !== 'subjective') allObjective.push({ ...r, entity: en });
            else if (r.score !== 0 && r.score !== null) allSubjective.push({ ...r, entity: en });
        });
    });

    const aspectMap = {};
    allObjective.forEach(r => {
        if (!aspectMap[r.aspect]) aspectMap[r.aspect] = {};
        aspectMap[r.aspect][r.entity] = r;
    });
    const aspectKeys = Object.keys(aspectMap);

    const subjectiveMap = {};
    entities.forEach(en => subjectiveMap[en] = []);
    allSubjective.forEach(r => subjectiveMap[r.entity].push(r));

    return (
      <div className="w-full flex justify-center animate-fade-in-up">
         <div className="glass-panel w-full max-w-5xl transition-all duration-500 ease-[cubic-bezier(0.25,0.8,0.25,1)]">
            <h3 className="text-2xl font-bold text-slate-200 mb-5">Comparison</h3>
            <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                   <thead>
                     <tr>
                       <th className="bg-slate-700/50 p-3 text-slate-300 text-sm font-bold uppercase tracking-wider rounded-tl-xl border-b border-white/5">Aspect</th>
                       {entities.map((en, i) => (
                          <th 
                             key={en}
                             className={`bg-slate-700/50 p-3 text-slate-300 text-sm font-bold uppercase tracking-wider border-b border-white/5 transition-all duration-300 hover:bg-blue-400/10 cursor-default ${i===entities.length-1?'rounded-tr-xl':''}`}
                             onMouseEnter={() => {
                                if (q.urls && q.urls[en]) setCurrentSources({ entity: en, urls: q.urls[en].urls });
                             }}
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
                                     className="p-4 border-b border-white/5 font-mono text-emerald-400 transition-all duration-300 hover:bg-blue-400/10 cursor-default"
                                     onMouseEnter={() => {
                                        if (q.urls && q.urls[en]) setCurrentSources({ entity: en, urls: q.urls[en].urls });
                                     }}
                                  >
                                     {rec ? `${rec.value} ${rec.unit || ''}` : '-'}
                                  </td>
                               );
                            })}
                         </tr>
                      ))}
                      {/* Opinions Divider */}
                      {allSubjective.length > 0 && (
                         <>
                            <tr>
                               <td colSpan={entities.length + 1} className="pt-6 pb-3 border-none">
                                  <h4 className="text-sm text-slate-400 font-bold uppercase tracking-widest">Opinions & Sentiments</h4>
                               </td>
                            </tr>
                            <tr>
                               <td className="border-none"></td>
                               {entities.map(en => (
                                  <td 
                                     key={en} 
                                     className="border-none align-top pt-2 transition-all duration-300 hover:bg-blue-400/5 rounded-md"
                                     onMouseEnter={() => {
                                        if (q.urls && q.urls[en]) setCurrentSources({ entity: en, urls: q.urls[en].urls });
                                     }}
                                  >
                                     <div className="flex flex-col items-center gap-3">
                                        {subjectiveMap[en].map((r, k) => {
                                            const tier = getSentimentTier(r.score);
                                            const isPos = r.score > 0;
                                            return (
                                               <div key={k} className={`w-full max-w-[280px] bg-slate-900/40 border border-white/5 rounded-xl p-3 flex flex-col items-center text-center transition-all duration-300 shadow-md transform hover:-translate-y-1 hover:shadow-lg ${isPos?'border-l-emerald-500 border-l-[3px]':'border-l-red-500 border-l-[3px]'}`}>
                                                  <div className="w-full flex justify-between items-center mb-2">
                                                     <span className="bg-white/10 px-2 py-1 rounded-full text-xs capitalize text-slate-200">{r.aspect}</span>
                                                     <span className={`text-xs font-bold px-2 py-1 rounded-full ${isPos?'bg-emerald-500/20 text-emerald-400':'bg-red-500/20 text-red-400'}`}>{tier}</span>
                                                  </div>
                                                  <p className="m-0 text-sm text-slate-300 italic leading-snug">"{r.text}"</p>
                                               </div>
                                            );
                                        })}
                                     </div>
                                  </td>
                               ))}
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
    <div className="flex h-screen w-screen overflow-hidden text-white font-sans bg-[radial-gradient(circle_at_top_left,#283347,#040a19)]">
      
      {/* Left Sidebar */}
      <div 
         className={`relative flex flex-col bg-[#111] transition-[width] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] z-10 ${sidebarOpen ? "px-4" : "px-4"} py-4`} 
         style={{ width: sidebarOpen ? sidebarWidth : 72 }}
      >
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex items-center gap-3 overflow-hidden min-h-[30px] mb-4">
            <button className="p-1 flex items-center justify-center rounded-md hover:bg-white/10 transition-colors cursor-pointer shrink-0" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? <PanelLeftClose size={24} className="text-slate-400" /> : <PanelLeftOpen size={24} className="text-slate-400" />}
            </button>
            <h3 className={`whitespace-nowrap transition-opacity duration-200 text-lg font-semibold m-0 ${sidebarOpen ? "opacity-100" : "opacity-0 invisible w-0"}`}>
              History
            </h3>
          </div>
          
          <div className={`h-px bg-gray-600 mb-4 transition-opacity ${sidebarOpen?'opacity-100':'opacity-50'}`}></div>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {queries.map((q, i) => (
              <div
                key={i}
                className={`cursor-pointer overflow-hidden text-ellipsis whitespace-nowrap transition-all duration-300 ease-in-out font-medium
                  ${i === activeChat 
                     ? "border border-gray-600 bg-transparent text-white px-0 flex items-center justify-center min-h-[40px] rounded-md shadow-inner" 
                     : (sidebarOpen ? "text-gray-400 hover:bg-gray-800 hover:text-white p-2 rounded-lg" : "text-gray-400 flex items-center justify-center p-2 rounded-lg")
                  }`}
                onClick={() => setActiveChat(i)}
                title={q.query_text}
              >
                {sidebarOpen ? q.query_text : (i === activeChat ? "\u2022" : "\u2022")}
              </div>
            ))}
          </div>
        </div>

        {/* Resizer Handle */}
        {sidebarOpen && (
          <div 
             className="absolute top-0 -right-[3px] w-[6px] h-full cursor-col-resize z-20 hover:bg-blue-400/50 transition-colors"
             onMouseDown={(e) => {
               isResizing.current = true;
               document.body.style.cursor = 'col-resize';
             }}
          />
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative min-w-0">
         <div ref={containerRef} className="flex-1 overflow-y-auto p-10 pb-[140px] flex flex-col items-center">
            
            {/* Absolute Centered Welcome Banner */}
            {queries.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <h1 className="welcome-glow text-6xl font-extrabold bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent transform scale-100 animate-pulse tracking-tight drop-shadow-lg">
                     Welcome, Seeker
                  </h1>
              </div>
            )}
            
            {/* Session Mapping */}
            <div className="w-full flex flex-col items-center z-10">
               {queries.map((q, i) => (
                 <div key={i} className="w-full flex flex-col items-center mb-8 animate-fade-in-up">
                   <div className="px-5 py-3 rounded-full bg-slate-800 text-slate-300 text-sm w-fit max-w-[95%] mb-5 shadow-md border border-slate-700/50">
                     {q.query_text}
                   </div>
                   <div className="w-full max-w-[1000px]">
                     {renderResults(q)}
                   </div>
                 </div>
               ))}
            </div>
         </div>

        {/* Floating Sources Card */}
        {currentSources && (
          <div className="absolute top-10 right-10 w-[340px] max-h-[500px] z-[100] flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/10 p-5 rounded-2xl bg-slate-900/60 backdrop-blur-xl transition-all duration-500 ease-[cubic-bezier(0.175,0.885,0.32,1.275)] animate-float-in">
            <div className="flex justify-between items-center border-b-2 border-dashed border-white/10 pb-3 mb-4">
               <h4 className="m-0 text-slate-200 font-semibold">Sources: <span className="text-blue-400 uppercase tracking-wide">{currentSources.entity}</span></h4>
               <button onClick={() => setCurrentSources(null)} className="bg-transparent border-none text-slate-400 text-2xl hover:text-white cursor-pointer transition-colors leading-none outline-none">&times;</button>
            </div>
            <div className="overflow-y-auto pr-2 custom-scrollbar">
               <ul className="list-none p-0 m-0 ml-[10px] relative border-l-2 border-blue-400/40">
                  {currentSources.urls.map((u, i) => (
                     <li key={u} className="relative pl-[20px] mb-4 last:mb-0 group">
                        {/* Timeline Bullet */}
                        <div className="absolute -left-[7px] top-[4px] w-[12px] h-[12px] bg-blue-500 rounded-full shadow-[0_0_0_3px_rgba(30,41,59,0.8)] transition-all duration-300 group-hover:scale-[1.3] group-hover:bg-blue-400 group-hover:shadow-[0_0_0_3px_rgba(96,165,250,0.2)]"></div>
                        <a href={u} target="_blank" rel="noreferrer" className="text-slate-200 text-sm inline-block leading-snug break-words transition-colors duration-200 hover:text-blue-300 bg-white/5 py-2 px-3 rounded-lg hover:bg-white/10 w-full shadow-sm">
                           {formatUrlText(u)}
                        </a>
                     </li>
                  ))}
               </ul>
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl flex items-center p-3 rounded-full bg-[#111] shadow-[0_10px_30px_rgba(0,0,0,0.5)] border border-white/10 z-50 transition-all duration-300 hover:shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
          <input
            className="flex-1 p-3 bg-transparent text-white border-none outline-none ml-2 text-md placeholder-slate-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendQuery();
            }}
            placeholder="Ask about a phone, laptop, or news topic..."
            disabled={loading}
          />
          <button 
             onClick={sendQuery} 
             className="ml-2 w-12 h-12 rounded-full border-none bg-slate-800 text-white flex items-center justify-center cursor-pointer transition-all duration-200 hover:bg-slate-700 active:scale-95 disabled:opacity-50"
             disabled={loading}
          >
            {loading ? <Loader className="animate-spin" size={24} /> : <ArrowRight size={22} />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;