import { useState, useRef, useEffect } from "react";
import "./App.css";
import { ArrowRight } from "lucide-react";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeChat, setActiveChat] = useState(0);
  const [queries, setQueries] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const containerRef = useRef(null);

  const sendQuery = async () => {
    if (!input.trim()) return;

    const queryText = input;
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/parse", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: queryText }),
      });

      const data = await res.json();

      const newQuery = {
        query_text: queryText,
        parsed: data,
      };

      setQueries(prev => [...prev, newQuery]);
    } catch (err) {
      const newQuery = {
        query_text: queryText,
        parsed: { error: "Backend error" },
      };

      setLoading(false);
      
      setQueries(prev => [...prev, newQuery]);
    }

    setInput("");
  };

  // Auto-scroll to bottom on new query
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [queries]);

 return (
    <div className="app">

      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>

        <div className="sidebar-inner">
          <div className="sidebar-header">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <div></div>
              <div></div>
              <div></div>
            </button>

            <h3 className={`sidebar-title ${sidebarOpen ? "" : "hidden"}`}>
              History
            </h3>
          </div>
        </div>

        <div className="sidebar-divider"></div>

        <div className="sidebar-inner">
          <div className="chat-list">
            {queries.map((q, i) => (
              <div
                key={i}
                className={`chat-item ${i === activeChat ? "active" : ""}`}
                onClick={() => setActiveChat(i)}
              >
                {q.query_text}
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Main */}
      <div className="main">

        {/* Content */}
        <div ref={containerRef} className="content">
          {queries.map((q, i) => (
            <div key={i} className="session">

              {/* Query */}
              <div className="query-pill">
                {q.query_text}
              </div>

              {/* Result */}
              <div className="result">
                {q.parsed.error ? (
                  <div>{q.parsed.error}</div>
                ) : (
                  <>
                    <div><b>Mode:</b> {q.parsed.mode}</div>
                    <div><b>Entities:</b> {q.parsed.entities?.join(", ")}</div>
                    <div><b>Type:</b> {q.parsed.type}</div>
                  </>
                )}
              </div>

            </div>
          ))}
        </div>

        {/* Input */}
        <div className="input-bar">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendQuery();
              }
            }}
            placeholder="Enter a query..."
          />
          <button onClick={sendQuery} className="send-btn">
            <ArrowRight size={48} />
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;