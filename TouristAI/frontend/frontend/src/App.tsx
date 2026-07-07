import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { TravelPlannerProvider } from "./context/TravelPlannerContext";
import Navigation from "./components/layout/Navigation";
import TopBar from "./components/layout/TopBar";
import Home from "./pages/Home";
import AIChat from "./pages/AIChat";
import TripPlanner from "./pages/TripPlanner";
import SavedTrips from "./pages/SavedTrips";
import Profile from "./pages/Profile";

function AppContent() {
import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  FaPaperPlane, FaRobot, FaPlus, FaMicrophone, FaUser,
  FaMapMarkerAlt, FaCloud, FaUtensils, FaCalendarAlt,
  FaBuilding, FaCog, FaSearch, FaTimes,
} from "react-icons/fa";
import CrowdMeter from "./components/CrowdMeter";
import NearbyExplorer from "./components/NearbyExplorer";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type Message = { role: "user" | "assistant"; text: string; routes?: string[] };
// type PlaceModal = {
//   name: string; city: string; lat: number | null; lon: number | null;
//   history: string; wikiUrl?: string; loading: boolean;
// };
type PlaceModal = {
  name: string; city: string;
  lat: number | null; lon: number | null;
  history: string;
  wikiUrl?: string;
  source?: "db" | "wikipedia" | "llm" | "google";
  loading: boolean;
};

function InlineMd({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const regex = /(\[([^\]]+)\]\(([^)]+)\))|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)|(`([^`]+)`)/g;
  let last = 0; let m: RegExpExecArray | null; let key = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[1]) {
      const href = m[3];
      parts.push(
        <a key={key++} href={href} data-place-link={href.startsWith("place://") ? "1" : undefined}
           target={href.startsWith("place://") ? undefined : "_blank"} rel="noreferrer"
           className="text-blue-600 hover:underline">{m[2]}</a>
      );
    } else if (m[4]) parts.push(<strong key={key++}>{m[5]}</strong>);
    else if (m[6]) parts.push(<em key={key++}>{m[7]}</em>);
    else if (m[8]) parts.push(<code key={key++} className="px-1 bg-gray-100 rounded text-xs">{m[9]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

function MarkdownContent({
  text, onPlaceClick,
}: { text: string; onPlaceClick: (raw: string) => void }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0; let key = 0;

  const imgRe = /^!\[([^\]]*)\]\(([^)]+)\)$/;
  const linkedImgRe = /^\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)$/;
  const linkedHeadingRe = /^(#{1,3})\s+\[([^\]]+)\]\(([^)]+)\)$/;

  const handleLinkClick = (e: React.MouseEvent, href: string) => {
    if (href.startsWith("place://")) { e.preventDefault(); onPlaceClick(href.replace("place://", "")); }
  };

  // Parse "name|city|lat|lon" out of a place:// href
  const parsePlaceHref = (href: string) => {
    if (!href.startsWith("place://")) return null;
    const [name, city] = decodeURIComponent(href.replace("place://", "")).split("|");
    return { name: name || "", city: city || "" };
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed === "<!-- gallery:start -->") {
      const cards: React.ReactNode[] = [];
      i++;
      while (i < lines.length && lines[i].trim() !== "<!-- gallery:end -->") {
        const l = lines[i].trim();
        const li = l.match(linkedImgRe);
        if (li) {
          const [, alt, src, href] = li;
          cards.push(
            <a key={key++} href={href} onClick={(e) => handleLinkClick(e, href)}
               className="block rounded-xl overflow-hidden border border-black/10 hover:opacity-90 transition">
              <img src={src} alt={alt}
                   onError={(e) => { (e.currentTarget.parentElement as HTMLElement).style.display = "none"; }}
                   className="w-full h-40 object-cover" />
            </a>
          );
        }
        i++;
      }
      i++;
      if (cards.length) {
        elements.push(
          <div key={key++} className="grid grid-cols-2 md:grid-cols-3 gap-3 my-4">{cards}</div>
        );
      }
      continue;
    }

    if (!trimmed) { i++; continue; }

    const linked = trimmed.match(linkedImgRe);
    if (linked) {
      const [, alt, src, href] = linked;
      elements.push(
        <a key={key++} href={href} onClick={(e) => handleLinkClick(e, href)} className="block my-3">
          <img src={src} alt={alt}
               onError={(e) => { (e.currentTarget.parentElement as HTMLElement).style.display = "none"; }}
               className="rounded-lg border border-black/[0.07] max-w-full h-auto hover:opacity-90 transition cursor-pointer" />
        </a>
      );
      i++; continue;
    }

    const img = trimmed.match(imgRe);
    if (img) {
      const [, alt, src] = img;
      elements.push(
        <img key={key++} src={src} alt={alt}
             onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
             className="my-3 rounded-lg border border-black/[0.07] max-w-full h-auto" />
      );
      i++; continue;
    }

    const lh = trimmed.match(linkedHeadingRe);
    if (lh) {
      const [, hashes, txt, href] = lh;
      const level = hashes.length;
      const cls =
        level === 1 ? "text-2xl font-bold mt-5 mb-2 text-gray-900" :
        level === 2 ? "text-xl font-semibold mt-5 mb-2 text-gray-900" :
                      "text-lg font-semibold mt-4 mb-2 text-gray-900";
      const anchor = (
        <a href={href} onClick={(e) => handleLinkClick(e, href)}
           className="hover:underline text-gray-900">{txt}</a>
      );
      const place = parsePlaceHref(href);
      const heading =
        level === 1 ? <h1 className={cls}>{anchor}</h1> :
        level === 2 ? <h2 className={cls}>{anchor}</h2> :
                      <h3 className={cls}>{anchor}</h3>;
      elements.push(
        <div key={key++}>
          {heading}
          {place && place.name && place.city && (
            <div className="my-2">
              <CrowdMeter city={place.city} attraction={place.name} />
            </div>
          )}
        </div>
      );
      i++; continue;
    }

    if (/^# /.test(line)) {
      elements.push(<h1 key={key++} className="text-2xl font-bold mt-5 mb-2 text-gray-900"><InlineMd text={line.replace(/^# /, "")} /></h1>);
      i++; continue;
    }
    if (/^## /.test(line)) {
      elements.push(<h2 key={key++} className="text-xl font-semibold mt-5 mb-2 text-gray-900"><InlineMd text={line.replace(/^## /, "")} /></h2>);
      i++; continue;
    }
    if (/^### /.test(line)) {
      elements.push(<h3 key={key++} className="text-lg font-semibold mt-4 mb-2 text-gray-900"><InlineMd text={line.replace(/^### /, "")} /></h3>);
      i++; continue;
    }

    if (/^[-*] /.test(line)) {
      const bullets: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        bullets.push(lines[i].replace(/^[-*] /, "")); i++;
      }
      elements.push(
        <ul key={key++} className="my-2 space-y-1">
          {bullets.map((b, bi) => (
            <li key={bi} className="flex gap-2 text-sm text-gray-800">
              <span>•</span><span><InlineMd text={b} /></span>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, "")); i++;
      }
      elements.push(
        <ol key={key++} className="my-2 space-y-1">
          {items.map((it, ii) => (
            <li key={ii} className="flex gap-2 text-sm text-gray-800">
              <span>{ii + 1}.</span><span><InlineMd text={it} /></span>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    if (trimmed === "---") { elements.push(<hr key={key++} className="my-4 border-gray-200" />); i++; continue; }

    elements.push(
      <p key={key++} className="my-2 text-sm text-gray-800 leading-relaxed">
        <InlineMd text={line} />
      </p>
    );
    i++;
  }

  return (
    <div onClick={(e) => {
      const t = e.target as HTMLElement;
      const a = t.closest("a[data-place-link]") as HTMLAnchorElement | null;
      if (a) { e.preventDefault(); onPlaceClick(a.getAttribute("href")!.replace("place://", "")); }
    }}>
      {elements}
    </div>
  );
}

const EXAMPLES = [
  { icon: <FaBuilding />, text: "Best hotels in Madurai" },
  { icon: <FaUtensils />, text: "Restaurants near Meenakshi Temple" },
  { icon: <FaCalendarAlt />, text: "3 day trip plan for Chennai" },
];

function getBadgeInfo(route: string) {
  switch (route) {
    case "weather":    return { label: "Weather Agent",     icon: <FaCloud />,        color: "#2563eb" };
    case "calendar":   return { label: "Calendar Agent",    icon: <FaCalendarAlt />,  color: "#059669" };
    case "hotel":      return { label: "Hotel Agent",       icon: <FaBuilding />,     color: "#d97706" };
    case "restaurant": return { label: "Restaurant Agent",  icon: <FaUtensils />,     color: "#dc2626" };
    case "nearby":     return { label: "Attractions Agent", icon: <FaMapMarkerAlt />, color: "#7c3aed" };
    default:           return { label: "General Chat",      icon: <FaRobot />,        color: "#4b5563" };
  }
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [modal, setModal] = useState<PlaceModal | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const askAI = async (text?: string) => {
    const userQuestion = text || question;
    if (!userQuestion.trim()) return;
    setMessages((prev) => [...prev, { role: "user", text: userQuestion }]);
    setQuestion(""); setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/chat", { question: userQuestion });
      setMessages((prev) => [...prev, { role: "assistant", text: res.data.answer, routes: res.data.routes }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Something went wrong. Please try again." }]);
    }
    setLoading(false);
  };

  const startVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return alert("Speech Recognition is not supported.");
    const rec = new SR(); rec.lang = "en-US"; setIsListening(true);
    rec.onresult = (e: any) => { const t = e.results[0][0].transcript; setQuestion(t); setTimeout(() => askAI(t), 400); };
    rec.onend = () => setIsListening(false); rec.onerror = () => setIsListening(false);
    rec.start();
  };

  // const openPlace = async (raw: string) => {
  //   const decoded = decodeURIComponent(raw);
  //   const [name, city, latStr, lonStr] = decoded.split("|");
  //   let lat = latStr ? parseFloat(latStr) : NaN;
  //   let lon = lonStr ? parseFloat(lonStr) : NaN;
  //   setModal({ name, city, lat: isNaN(lat) ? null : lat, lon: isNaN(lon) ? null : lon, history: "", loading: true });

  //   if (isNaN(lat) || isNaN(lon)) {
  //     try {
  //       const g = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(name + ", " + city)}`);
  //       if (g.data?.[0]) { lat = parseFloat(g.data[0].lat); lon = parseFloat(g.data[0].lon); }
  //     } catch {}
  //   }

  //   let history = "No description available."; let wikiUrl: string | undefined;
  //   try {
  //     const s = await axios.get(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(name)}`);
  //     if (s.data?.extract) { history = s.data.extract; wikiUrl = s.data.content_urls?.desktop?.page; }
  //   } catch {}

  //   setModal({ name, city, lat: isNaN(lat) ? null : lat, lon: isNaN(lon) ? null : lon, history, wikiUrl, loading: false });
  // };

  const openPlace = async (raw: string) => {
  // const [name, city] = decodeURIComponent(raw).split("|");
  const decoded = decodeURIComponent(raw);

const [
    name,
    city,
    latStr,
    lonStr
] = decoded.split("|");

const lat =
latStr ? Number(latStr) : null;

const lon =
lonStr ? Number(lonStr) : null;
  // setModal({ name, city, lat: null, lon: null, history: "", loading: true });
  setModal({
    name,
    city,
    lat,
    lon,
    history:"",
    loading:true
});

  try {
    const res = await axios.get("http://localhost:8000/api/place", {
      params: { name, city },
    });
    const d = res.data;
    setModal({
      name: d.name ?? name,
      city: d.city ?? city,
      lat: d.lat ?? null,
      lon: d.lon ?? null,
      history: d.history || "No description available.",
      wikiUrl: d.wikiUrl,
      source: d.source,
      loading: false,
    });
  } catch {
    setModal({ name, city, lat: null, lon: null,
      history: "Could not load details.", loading: false });
  }
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

function App() {
  return (
    <TravelPlannerProvider>
      <Router>
        <AppContent />
      </Router>
    </TravelPlannerProvider>
  );
}

export default App;
