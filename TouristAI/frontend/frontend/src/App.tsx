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
    <div className="flex h-screen bg-white text-gray-900">
      <aside className="w-64 border-r border-black/10 p-4 flex flex-col gap-4">
        <div className="flex items-center gap-2 font-semibold">
          <FaRobot /> Tourist AI
        </div>
        <button onClick={() => setMessages([])}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-black/10 text-sm text-gray-600 hover:bg-gray-50">
          <FaPlus /> New chat
        </button>
        <div className="text-xs uppercase text-gray-400 tracking-wide">Try asking</div>
        <div className="flex flex-col gap-1">
          {EXAMPLES.map((ex) => (
            <button key={ex.text} onClick={() => askAI(ex.text)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-600 hover:bg-gray-50 text-left">
              {ex.icon}{ex.text}
            </button>
          ))}
        </div>
        <div className="mt-auto text-xs text-gray-500 flex items-center gap-2">
          <FaUser /> Traveller
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="px-6 py-4 border-b border-black/10 flex items-center gap-3">
          <FaRobot className="text-xl text-gray-700" />
          <div>
            <div className="font-semibold">Tourist AI Assistant</div>
            <div className="text-xs text-gray-500">Powered by AI · Tamil Nadu & beyond</div>
          </div>
        </header>

        <section className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center mt-16">
              <FaSearch className="mx-auto text-3xl text-gray-400" />
              <div className="text-xl font-semibold mt-3">Where to next?</div>
              <div className="text-sm text-gray-500 mt-1">
                Ask about hotels, restaurants, weather, or full trip plans — anywhere in India.
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 flex-shrink-0">
                  {msg.role === "assistant" ? <FaRobot /> : <FaUser />}
                </div>
                <div className="flex-1">
                  {msg.role === "user" ? (
                    <p className="text-sm">{msg.text}</p>
                  ) : (
                    <>
                      <MarkdownContent text={msg.text} onPlaceClick={openPlace} />
                      {msg.routes && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {msg.routes.filter((r) => r !== "merge" && r !== "general").map((r) => {
                            const b = getBadgeInfo(r);
                            return (
                              <span key={r} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full"
                                    style={{ background: `${b.color}15`, color: b.color }}>
                                {b.icon} {b.label}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && <div className="text-sm text-gray-500">Thinking…</div>}
          <div ref={chatEndRef} />
        </section>

        <footer className="p-4 border-t border-black/10">
          <div className="flex items-center gap-2 px-3 py-2 border border-black/10 rounded-xl">
            <FaSearch className="text-gray-400" />
            <input value={question} onChange={(e) => setQuestion(e.target.value)}
                   onKeyDown={(e) => e.key === "Enter" && askAI()}
                   placeholder="Ask about your trip…"
                   className="flex-1 bg-transparent outline-none text-sm" />
            <button onClick={startVoice} className={`w-8 h-8 rounded-lg flex items-center justify-center ${isListening ? "text-red-500" : "text-gray-500"}`}>
              <FaMicrophone />
            </button>
            <button onClick={() => askAI()}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white"
                    style={{ background: "linear-gradient(135deg,#1D9E75 0%,#185FA5 100%)" }}>
              <FaPaperPlane />
            </button>
          </div>
        </footer>
      </main>
      {/* Nearby Explorer Sidebar */}
<aside className="w-[360px] border-l border-gray-200 bg-gray-50 overflow-y-auto">
  <NearbyExplorer />
</aside>

      {modal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setModal(null)}>
          <div className="bg-white rounded-2xl w-[90%] max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between p-4 border-b border-black/10">
              <div>
                <h2 className="text-lg font-semibold">{modal.name}</h2>
                {modal.city && <p className="text-xs text-gray-500">{modal.city}</p>}
              </div>
              <button onClick={() => setModal(null)} className="text-gray-500 hover:text-gray-800"><FaTimes /></button>
            </div>

            <div className="h-64 w-full">
              {modal.lat != null && modal.lon != null ? (
                <MapContainer center={[modal.lat, modal.lon]} zoom={14} style={{ height: "100%", width: "100%" }}>
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                             attribution='&copy; OpenStreetMap' />
                  <Marker position={[modal.lat, modal.lon]}>
                    <Popup>{modal.name}</Popup>
                  </Marker>
                </MapContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-gray-500">Location unavailable</div>
              )}
            </div>

            <div className="p-4 overflow-y-auto">
              <h3 className="font-semibold mb-2">History</h3>
              {modal.loading ? (
                <p className="text-sm text-gray-500">Loading…</p>
              ) : (
                <>
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{modal.history}</p>
                  {modal.source === "llm" && (
  <small className="text-amber-600">⚠ AI-generated, verify.</small>
)}
                  {modal.wikiUrl && (
                    <a href={modal.wikiUrl} target="_blank" rel="noreferrer"
                       className="inline-block mt-3 text-sm text-blue-600 hover:underline">
                      Read more on Wikipedia →
                    </a>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
