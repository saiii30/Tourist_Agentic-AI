import { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  FaPaperPlane,
  FaRobot,
  FaPlus,
  FaMicrophone,
  FaUser,
  FaMapMarkerAlt,
  FaCloud,
  FaUtensils,
  FaCalendarAlt,
  FaBuilding,
  FaCog,
  FaSearch,
} from "react-icons/fa";

type Message = {
  role: "user" | "assistant";
  text: string;
  routes?: string[];
};

// Simple markdown renderer for AI responses
function MarkdownContent({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Skip empty lines
    if (line.trim() === "") {
      i++;
      continue;
    }

    // H1 heading: # Title
    if (/^# /.test(line)) {
      elements.push(
        <p key={i} className="text-base font-semibold text-gray-900 mt-3 mb-1">
          {line.replace(/^# /, "")}
        </p>
      );
      i++;
      continue;
    }

    // H2/H3 heading: ## or ###
    if (/^#{2,3} /.test(line)) {
      elements.push(
        <p key={i} className="text-sm font-semibold text-gray-800 mt-3 mb-1">
          {line.replace(/^#{2,3} /, "")}
        </p>
      );
      i++;
      continue;
    }

    // Bullet list block: lines starting with - or *
    if (/^[-*] /.test(line)) {
      const bullets: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        bullets.push(lines[i].replace(/^[-*] /, ""));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="mt-1 mb-2 space-y-1.5 pl-1">
          {bullets.map((b, bi) => (
            <li key={bi} className="flex items-start gap-2 text-sm text-gray-700">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#1D9E75] flex-shrink-0" />
              <span dangerouslySetInnerHTML={{ __html: inlineMd(b) }} />
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Numbered list block: lines starting with 1. 2. etc.
    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, ""));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="mt-1 mb-2 space-y-1.5 pl-1">
          {items.map((it, ii) => (
            <li key={ii} className="flex items-start gap-2.5 text-sm text-gray-700">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#1D9E75]/10 text-[#1D9E75] text-[10px] font-semibold flex items-center justify-center mt-0.5">
                {ii + 1}
              </span>
              <span dangerouslySetInnerHTML={{ __html: inlineMd(it) }} />
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Bold-only line used as a section label (e.g. **Hotels:**)
    if (/^\*\*[^*]+\*\*:?$/.test(line.trim())) {
      elements.push(
        <p key={i} className="text-sm font-semibold text-gray-800 mt-3 mb-0.5">
          {line.replace(/\*\*/g, "").replace(/:$/, "")}
        </p>
      );
      i++;
      continue;
    }

    // Regular paragraph
    elements.push(
      <p
        key={i}
        className="text-sm text-gray-700 leading-relaxed mb-1"
        dangerouslySetInnerHTML={{ __html: inlineMd(line) }}
      />
    );
    i++;
  }

  return <div className="space-y-0.5">{elements}</div>;
}

// Convert inline markdown: **bold**, *italic*, `code`
function inlineMd(text: string): string {
  return text
    .replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="my-2 rounded-lg border border-black/[0.07] max-h-48" />')    
    .replace(/\[View Map\]\((.+?)\)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">🗺️ View Map</a>')
    .replace(/\[Visit Website\]\((.+?)\)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">Visit Website</a>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="bg-gray-100 text-[#1D9E75] px-1 py-0.5 rounded text-xs font-mono">$1</code>');
}

const EXAMPLES = [
  { icon: <FaBuilding />, text: "Best hotels in Madurai" },
  { icon: <FaUtensils />, text: "Restaurants near Meenakshi Temple" },
  { icon: <FaCalendarAlt />, text: "3 day trip plan for Chennai" },
];

function getBadgeInfo(route: string) {
  switch (route) {
    case "weather":
      return { label: "Weather Agent", icon: <FaCloud className="text-[9px]" />, bg: "rgba(59, 130, 246, 0.07)", color: "#2563eb", borderColor: "rgba(59, 130, 246, 0.12)" };
    case "calendar":
      return { label: "Calendar Agent", icon: <FaCalendarAlt className="text-[9px]" />, bg: "rgba(16, 185, 129, 0.07)", color: "#059669", borderColor: "rgba(16, 185, 129, 0.12)" };
    case "hotel":
      return { label: "Hotel Agent", icon: <FaBuilding className="text-[9px]" />, bg: "rgba(245, 158, 11, 0.07)", color: "#d97706", borderColor: "rgba(245, 158, 11, 0.12)" };
    case "restaurant":
      return { label: "Restaurant Agent", icon: <FaUtensils className="text-[9px]" />, bg: "rgba(239, 68, 68, 0.07)", color: "#dc2626", borderColor: "rgba(239, 68, 68, 0.12)" };
    case "nearby":
      return { label: "Attractions Agent", icon: <FaMapMarkerAlt className="text-[9px]" />, bg: "rgba(167, 139, 250, 0.07)", color: "#7c3aed", borderColor: "rgba(167, 139, 250, 0.12)" };
    default:
      return { label: "General Chat", icon: <FaRobot className="text-[9px]" />, bg: "rgba(156, 163, 175, 0.07)", color: "#4b5563", borderColor: "rgba(156, 163, 175, 0.12)" };
  }
}

const PROGRESS_STEPS = [
  { current: "🔍 Finding hotels...", done: "✅ Hotels found" },
  { current: "🍽️ Finding restaurants...", done: "✅ Restaurants found" },
  { current: "🌤️ Checking weather...", done: "✅ Weather updated" },
  { current: "🗺️ Creating itinerary...", done: "✅ Done" }
];

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [savedTrips, setSavedTrips] = useState<Record<number, { tripName: string; loading: boolean }>>({});
  const [mapModalUrl, setMapModalUrl] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let interval: any;
    if (loading) {
      setProgressStep(0);
      interval = setInterval(() => {
        setProgressStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 700);
    } else {
      setProgressStep(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const saveItinerary = async (index: number, text: string) => {
    setSavedTrips(prev => ({
      ...prev,
      [index]: { tripName: "", loading: true }
    }));
    
    try {
      const res = await axios.post("http://localhost:8000/calendar/save", {
        itinerary_text: text
      });
      if (res.data.success) {
        setSavedTrips(prev => ({
          ...prev,
          [index]: { tripName: res.data.trip_name, loading: false }
        }));
      } else {
        alert("Failed to save itinerary: " + res.data.message);
        setSavedTrips(prev => {
          const updated = { ...prev };
          delete updated[index];
          return updated;
        });
      }
    } catch (err) {
      console.error(err);
      alert("Error communicating with calendar backend.");
      setSavedTrips(prev => {
        const updated = { ...prev };
        delete updated[index];
        return updated;
      });
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const askAI = async (text?: string) => {
    const userQuestion = text || question;
    if (!userQuestion.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: userQuestion }]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/chat", {
        question: userQuestion,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.data.answer, routes: res.data.routes },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Something went wrong. Please try again." },
      ]);
    }

    setLoading(false);
  };

  const startVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    setIsListening(true);

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      setQuestion(text);
      setTimeout(() => askAI(text), 500);
    };

    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.start();
  };

  return (
    <div className="h-screen flex bg-[#F5F4F0] text-[#1a1a1a] font-sans">

      {/* ── Sidebar ── */}
      <aside className="w-64 bg-white border-r border-black/[0.08] flex flex-col flex-shrink-0">

        {/* Logo */}
        <div className="p-5 border-b border-black/[0.07]">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[#1D9E75] to-[#185FA5] rounded-full px-4 py-2">
            <FaMapMarkerAlt className="text-white text-sm" />
            <span className="text-white text-sm font-medium tracking-wide">
              Tourist AI
            </span>
          </div>
        </div>

        {/* New Chat */}
        <div className="p-3">
          <button
            onClick={() => setMessages([])}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg border border-black/10 text-sm text-gray-600 hover:bg-gray-50 hover:border-black/20 transition-all duration-150"
          >
            <FaPlus className="text-xs text-gray-400" />
            New chat
          </button>
        </div>

        {/* Examples */}
        <div className="px-4 pb-2">
          <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-2">
            Try asking
          </p>
          <div className="space-y-1">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.text}
                onClick={() => askAI(ex.text)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg border border-black/[0.06] text-xs text-gray-500 hover:bg-gray-50 hover:text-gray-800 hover:border-black/10 transition-all duration-150 text-left"
              >
                <span className="text-[#1D9E75] text-xs flex-shrink-0">
                  {ex.icon}
                </span>
                {ex.text}
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-auto p-4 border-t border-black/[0.07] flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-gray-100 border border-black/10 flex items-center justify-center">
            <FaUser className="text-[11px] text-gray-400" />
          </div>
          <span className="text-xs text-gray-500 flex-1">Traveller</span>
          <FaCog className="text-xs text-gray-300 cursor-pointer hover:text-gray-400 transition-colors" />
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Topbar */}
        <header className="h-14 bg-white border-b border-black/[0.07] flex items-center justify-between px-5 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-[#1D9E75] flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-gray-800">
                Tourist AI Assistant
              </p>
              <p className="text-[11px] text-gray-400">
                Powered by AI · Tamil Nadu & beyond
              </p>
            </div>
          </div>
          <FaRobot className="text-gray-300 text-base" />
        </header>

        {/* Chat */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
                   style={{ background: "linear-gradient(135deg, rgba(29,158,117,0.1) 0%, rgba(24,95,165,0.1) 100%)", border: "1px solid rgba(29,158,117,0.2)" }}>
                <FaMapMarkerAlt className="text-2xl text-[#1D9E75]" />
              </div>
              <h1 className="text-2xl font-medium text-gray-800 mb-2">
                Where to next?
              </h1>
              <p className="text-sm text-gray-400 max-w-xs leading-relaxed">
                Ask about hotels, restaurants, weather, or full trip plans — anywhere in India.
              </p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2.5 ${
                  msg.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    msg.role === "assistant"
                      ? "text-white"
                      : "bg-gray-100 border border-black/10"
                  }`}
                  style={
                    msg.role === "assistant"
                      ? { background: "linear-gradient(135deg, #1D9E75 0%, #185FA5 100%)" }
                      : {}
                  }
                >
                  {msg.role === "assistant" ? (
                    <FaRobot className="text-[11px]" />
                  ) : (
                    <FaUser className="text-[11px] text-gray-400" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[72%] px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "text-white rounded-2xl rounded-br-[4px]"
                      : "bg-white border border-black/[0.07] text-gray-800 rounded-2xl rounded-bl-[4px]"
                  }`}
                  style={
                    msg.role === "user"
                      ? { background: "linear-gradient(135deg, #1D9E75 0%, #0F6E56 100%)" }
                      : {}
                  }
                >
                  {msg.role === "user" ? (
                    msg.text
                  ) : (
                    <>
                      <MarkdownContent text={msg.text} />
                      {msg.routes && msg.routes.filter(r => r !== "merge" && r !== "general").length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3 pt-2 border-t border-black/[0.05]">
                          {msg.routes.filter(r => r !== "merge" && r !== "general").map((route) => {
                            const badgeInfo = getBadgeInfo(route);
                            return (
                              <span
                                key={route}
                                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium border"
                                style={{
                                  backgroundColor: badgeInfo.bg,
                                  color: badgeInfo.color,
                                  borderColor: badgeInfo.borderColor,
                                }}
                              >
                                {badgeInfo.icon}
                                {badgeInfo.label}
                              </span>
                            );
                          })}
                        </div>
                      )}
                      
                      {msg.routes && msg.routes.includes("calendar") && (
                        <div className="mt-3 pt-2 border-t border-black/[0.05] flex items-center gap-2 flex-wrap">
                          {!savedTrips[i] && (
                            <button
                              onClick={() => saveItinerary(i, msg.text)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-black/10 text-[10px] font-medium text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer"
                            >
                              <FaPlus className="text-[8px]" /> Save Itinerary to Calendar
                            </button>
                          )}
                          {savedTrips[i] && savedTrips[i].loading && (
                            <span className="text-[10px] font-medium text-gray-500 animate-pulse">
                              ⏳ Saving to database...
                            </span>
                          )}
                          {savedTrips[i] && !savedTrips[i].loading && (
                            <>
                              <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600">
                                ✓ Saved: "{savedTrips[i].tripName}"
                              </span>
                              <a
                                href={`http://localhost:8000/calendar/export?trip_name=${encodeURIComponent(savedTrips[i].tripName)}`}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-600 hover:text-blue-700 transition-colors ml-2"
                              >
                                Download Calendar (.ics)
                              </a>
                            </>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Thinking indicator */}
          {loading && (
            <div className="flex gap-2.5">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-white"
                style={{ background: "linear-gradient(135deg, #1D9E75 0%, #185FA5 100%)" }}
              >
                <FaRobot className="text-[11px]" />
              </div>
              <div className="bg-white border border-black/[0.07] px-4 py-3 rounded-2xl rounded-bl-[4px] flex flex-col gap-1.5 min-w-[220px]">
                <div className="flex items-center gap-1.5 mb-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-[#1D9E75] animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <div className="space-y-1 text-xs">
                  {PROGRESS_STEPS.map((step, idx) => {
                    if (progressStep < idx) return null;
                    const isDone = progressStep > idx;
                    return (
                      <div
                        key={idx}
                        className={`flex items-center gap-1.5 transition-opacity duration-300 ${
                          isDone ? "text-emerald-600 font-medium" : "text-gray-500 animate-pulse"
                        }`}
                      >
                        <span>{isDone ? step.done : step.current}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-black/[0.07] p-4 flex-shrink-0">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-2 bg-gray-50 border border-black/[0.09] rounded-xl px-3 py-2 focus-within:border-[#1D9E75] focus-within:ring-1 focus-within:ring-[#1D9E75]/20 transition-all duration-150">
              <FaSearch className="text-gray-300 text-xs flex-shrink-0" />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") askAI(); }}
                placeholder="Ask about your trip…"
                className="flex-1 bg-transparent outline-none text-sm text-gray-800 placeholder-gray-400"
              />
              <button
                onClick={startVoice}
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-150 ${
                  isListening
                    ? "bg-red-50 text-red-500 animate-pulse"
                    : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                }`}
                aria-label="Voice input"
              >
                <FaMicrophone className="text-xs" />
              </button>
              <button
                onClick={() => askAI()}
                className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-white transition-opacity hover:opacity-85"
                style={{ background: "linear-gradient(135deg, #1D9E75 0%, #185FA5 100%)" }}
                aria-label="Send"
              >
                <FaPaperPlane className="text-xs" />
              </button>
            </div>
            <p className="text-center text-[11px] text-gray-400 mt-2">
              {isListening
                ? "🎤 Listening…"
                : "Click the microphone to speak, or type your question"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
