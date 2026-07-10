import React, { useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { FaTimes } from "react-icons/fa";

const API_BASE = "http://localhost:8000";

// leaflet default icon fix (safe to run once)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type PlaceModal = {
  name: string;
  city: string;
  lat: number | null;
  lon: number | null;
  history: string;
  wikiUrl?: string;
  source?: "db" | "wikipedia" | "llm" | "google";
  loading: boolean;
};

/** Inline markdown for bold / italic / code / links */
function InlineMd({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const regex =
    /(\[([^\]]+)\]\(([^)]+)\))|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)|(`([^`]+)`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[1]) {
      const href = m[3];
      const isPlace = href.startsWith("place://");
      parts.push(
        <a
          key={key++}
          href={href}
          {...(isPlace ? { "data-place-link": "true" } : { target: "_blank", rel: "noreferrer" })}
          className="text-teal-600 hover:underline"
        >
          {m[2]}
        </a>
      );
    } else if (m[4]) parts.push(<strong key={key++} className="font-bold text-slate-900 dark:text-white">{m[5]}</strong>);
    else if (m[6]) parts.push(<em key={key++}>{m[7]}</em>);
    else if (m[8]) parts.push(<code key={key++} className="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[11px]">{m[9]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

export default function DiscoverMarkdown({
  text,
}: {
  text: string;
}) {
  const [modal, setModal] = useState<PlaceModal | null>(null);

  const openPlace = async (raw: string) => {
    const decoded = decodeURIComponent(raw);
    const [name, city, latStr, lonStr] = decoded.split("|");
    const lat = latStr ? Number(latStr) : null;
    const lon = lonStr ? Number(lonStr) : null;

    setModal({ name, city, lat, lon, history: "", loading: true });

    try {
      const res = await axios.get(`${API_BASE}/api/place`, { params: { name, city } });
      const d = res.data;
      setModal({
        name: d.name ?? name,
        city: d.city ?? city,
        lat: d.lat ?? lat ?? null,
        lon: d.lon ?? lon ?? null,
        history: d.history || "No description available.",
        wikiUrl: d.wikiUrl,
        source: d.source,
        loading: false,
      });
    } catch {
      setModal({
        name,
        city,
        lat,
        lon,
        history: "Could not load details.",
        loading: false,
      });
    }
  };

  const handleLinkClick = (e: React.MouseEvent, href: string) => {
    if (href.startsWith("place://")) {
      e.preventDefault();
      openPlace(href.replace("place://", ""));
    }
  };

  // ----- render markdown -----
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  const imgRe = /^!\[([^\]]*)\]\(([^)]+)\)$/;
  const linkedImgRe = /^\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)$/;
  const linkedHeadingRe = /^(#{1,3})\s+\[([^\]]+)\]\(([^)]+)\)$/;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Gallery block from backend: <!-- gallery:start --> ... <!-- gallery:end -->
    if (trimmed === "<!-- gallery:start -->") {
      const cards: React.ReactNode[] = [];
      i++;
      while (i < lines.length && lines[i].trim() !== "<!-- gallery:end -->") {
        const li = lines[i].trim().match(linkedImgRe);
        if (li) {
          const [, alt, src, href] = li;
          cards.push(
            <a
              key={key++}
              href={href}
              onClick={(e) => handleLinkClick(e, href)}
              className="block rounded-xl overflow-hidden border border-black/10 dark:border-white/10 hover:opacity-90 transition"
            >
              <img
                src={src}
                alt={alt}
                onError={(e) => {
                  (e.currentTarget.parentElement as HTMLElement).style.display = "none";
                }}
                className="w-full h-40 object-cover"
              />
            </a>
          );
        }
        i++;
      }
      i++; // consume gallery:end
      if (cards.length) {
        elements.push(
          <div key={key++} className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-3">
            {cards}
          </div>
        );
      }
      continue;
    }

    if (!trimmed) {
      i++;
      continue;
    }

    // Linked image
    const linked = trimmed.match(linkedImgRe);
    if (linked) {
      const [, alt, src, href] = linked;
      elements.push(
        <a
          key={key++}
          href={href}
          onClick={(e) => handleLinkClick(e, href)}
          className="block my-3"
        >
          <img
            src={src}
            alt={alt}
            onError={(e) => {
              (e.currentTarget.parentElement as HTMLElement).style.display = "none";
            }}
            className="rounded-lg border border-black/[0.07] dark:border-white/10 max-w-full h-auto hover:opacity-90 transition cursor-pointer"
          />
        </a>
      );
      i++;
      continue;
    }

    // Plain image
    const img = trimmed.match(imgRe);
    if (img) {
      const [, alt, src] = img;
      elements.push(
        <img
          key={key++}
          src={src}
          alt={alt}
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
          className="my-3 rounded-lg border border-black/[0.07] dark:border-white/10 max-w-full h-auto"
        />
      );
      i++;
      continue;
    }

    // Linked heading (### [1. Name (info)](place://...))
    const lh = trimmed.match(linkedHeadingRe);
    if (lh) {
      const [, hashes, txt, href] = lh;
      const level = hashes.length;
      const anchor = (
        <a
          href={href}
          onClick={(e) => handleLinkClick(e, href)}
          className="hover:underline text-slate-900 dark:text-slate-100"
        >
          {txt}
        </a>
      );
      const heading =
        level === 1 ? (
          <h1 className="text-2xl font-bold mt-5 mb-2">{anchor}</h1>
        ) : level === 2 ? (
          <h2 className="text-xl font-semibold mt-5 mb-2">{anchor}</h2>
        ) : (
          <h3 className="text-lg font-semibold mt-4 mb-2">{anchor}</h3>
        );

      elements.push(
        <div key={key++}>
          {heading}
        </div>
      );
      i++;
      continue;
    }

    // Plain headings
    if (/^# /.test(line)) {
      elements.push(
        <h1 key={key++} className="text-2xl font-bold mt-5 mb-2">
          <InlineMd text={line.replace(/^# /, "")} />
        </h1>
      );
      i++;
      continue;
    }
    if (/^## /.test(line)) {
      elements.push(
        <h2 key={key++} className="text-xl font-semibold mt-5 mb-2">
          <InlineMd text={line.replace(/^## /, "")} />
        </h2>
      );
      i++;
      continue;
    }
    if (/^### /.test(line)) {
      elements.push(
        <h3 key={key++} className="text-lg font-semibold mt-4 mb-2">
          <InlineMd text={line.replace(/^### /, "")} />
        </h3>
      );
      i++;
      continue;
    }

    // Bullet list
    if (/^[-*] /.test(line)) {
      const bullets: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        bullets.push(lines[i].replace(/^[-*] /, ""));
        i++;
      }
      elements.push(
        <ul key={key++} className="my-2 space-y-1">
          {bullets.map((b, bi) => (
            <li key={bi} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
              <span className="text-teal-600">•</span>
              <span className="flex-1"><InlineMd text={b} /></span>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered list
    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, ""));
        i++;
      }
      elements.push(
        <ol key={key++} className="my-2 space-y-1">
          {items.map((it, ii) => (
            <li key={ii} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
              <span className="font-bold text-teal-600">{ii + 1}.</span>
              <span className="flex-1"><InlineMd text={it} /></span>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    if (trimmed === "---") {
      elements.push(<hr key={key++} className="my-4 border-slate-200 dark:border-slate-800" />);
      i++;
      continue;
    }

    // Paragraph
    elements.push(
      <p key={key++} className="my-2 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
        <InlineMd text={line} />
      </p>
    );
    i++;
  }

  return (
    <div
      onClick={(e) => {
        const t = e.target as HTMLElement;
        const a = t.closest("a[data-place-link]") as HTMLAnchorElement | null;
        if (a) {
          e.preventDefault();
          openPlace(a.getAttribute("href")!.replace("place://", ""));
        }
      }}
    >
      {elements}

      {/* Place modal with Leaflet map */}
      {modal && (
        <div
          className="fixed inset-0 z-[100] bg-black/60 flex items-center justify-center p-4"
          onClick={() => setModal(null)}
        >
          <div
            className="bg-white dark:bg-[#111827] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between p-5 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{modal.name}</h3>
                {modal.city && <p className="text-xs text-slate-500 mt-0.5">{modal.city}</p>}
              </div>
              <button
                onClick={() => setModal(null)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                aria-label="Close"
              >
                <FaTimes />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="h-64 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800">
                {modal.lat != null && modal.lon != null ? (
                  <MapContainer
                    center={[modal.lat, modal.lon]}
                    zoom={13}
                    style={{ height: "100%", width: "100%" }}
                  >
                    <TileLayer
                      attribution='&copy; OpenStreetMap contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={[modal.lat, modal.lon]}>
                      <Popup>{modal.name}</Popup>
                    </Marker>
                  </MapContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-500">
                    Location unavailable
                  </div>
                )}
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-2">History</h4>
                {modal.loading ? (
                  <p className="text-xs text-slate-500">Loading…</p>
                ) : (
                  <>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {modal.history}
                    </p>
                    {modal.source === "llm" && (
                      <p className="text-[10px] text-amber-600 mt-2">⚠ AI-generated, verify.</p>
                    )}
                    {modal.wikiUrl && (
                      <a
                        href={modal.wikiUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-block mt-3 text-xs text-teal-600 hover:underline"
                      >
                        Read more on Wikipedia →
                      </a>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
