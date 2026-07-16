import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Send, Mic, Image, Sparkles, Bot, User, Cloud, Hotel, Utensils, Compass, ArrowRight, Loader, Info, Calendar, DollarSign, Users, Sun, MapPin, Star, ExternalLink, Phone, CreditCard, Accessibility, CheckCircle2, ChevronDown, Volume2, VolumeX, Edit3, Save, Eye, Coffee, Clock, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import type { TripDetails } from "../context/TravelPlannerContext";
import { ImageOff } from "lucide-react";
import type { NearbyResult } from "../context/TravelPlannerContext";//added this import fro nearbyagent

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");

const stripMarkdown = (value: string) =>
  value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1");

const formatInlineMarkdown = (value: string) => {
  let html = escapeHtml(value);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-teal-600 underline decoration-teal-500/50 underline-offset-2">$1</a>');
  html = html.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-teal-600 underline decoration-teal-500/50 underline-offset-2">$1</a>');
  return html.replace(/\n/g, "<br />");
};

function ImageSlider({ images }: { images: string[] }) {
  const swiperRef = useRef<any>(null);
  const showNav = images.length > 3;

  return (
    <div className="my-2 flex justify-center px-3">
      <div className="relative w-full max-w-[400px]">
        <Swiper
          modules={[Navigation, Pagination]}
          onSwiper={(swiper) => (swiperRef.current = swiper)}
          slidesPerView={3}
          spaceBetween={6}
          pagination={{ clickable: true }}
          loop={showNav}
        >
          {images.map((img, index) => (
            <SwiperSlide key={index}>
              <img src={img} alt={`Photo ${index + 1}`} className="h-24 w-full rounded-lg object-cover" loading="lazy" />
            </SwiperSlide>
          ))}
        </Swiper>

        {showNav && (
          <>
            <button
              onClick={() => swiperRef.current?.slidePrev()}
              aria-label="Previous"
              className="absolute left-0 top-1/2 z-10 flex h-6 w-6 -translate-x-2 -translate-y-1/2 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-300 shadow-md hover:bg-slate-700"
            >
              <ChevronLeft className="text-[9px]" />
            </button>
            <button
              onClick={() => swiperRef.current?.slideNext()}
              aria-label="Next"
              className="absolute right-0 top-1/2 z-10 flex h-6 w-6 translate-x-2 -translate-y-1/2 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-300 shadow-md hover:bg-slate-700"
            >
              <ChevronRight className="text-[9px]" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}


// function PlaceMedia({
//   image,
//   googlePhotoName,
//   name,
// }: {
//   image: string | null;
//   googlePhotoName?: string | null;
//   name: string;
// }) {
//   const [failed, setFailed] = React.useState(false);

//   // Priority: Wikipedia image -> Google Places photo (proxied) -> placeholder
//   const src = !failed && image
//     ? image
//     : googlePhotoName
//       ? `${import.meta.env.VITE_API_BASE_URL ?? ""}/place-photo?photo_name=${encodeURIComponent(googlePhotoName)}`
//       : null;

//   return (
//     <div className="aspect-video w-full bg-slate-800 overflow-hidden">
//       {src ? (
//         <img
//           src={src}
//           alt={name}
//           className="h-full w-full object-cover"
//           loading="lazy"
//           onError={() => setFailed(true)}
//         />
//       ) : (
//         <div className="flex h-full w-full items-center justify-center text-slate-500">
//           <ImageOff className="h-8 w-8" />
//         </div>
//       )}
//     </div>
//   );
// }

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

const googlePhotoUrl = (photoName: string) =>
  `${API_BASE_URL}/place-photo?photo_name=${encodeURIComponent(
    photoName
  )}&maxwidth=800`;

function PlaceMedia({
  image,
  googlePhotoName,
  name,
}: {
  image: string | null;
  googlePhotoName?: string | null;
  name: string;
}) {
  const sources = React.useMemo(() => {
    const next: string[] = [];

    if (googlePhotoName) {
      next.push(googlePhotoUrl(googlePhotoName));
    }

    if (image && !next.includes(image)) {
      next.push(image);
    }

    return next;
  }, [googlePhotoName, image]);
  const [sourceIndex, setSourceIndex] = React.useState(0);
  const source = sources[sourceIndex];

  React.useEffect(() => {
    setSourceIndex(0);
  }, [googlePhotoName, image]);

  return (
    <div className="aspect-video w-full bg-slate-800 overflow-hidden">
      {source ? (
        <img
          src={source}
          alt={name}
          className="h-full w-full object-cover"
          loading="lazy"
          onError={() => setSourceIndex((current) => current + 1)}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-slate-500">
          <ImageOff className="h-8 w-8" />
        </div>
      )}
    </div>
  );
}


function PlaceInfoTabs({ place }: { place: any }) {
  const [tab, setTab] = React.useState<"overview" | "info" | "access">("overview");
  const acc = place.accessibility || {};
  const accEntries = Object.entries(acc).filter(([, v]) => v === true);

  const tabs: { key: typeof tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "info",     label: "Info" },
    { key: "access",   label: "Access" },
  ];

  return (
    <div className="mt-2 rounded-md border border-slate-700/60 min-w-0">
      <div className="grid grid-cols-3 border-b border-slate-700/60">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`min-w-0 truncate whitespace-nowrap px-1 py-1.5 text-[10px] font-medium transition-colors ${
              tab === t.key
                ? "text-teal-400 border-b-2 border-teal-400"
                : "text-slate-400 border-b-2 border-transparent hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-2 text-[11px] leading-snug text-slate-300 break-words">
        {tab === "overview" && (
          <p className="line-clamp-4">{place.description || "No overview available."}</p>
        )}
        {tab === "info" && (
          <ul className="space-y-1">
            {place.address && <li className="line-clamp-2">📍 {place.address}</li>}
            {place.phone && <li>📞 {place.phone}</li>}
            {place.hours?.length ? <li className="line-clamp-1">🕒 {place.hours[0]}</li> : null}
            {place.priceLevel && <li>💰 {place.priceLevel}</li>}
            {!place.address && !place.phone && !place.hours?.length && !place.priceLevel && (
              <li className="text-slate-500">No details available.</li>
            )}
          </ul>
        )}
        {tab === "access" && (
          accEntries.length ? (
            <ul className="space-y-0.5">
              {accEntries.map(([k]) => (
                <li key={k} className="capitalize">♿ {k.replace(/([A-Z])/g, " $1").toLowerCase()}</li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500">No accessibility info.</p>
          )
        )}
      </div>
    </div>
  );
}

function NearbyDiscovery({ data }: { data: NearbyResult }) {
  if (!data?.categories?.length) {
    return (
      <p className="text-sm text-slate-300">
        Couldn't find places for <b>{data?.location}</b>. Try another city.
      </p>
    );
  }

  return (
    <div className="space-y-6 text-left">
      <p className="text-sm text-slate-300">
        <span className="font-semibold text-slate-100">
          {data.location}
        </span>
        {" "}— here are the top places to explore by category:
      </p>

      {data.categories.map((cat) => (
        <section key={cat.key} className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-100">
            <span className="text-lg">{cat.icon}</span>
            {cat.label}
            <span className="text-[10px] font-normal text-slate-500">
              ({cat.places.length})
            </span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {cat.places.map((p) => (
              <div
                key={p.id}
                className="rounded-xl overflow-hidden border border-slate-700/70 bg-slate-900 hover:shadow-md transition flex flex-col"
              >
                {p.wikiUrl ? (
                  <a
                    href={p.wikiUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {/* <PlaceMedia image={p.image} name={p.name} /> */}
                    <PlaceMedia
                      image={p.image}
                      googlePhotoName={p.googlePhotoName}
                      name={p.name}
                    />
                  </a>
                ) : (
                  // <PlaceMedia image={p.image}  name={p.name} />
                  <PlaceMedia
                    image={p.image}
                    googlePhotoName={p.googlePhotoName}
                    name={p.name}
                  />
                )}

                <div className="p-2.5 flex flex-col gap-1 flex-1">
                  <div className="flex items-start justify-between gap-1.5">
                    <h4 className="text-[12px] font-semibold leading-tight text-slate-100 line-clamp-2">
                      {p.name}
                    </h4>

                    {p.rating != null && (
                      <span className="text-[10px] text-yellow-400 shrink-0">
                        ★ {p.rating.toFixed(1)}
                      </span>
                    )}
                  </div>

                  {p.description && (
                    <p className="text-[10.5px] text-slate-400 line-clamp-2">
                      {p.description}
                    </p>
                  )}

                  {p.address && (
                    <p className="text-[10px] text-slate-500 line-clamp-1 mt-auto pt-1">
                      {p.address}
                    </p>
                  )}

                  <PlaceInfoTabs place={p} />

                  {/* {p.wikiUrl && (
                    <a
                      href={p.wikiUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-teal-400 hover:underline"
                    >
                      {p.wikiSearchFallback ? "Search Wikipedia →" : "Read history on Wikipedia →"}
                    </a>
                  )} */}

                <div className="mt-2 flex flex-wrap gap-3 text-[10px]">
  {p.mapsUrl ? (
    <a
      href={p.mapsUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-400 hover:underline"
    >
      📍 View Map
    </a>
  ) : p.address ? (
    <a
      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
        p.address
      )}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-400 hover:underline"
    >
      📍 View Map
    </a>
  ) : null}

  {p.wikiUrl ? (
    <a
      href={p.wikiUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-400 hover:underline"
    >
      📖 Read on Wikipedia →
    </a>
  ) : (
    <a
      href={`https://en.wikipedia.org/w/index.php?search=${encodeURIComponent(
        p.name
      )}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-400 hover:underline"
    >
      📖 Search Wikipedia →
    </a>
  )}

  {p.website && (
    <a
      href={p.website}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-400 hover:underline"
    >
      🌐 Website
    </a>
  )}
</div>

                </div>
              </div>
            ))}
          </div>
        </section>
      ))}

      <p className="text-sm text-slate-200 pt-2 border-t border-slate-800">
        {data.followUp ??
          `How many days are you planning to spend in ${data.location}? I can put together the best itinerary for you.`}
      </p>
    </div>
  );
}//added new code upto this line 177

function PlaceCard({ lines }: { lines: string[] }) {
  const [tab, setTab] = useState<"overview" | "info" | "accessibility" | "paymentOptions" | "parkingOptions" | "dining">("overview");
  const [hoursOpen, setHoursOpen] = useState(false);

  const title = stripMarkdown(lines[0] || "").replace(/^\d+\.\s*/, "").trim();
  const details = lines.slice(1).filter(Boolean);
  const imageRegex = /!\[.*?\]\((.*?)\)/;
  const mapRegex = /\[View Map\]\((.*?)\)/;
  const websiteRegex = /\[Visit Website\]\((.*?)\)/;

  const images = details.map((line) => line.match(imageRegex)?.[1]).filter(Boolean) as string[];
  const mapUrl = details.find((line) => mapRegex.test(line))?.match(mapRegex)?.[1];
  const websiteUrl = details.find((line) => websiteRegex.test(line))?.match(websiteRegex)?.[1];

  const otherDetails = details.filter((line) => !imageRegex.test(line) && !mapRegex.test(line) && !websiteRegex.test(line));
  const ratingLine = otherDetails.find((l) => /⭐|★/.test(l));
  const locationLine = otherDetails.find((l) => /📍/.test(l));
  const hoursLines = otherDetails.filter((l) => /🕒/.test(l));
  const phoneLine = otherDetails.find((l) => /📞|phone/i.test(l));
  const paymentLine = otherDetails.find((l) => /💳/.test(l));
  const parkingLine = otherDetails.find((l) => /🅿/.test(l));
  const accessibilityLine = otherDetails.find((l) => /♿/.test(l));
  const priceLine = otherDetails.find((l) => !/compare prices/i.test(l) && (/₹/.test(l) || /price level/i.test(l) || /💰/.test(l)) && l !== ratingLine && l !== locationLine);
  const otaLine = otherDetails.find((l) => /🔎|compare prices/i.test(l));

  const remaining = otherDetails.filter((l) => l !== ratingLine && l !== locationLine && l !== priceLine && l !== phoneLine && !hoursLines.includes(l) && l !== paymentLine && l !== accessibilityLine && l !== parkingLine && l !== otaLine);
  const diningKeywords = /(serves|available|serves breakfast|serves lunch|serves dinner|serves beer|serves wine|serves vegetarian|takeout|delivery|dine-in|breakfast restaurant|🍽️|🍳|🥗|🍺|🍷|🥦|🥡|🚚|🍴)/i;
  const diningLines = remaining.filter((l) => diningKeywords.test(l));
  const descriptionLines = remaining.filter((l) => l.replace(/^\W+/, "").length > 45);
  const amenityLines = remaining.filter((l) => !descriptionLines.includes(l) && !diningLines.includes(l));

  let ratingValue = "";
  let reviewCount = "";
  if (ratingLine) {
    const ratingMatch = ratingLine.match(/(\d+(?:\.\d+)?)/);
    ratingValue = ratingMatch ? ratingMatch[1] : "";
    const reviewMatch = ratingLine.match(/(\d+)\s*review/i);
    reviewCount = reviewMatch ? reviewMatch[1] : "";
  }

  const PRICE_LEVEL_MAP: Record<string, string> = {
    FREE: "Free",
    INEXPENSIVE: "Inexpensive",
    MODERATE: "Moderate",
    EXPENSIVE: "Expensive",
    VERY_EXPENSIVE: "Very Expensive",
  };

  let priceValue = "";
  const priceSource = priceLine || ratingLine || "";
  const rupeeMatch = priceSource.match(/₹+/);
  if (rupeeMatch) {
    priceValue = rupeeMatch[0];
  } else {
    const levelMatch = priceSource.match(/PRICE_LEVEL_([A-Z_]+)/i);
    if (levelMatch) {
      priceValue = PRICE_LEVEL_MAP[levelMatch[1].toUpperCase()] || levelMatch[1];
    }
  }

  const locationText = locationLine ? stripMarkdown(locationLine).replace(/📍/g, "").replace(/^\s*Address:\s*/i, "").trim() : "";
  const phoneText = phoneLine ? stripMarkdown(phoneLine).replace(/📞/g, "").replace(/^\s*Phone:\s*/i, "").trim() : "";
  const paymentText = paymentLine ? stripMarkdown(paymentLine).replace(/💳/g, "").trim() : "";
  const parkingText = parkingLine ? stripMarkdown(parkingLine).replace(/🅿/g, "").trim() : "";
  const accessibilityText = accessibilityLine ? stripMarkdown(accessibilityLine).replace(/♿/g, "").trim() : "";

  let websiteDomain = "";
  try {
    websiteDomain = websiteUrl ? new URL(websiteUrl).hostname : "";
  } catch {
    websiteDomain = "";
  }
  const websiteLogo = websiteDomain ? `https://www.google.com/s2/favicons?sz=128&domain=${websiteDomain}` : "";

  const todayHours = hoursLines[0] ? hoursLines[0].replace(/🕒\s*Hours?:?\s*/i, "") : "";
  const isOpen = /open/i.test(todayHours) || amenityLines.some((l) => /✅|open now/i.test(l));
  const hasAmenities = amenityLines.length > 0;

  const otaLinks = otaLine
    ? Array.from(otaLine.matchAll(/\[(.*?)\]\((.*?)\)/g)).map((match) => ({
        name: match[1],
        url: match[2],
        logo: `https://www.google.com/s2/favicons?sz=64&domain=${match[1].toLowerCase().replace(/\s/g, "").replace(".com", "").trim()}.com`,
      }))
    : [];

  return (
    <div className="my-4 max-w-[420px] overflow-hidden rounded-2xl border border-slate-700/70 bg-slate-900 text-left shadow-sm">
      <div className="p-3.5 text-left">
        <div className="flex items-start justify-between gap-2.5">
          <div className="min-w-0 flex-1 text-left">
            <h3 className="text-left text-sm font-semibold leading-snug text-slate-100" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(title) }} />
            {(ratingValue || priceValue) && (
              <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-slate-400">
                {ratingValue && (
                  <>
                    <Star className="h-3 w-3 fill-current text-yellow-400" />
                    <span className="font-semibold text-slate-100">{ratingValue}</span>
                  </>
                )}
                {ratingValue && priceValue && <span className="text-slate-600">|</span>}
                {priceValue && <span className="font-semibold text-emerald-400">{priceValue}</span>}
                {(ratingValue || priceValue) && reviewCount && <span className="text-slate-600">|</span>}
                {reviewCount && <span>{reviewCount} Reviews</span>}
              </div>
            )}

            {hoursLines.length > 0 && (
              <button
                onClick={() => setHoursOpen(!hoursOpen)}
                className={`mt-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${isOpen ? "bg-emerald-500/15 text-emerald-400" : "bg-slate-800 text-slate-300"}`}
              >
                {todayHours || "Hours"}
                <ChevronDown className={`text-[9px] transition-transform ${hoursOpen ? "rotate-180" : ""}`} />
              </button>
            )}
            {hoursOpen && hoursLines.length > 0 && (
              <div className="mt-1.5 space-y-0.5 pl-1 text-[11px] leading-relaxed text-slate-400">
                {hoursLines.map((line, idx) => (
                  <div key={idx}>{stripMarkdown(line).replace(/🕒\s*Hours?:?\s*/i, "")}</div>
                ))}
              </div>
            )}
          </div>

          {websiteUrl && (
            <a href={websiteUrl} target="_blank" rel="noreferrer" className="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg border border-slate-700 bg-slate-800 shadow-sm">
              {websiteLogo ? <img src={websiteLogo} alt="Website" className="h-6 w-6 object-contain" /> : <ExternalLink className="h-4 w-4 text-slate-300" />}
            </a>
          )}
        </div>
      </div>

      {images.length > 0 && (
        <>
          <div className="border-t border-slate-700/70" />
          <div className="bg-slate-800/60">
            <ImageSlider images={images} />
          </div>
        </>
      )}

      {hasAmenities && (
        <div className="flex border-t border-slate-700/70">
          <button onClick={() => setTab("overview")} className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${tab === "overview" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
            Overview
          </button>
          <button onClick={() => setTab("info")} className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${tab === "info" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
            Information
          </button>
          {accessibilityText && (
            <button onClick={() => setTab("accessibility")} className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${tab === "accessibility" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
              Accessibility
            </button>
          )}
          {paymentLine && (
            <button onClick={() => setTab("paymentOptions")} className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${tab === "paymentOptions" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
              Payment
            </button>
          )}
          {parkingLine && (
            <button onClick={() => setTab("parkingOptions")} className={`flex-1 truncate py-2 text-[11px] font-semibold transition-colors ${tab === "parkingOptions" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
              Parking
            </button>
          )}
          {diningLines.length > 0 && (
            <button onClick={() => setTab("dining")} className={`flex-1 truncate py-2 text-[11px] font-semibold transition-colors ${tab === "dining" ? "border-b-2 border-[#1D9E75] text-slate-100" : "border-b-2 border-transparent text-slate-500"}`}>
              Dining
            </button>
          )}
        </div>
      )}

      <div className="px-3.5 py-2.5">
        {tab === "overview" ? (
          <div className="space-y-2 text-left">
            {descriptionLines.map((line, i) => (
              <p key={i} className="text-left text-[11.5px] leading-relaxed text-slate-400" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(line)) }} />
            ))}
            {locationText && (
              <div className="flex items-start gap-1.5 text-[11px] text-slate-400">
                <MapPin className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-500" />
                <span className="flex-1" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(locationText) }} />
              </div>
            )}
            {phoneText && (
              <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <Phone className="h-3.5 w-3.5 flex-shrink-0 text-slate-500" />
                <span>{phoneText}</span>
              </div>
            )}
            {otaLinks.length > 0 && (
              <div className="mt-3 border-t border-slate-700/70 pt-3">
                <p className="mb-2 text-[11px] font-semibold text-slate-200">Compare prices:</p>
                <div className="grid grid-cols-3 gap-2">
                  {otaLinks.map((link) => (
                    <a key={link.name} href={link.url} target="_blank" rel="noreferrer" className="flex items-center justify-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/80 px-2 py-1.5 transition-colors hover:bg-slate-700/80">
                      <img src={link.logo} alt={link.name} className="h-3.5 w-3.5" />
                      <span className="text-[10px] font-medium text-slate-300">{link.name}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : tab === "info" ? (
          <div className="grid grid-cols-2 gap-2">
            {amenityLines.map((line, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0 text-[#1D9E75]" />
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(line.replace(/^[^\w]+/, "").trim())) }} />
              </div>
            ))}
          </div>
        ) : tab === "accessibility" ? (
          <div className="grid grid-cols-2 gap-2">
            {accessibilityText.split(",").map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                <Accessibility className="h-3.5 w-3.5 flex-shrink-0 text-[#1D9E75]" />
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "paymentOptions" ? (
          <div className="grid grid-cols-2 gap-2">
            {paymentText.replace(/^Accepts\s/i, "").split(",").map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                <CreditCard className="h-3.5 w-3.5 flex-shrink-0 text-[#1D9E75]" />
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "parkingOptions" ? (
          <div className="grid grid-cols-2 gap-2">
            {parkingText.replace(/^Parking:\s/i, "").split(",").map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                <MapPin className="h-3.5 w-3.5 flex-shrink-0 text-[#1D9E75]" />
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "dining" ? (
          <div className="grid grid-cols-2 gap-2">
            {diningLines.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                <Utensils className="h-3.5 w-3.5 flex-shrink-0 text-[#1D9E75]" />
                <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(item.replace(/^[^\w]+/, "").trim())) }} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">No details available.</p>
        )}
      </div>

      {(mapUrl || websiteUrl) && (
        <>
          <div className="border-t border-slate-700/70" />
          <div className="flex items-center gap-2 p-2.5">
            {mapUrl && (
              <a href={mapUrl} target="_blank" rel="noreferrer" className="flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[11px] font-semibold text-white transition-opacity hover:opacity-90" style={{ background: "#1D9E75" }}>
                <MapPin className="h-3 w-3" /> View Map
              </a>
            )}
            {websiteUrl && (
              <a href={websiteUrl} target="_blank" rel="noreferrer" className="flex flex-1 items-center justify-center gap-1.5 rounded-md border px-3 py-1.5 text-[11px] font-semibold transition-colors hover:bg-[#1D9E75]/5" style={{ borderColor: "#1D9E75", color: "#1D9E75" }}>
                <ExternalLink className="h-3 w-3" /> Visit Website
              </a>
            )}
          </div>
        </>
      )}
    </div>
  );
}

type ScheduleSection = {
  label: string;
  time?: string;
  content: string[];
};

type ScheduleDay = {
  title: string;
  sections: ScheduleSection[];
};

const getScheduleSectionMeta = (label: string) => {
  const normalized = label.toLowerCase();
  if (normalized.includes("hotel")) return { icon: Hotel, tone: "text-indigo-500 bg-indigo-50 dark:bg-indigo-950/20", label: "Hotel" };
  if (normalized.includes("breakfast")) return { icon: Coffee, tone: "text-amber-500 bg-amber-50 dark:bg-amber-950/20", label: "Breakfast" };
  if (normalized.includes("lunch")) return { icon: Utensils, tone: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20", label: "Lunch" };
  if (normalized.includes("dinner")) return { icon: Utensils, tone: "text-rose-500 bg-rose-50 dark:bg-rose-950/20", label: "Dinner" };
  if (normalized.includes("morning")) return { icon: Sun, tone: "text-sky-500 bg-sky-50 dark:bg-sky-950/20", label: "Morning" };
  if (normalized.includes("afternoon")) return { icon: Clock, tone: "text-orange-500 bg-orange-50 dark:bg-orange-950/20", label: "Afternoon" };
  if (normalized.includes("evening")) return { icon: Moon, tone: "text-violet-500 bg-violet-50 dark:bg-violet-950/20", label: "Evening" };
  return { icon: Compass, tone: "text-teal-500 bg-teal-50 dark:bg-teal-950/20", label };
};

const parseScheduleHeading = (line: string): { label: string; time?: string } | null => {
  const clean = stripMarkdown(line).replace(/^[^\w]+/, "").trim();
  const match = clean.match(/^(Hotel|Breakfast|Morning|Lunch|Afternoon|Evening|Dinner)(?:\s*\(([^)]+)\))?:?$/i);
  if (!match) return null;
  return { label: match[1], time: match[2] };
};

const parseItinerarySchedule = (text: string): ScheduleDay[] => {
  const lines = (text || "").split(/\r?\n/);
  const days: ScheduleDay[] = [];
  let currentDay: ScheduleDay | null = null;
  let currentSection: ScheduleSection | null = null;

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line || line === "---" || line === "--") return;

    const dayMatch = line.match(/^Day\s+\d+/i);
    if (dayMatch) {
      currentDay = { title: dayMatch[0], sections: [] };
      days.push(currentDay);
      currentSection = null;
      return;
    }

    const sectionHeading = parseScheduleHeading(line);
    if (sectionHeading && currentDay) {
      currentSection = { label: sectionHeading.label, time: sectionHeading.time, content: [] };
      currentDay.sections.push(currentSection);
      return;
    }

    if (currentSection) {
      currentSection.content.push(line);
    }
  });

  return days.filter((day) => day.sections.some((section) => section.content.length > 0));
};

function ItinerarySchedule({ days }: { days: ScheduleDay[] }) {
  return (
    <div className="space-y-3">
      {days.map((day) => (
        <section key={day.title} className="overflow-hidden rounded-xl border border-slate-200/70 bg-white text-left shadow-sm dark:border-slate-800 dark:bg-slate-950/30">
          <div className="flex items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-3.5 py-2.5 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center gap-2">
              <Calendar className="h-3.5 w-3.5 text-teal-600" />
              <h3 className="text-xs font-extrabold text-slate-800 dark:text-slate-100">{day.title}</h3>
            </div>
            <span className="text-[10px] font-bold text-slate-400">{day.sections.length} stops</span>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {day.sections.map((section, sectionIndex) => {
              const meta = getScheduleSectionMeta(section.label);
              const Icon = meta.icon;
              return (
                <div key={`${day.title}-${section.label}-${sectionIndex}`} className="grid grid-cols-[2.25rem_1fr] gap-2.5 px-3.5 py-3">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${meta.tone}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-extrabold uppercase tracking-wide text-slate-700 dark:text-slate-200">{meta.label}</span>
                      {section.time && (
                        <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-400">{section.time}</span>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      {section.content.map((item, itemIndex) => (
                        <p
                          key={`${section.label}-${itemIndex}`}
                          className="text-[12px] font-medium leading-relaxed text-slate-600 dark:text-slate-350"
                          dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(item)) }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

function renderStructuredMessage(text: string, skipOptions = false) {
  const lines = (text || "").split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let i = 0;
  const scheduleDays = parseItinerarySchedule(text);

  if (scheduleDays.length > 0) {
    return <ItinerarySchedule days={scheduleDays} />;
  }

  while (i < lines.length) {
    const line = lines[i].trim();

    if (!line) {
      i += 1;
      continue;
    }

    if (skipOptions) {
      const match = line.match(/^(?:[•*\-+]|\d+\.)\s*(.+)$/);
      if (match && match[1]) {
        const optionText = match[1].trim().replace(/[*_~`[\]]/g, "").trim();
        if (optionText.length > 0 && optionText.length < 40) {
          i += 1;
          continue;
        }
      }
    }

    if (/^\d+\.\s+/.test(line)) {
      const cardLines: string[] = [];
      cardLines.push(line.replace(/^\d+\.\s+/, ""));
      i += 1;
      while (i < lines.length && lines[i].trim() && !/^\d+\.\s+/.test(lines[i].trim())) {
        cardLines.push(lines[i].trim());
        i += 1;
      }
      elements.push(<PlaceCard key={`card-${i}`} lines={cardLines} />);
      continue;
    }

    if (/^#{1,3}\s+/.test(line)) {
      const headingLevel = line.match(/^#+/)?.[0].length || 1;
      const headingClass = headingLevel === 1 ? "mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100" : "mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500";
      elements.push(<div key={`h-${i}`} className={headingClass}>{line.replace(/^#{1,3}\s+/, "")}</div>);
      i += 1;
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const bullets: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        bullets.push(lines[i].trim().replace(/^[-*]\s+/, ""));
        i += 1;
      }
      elements.push(
        <ul key={`ul-${i}`} className="ml-4 mt-2 list-disc space-y-1 text-sm text-slate-700 dark:text-slate-300">
          {bullets.map((b, idx) => (
            <li key={idx} dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(b)) }} />
          ))}
        </ul>
      );
      continue;
    }

    elements.push(<p key={`p-${i}`} className="text-sm leading-relaxed text-slate-700 dark:text-slate-300" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(stripMarkdown(line)) }} />);
    i += 1;
  }

  return <div className="space-y-1">{elements}</div>;
}

// Import all dialogs to support buttons inside chat attachment card
import { ModifyDrawer } from "../components/dialogs/ModifyDrawer";
import { SaveDialog } from "../components/dialogs/SaveDialog";
import { CalendarSyncDialog } from "../components/dialogs/CalendarSyncDialog";

const QUESTION_OPTION_SETS = [
  {
    matcher: /what kind of trip do you prefer/i,
    options: ["Family", "Solo", "Friends", "Couple", "Business"]
  },
  {
    matcher: /any special interests/i,
    options: ["History", "Nature", "Adventure", "Food", "Photography", "Shopping"]
  }
];

const getClickableQuestionOptions = (text: string): string[] => {
  const optionSet = QUESTION_OPTION_SETS.find((set) => set.matcher.test(text));
  if (!optionSet) return [];

  const normalizedText = text.toLowerCase();
  return optionSet.options.filter((option) => normalizedText.includes(option.toLowerCase()));
};

export const AIChat: React.FC = () => {
  const navigate = useNavigate();
  const { chatMessages, askAIChat, isLoadingChat, setActiveTrip, saveTrip } = useTravelPlanner();
  
  const [question, setQuestion] = useState("");
  const [selectedDays, setSelectedDays] = useState<number>(3);
  const [selectedTravelers, setSelectedTravelers] = useState<number>(2);
  const [isListening, setIsListening] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // States to handle overlays inside chat card actions
  const [targetTripCard, setTargetTripCard] = useState<TripDetails | null>(null);
  const [isModifyOpen, setIsModifyOpen] = useState(false);
  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);

  // Toast alert status state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Smart Voice-Over Settings
  const [isVoiceOverEnabled, setIsVoiceOverEnabled] = useState(() => {
    return localStorage.getItem("isVoiceOverEnabled") === "true";
  });

  const toggleVoiceOver = () => {
    setIsVoiceOverEnabled((prev) => {
      const next = !prev;
      localStorage.setItem("isVoiceOverEnabled", String(next));
      if (!next && typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  };

  const speakText = (text: string) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      
      // Filter out markdown characters, brackets, URLs, etc. for clear speech synthesis
      const cleanText = text
        .replace(/[*#_~`\[\]()]/g, "")
        .replace(/[-+•]\s+/g, "")
        .replace(/:\s*(\n|$)/g, ". ")
        .replace(/\n+/g, ". ");
        
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Automatically read aloud new incoming assistant messages when voice over is enabled
  useEffect(() => {
    if (chatMessages.length > 0 && isVoiceOverEnabled) {
      const lastMsg = chatMessages[chatMessages.length - 1];
      if (lastMsg.role === "assistant") {
        speakText(lastMsg.text);
      }
    }
  }, [chatMessages.length, isVoiceOverEnabled]);

  // Auto-scroll on messages addition
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isLoadingChat]);

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    if (isVoiceOverEnabled) {
      speakText(msg);
    }
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleSend = async (text?: string) => {
    const queryText = text || question;
    if (!queryText.trim()) return;
    
    setQuestion("");
    await askAIChat(queryText);
  };

  const getAgentBadge = (route: string) => {
    switch (route) {
      case "weather":
        return { label: "Weather Agent", icon: Cloud, color: "text-sky-505 text-sky-600 bg-sky-50 dark:bg-sky-950/20 border-sky-100 dark:border-sky-900/30" };
      case "hotel":
        return { label: "Hotel Agent", icon: Hotel, color: "text-amber-605 text-amber-600 bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30" };
      case "restaurant":
        return { label: "Restaurant Agent", icon: Utensils, color: "text-rose-605 text-rose-600 bg-rose-50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30" };
      case "nearby":
        return { label: "Attractions Agent", icon: Compass, color: "text-purple-605 text-purple-600 bg-purple-50 dark:bg-purple-950/20 border-purple-100 dark:border-purple-900/30" };
      case "budget":
        return { label: "Budget Agent", icon: DollarSign, color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/30" };
      default:
        return { label: "General Chat", icon: Bot, color: "text-slate-500 bg-slate-50 dark:bg-slate-900 border-slate-100 dark:border-slate-800" };
    }
  };

  // Card button trigger actions
  const handleLoadTrip = (trip: TripDetails) => {
    setActiveTrip(trip);
    navigate("/planner");
  };

  const handleCardModify = (trip: TripDetails) => {
    setActiveTrip(trip);
    setTargetTripCard(trip);
    setIsModifyOpen(true);
  };

  const handleCardSave = (trip: TripDetails) => {
    setActiveTrip(trip);
    setTargetTripCard(trip);
    setIsSaveOpen(true);
  };

  const handleSaveOnly = () => {
    if (targetTripCard) {
      saveTrip(targetTripCard);
      setIsSaveOpen(false);
      triggerToast("Trip Saved Successfully!");
    }
  };

  const handleSaveAndSync = () => {
    if (targetTripCard) {
      saveTrip(targetTripCard);
      setIsSaveOpen(false);
      setTimeout(() => {
        setIsSyncOpen(true);
      }, 300);
    }
  };

  // Web Speech API Microphone listener
  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice Speech Recognition is not supported by this browser version.");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    setIsListening(true);

    recognition.onresult = (event: any) => {
      const speechToText = event.results[0][0].transcript;
      setQuestion(speechToText);
      setIsListening(false);
      setTimeout(() => handleSend(speechToText), 800);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const suggestedPrompts = [
    "Plan a 3-day cultural trip to Madurai",
    "Find romantic restaurants in Chennai Marina",
    "4 days adventure itinerary for Goa beach",
    "Weather report for Paris this week"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50/50 dark:bg-[#0b0f19] relative">
      
      {/* Voice-Over Mode Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-200/60 dark:border-slate-800/60 bg-white/55 dark:bg-[#111827]/55 backdrop-blur px-5 py-3 text-left">
        <div>
          <h2 className="text-xs font-bold text-slate-800 dark:text-slate-205 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-teal-605" />
            AI Travel Assistant
          </h2>
        </div>
        <button
          onClick={toggleVoiceOver}
          className={`px-3 py-1.5 rounded-full border text-[10px] font-extrabold flex items-center gap-1.5 transition-all select-none hover-scale ${
            isVoiceOverEnabled
              ? "bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 border-teal-100 dark:border-teal-900/40 shadow-sm"
              : "bg-slate-50 dark:bg-slate-900 text-slate-455 dark:text-slate-400 border-slate-200 dark:border-slate-800"
          }`}
          title="Toggle Smart Voice Notification Aloud Mode"
        >
          {isVoiceOverEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span>{isVoiceOverEnabled ? "Voice notifications ON" : "Voice notifications OFF"}</span>
        </button>
      </div>

      {/* 1. Chat Dialog Log */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 no-scrollbar">
        
        {chatMessages.length === 0 ? (
          /* Landing Empty State */
          <div className="h-full flex flex-col items-center justify-center max-w-md mx-auto text-center space-y-5 py-12">
            <div className="w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-950/20 border border-teal-100/50 dark:border-teal-900/30 flex items-center justify-center text-teal-605">
              <Bot className="w-8 h-8 text-teal-600 dark:text-teal-405 animate-pulse" />
            </div>
            <div>
              <h2 className="font-heading text-lg sm:text-xl font-extrabold text-slate-800 dark:text-slate-100">
                Explore with AI Travel Core
              </h2>
              <p className="text-xs text-slate-455 dark:text-slate-400 mt-1 leading-relaxed">
                Describe your dream location, custom budgets, and durations. Our multi-agent travel core will assemble your itineraries instantly.
              </p>
            </div>

            {/* Suggested prompts list */}
            <div className="w-full space-y-2 pt-2 text-left">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">
                Suggested Prompts
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestedPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="p-3 text-xs text-slate-650 dark:text-slate-355 font-semibold text-left border border-slate-200/60 dark:border-slate-850 bg-white dark:bg-[#111827] rounded-xl hover:border-teal-500 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-all hover-scale"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Active Chat Conversation Log */
          <div className="space-y-6 max-w-3xl mx-auto pb-4">
            {chatMessages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div key={idx} className={`flex gap-3 text-left ${isUser ? "justify-end" : "justify-start"}`}>
                  
                  {/* Assistant Avatar */}
                  {!isUser && (
                    <div className="w-8.5 h-8.5 rounded-xl bg-teal-600 text-white flex items-center justify-center flex-shrink-0 mt-1 shadow-sm shadow-teal-500/10">
                      <Sparkles className="w-4.5 h-4.5" />
                    </div>
                  )}

                  {/* Message bubble wrapper */}
                  <div className="space-y-3.5 max-w-[85%] sm:max-w-[78%]">
                    
                    {/* ChatGPT-style bubbles */}
                    <div
                      className={`relative p-4 rounded-2xl shadow-sm border leading-relaxed ${
                        isUser
                          ? "bg-teal-600 border-teal-650 text-white rounded-br-none"
                          : "bg-white dark:bg-[#111827] border-slate-200/60 dark:border-slate-800 text-slate-700 dark:text-slate-200 rounded-bl-none pr-9"
                      }`}
                    >
                      {/* Read Aloud button for assistant replies */}
                      {!isUser && (
                        <button
                          onClick={() => speakText(msg.text)}
                          className="absolute top-2.5 right-2.5 p-1 rounded-lg text-slate-400 hover:text-teal-605 hover:bg-slate-105 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all hover-scale"
                          title="Read Aloud"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                        </button>
                      )}

                    
                      {/* Message Content */}
{!isUser && msg.nearbyResult ? (
  <NearbyDiscovery data={msg.nearbyResult} />
) : !isUser ? (
  renderStructuredMessage(msg.text)
) : null}
                      {isUser && (
                        <p className="text-xs sm:text-sm whitespace-pre-line font-medium leading-relaxed">
                          {msg.text}
                        </p>
                      )}

                      {!isUser && idx === chatMessages.length - 1 && (() => {
                        const options = getClickableQuestionOptions(msg.text);
                        if (options.length === 0) return null;

                        return (
                          <div className="mt-3.5 flex flex-wrap gap-2 border-t border-slate-100 pt-3 text-left dark:border-slate-800/80">
                            {options.map((option) => (
                              <button
                                key={option}
                                onClick={() => handleSend(option)}
                                className="min-h-8 rounded-lg border border-teal-100/60 bg-teal-50 px-3 py-1.5 text-[11px] font-extrabold text-teal-700 shadow-sm transition-all hover:bg-teal-100 dark:border-teal-900/40 dark:bg-teal-950/20 dark:text-teal-400 dark:hover:bg-teal-900/40"
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        );
                      })()}

                      {/* Timestamps */}
                      <span className={`block text-[9px] mt-2 text-right ${isUser ? "text-slate-200/80" : "text-slate-400"}`}>
                        {msg.timestamp || "10:15 AM"}
                      </span>

                      {/* Enabled Agent Chips */}
                      {msg.routes && msg.routes.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                          {msg.routes.map((rt) => {
                            const badge = getAgentBadge(rt);
                            const Icon = badge.icon;
                            return (
                              <span
                                key={rt}
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${badge.color}`}
                              >
                                <Icon className="w-3 h-3" />
                                {badge.label}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Premium Inline Trip Summary Card Attachment */}
                    {msg.tripCard && (
                      <motion.div
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="rounded-2xl overflow-hidden border border-slate-200/60 dark:border-slate-800/85 bg-white dark:bg-[#111827] shadow-md text-left"
                      >
                        {/* City Cover Image */}
                        <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
                          <img
                            src={msg.tripCard.bannerImage}
                            alt={msg.tripCard.cityName}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/85 to-transparent" />
                          <div className="absolute bottom-3 left-4 text-white text-left">
                            <span className="text-[9px] font-bold text-teal-400 bg-teal-950/60 backdrop-blur-sm px-2.5 py-0.5 rounded border border-teal-500/20 uppercase tracking-wider mb-1 inline-block">
                              Itinerary Deck
                            </span>
                            <h4 className="font-heading font-extrabold text-sm sm:text-base tracking-tight leading-none">
                              {msg.tripCard.cityName}
                            </h4>
                          </div>
                        </div>

                        {/* Itinerary specifications Grid */}
                        <div className="p-4 grid grid-cols-2 gap-3 text-xs border-b border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10">
                          <div className="flex items-center gap-1.5 font-semibold text-slate-600 dark:text-slate-350">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.durationDays} Days Plan</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-600 dark:text-slate-350">
                            <Users className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.travelersCount} Travelers</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-650 dark:text-slate-350">
                            <DollarSign className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.budget} Budget</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-650 dark:text-slate-350">
                            <Sun className="w-4 h-4 text-amber-500" />
                            <span>Sunny Forecast</span>
                          </div>
                          <div className="col-span-2 flex items-center gap-1 font-bold text-teal-700 dark:text-teal-405 text-xs pt-1 border-t border-slate-200/40 dark:border-slate-800/40">
                            <span>Estimated cost: </span>
                            <span>₹{typeof msg.tripCard.estimatedCost === 'number' ? msg.tripCard.estimatedCost.toLocaleString('en-IN') : msg.tripCard.estimatedCost} INR</span>
                          </div>
                        </div>

                        {/* Summary Deck Actions */}
                        <div className="p-3 bg-white dark:bg-[#111827]">
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <span className="text-[10px] font-extrabold uppercase tracking-wide text-slate-400">Plan actions</span>
                            <span className="text-[10px] font-semibold text-slate-400">Open full planner for editing and schedule view</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center sm:justify-end">
                          <button
                            onClick={() => handleCardModify(msg.tripCard!)}
                            title="Edit trip preferences and stops"
                            className="min-h-9 justify-center px-3 py-2 border border-slate-205 dark:border-slate-800 text-slate-600 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold flex items-center gap-1.5 hover-scale"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                            Edit Plan
                          </button>
                          
                          <button
                            onClick={() => handleCardSave(msg.tripCard!)}
                            title="Save this trip"
                            className="min-h-9 justify-center px-3 py-2 border border-slate-205 dark:border-slate-800 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold flex items-center gap-1.5 hover-scale"
                          >
                            <Save className="h-3.5 w-3.5" />
                            Save Trip
                          </button>

                          <button
                            onClick={() => handleLoadTrip(msg.tripCard!)}
                            title="Open the complete itinerary workspace"
                            className="min-h-9 justify-center px-3.5 py-2 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-[10.5px] font-bold flex items-center gap-1.5 hover-scale shadow-sm sm:min-w-32"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            Open Planner
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* User Avatar */}
                  {isUser && (
                    <div className="w-8.5 h-8.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                      <User className="w-4.5 h-4.5" />
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}

        {/* AI Typing / Agent Core Thinking Loader */}
        {isLoadingChat && (
          <div className="flex gap-3 text-left max-w-3xl mx-auto">
            <div className="w-8 h-8 rounded-xl bg-teal-650 bg-teal-600 text-white shadow-sm flex items-center justify-center flex-shrink-0 mt-1">
              <Sparkles className="w-4 h-4 animate-spin-slow" />
            </div>
            
            <div className="bg-white dark:bg-[#111827] border border-slate-200/50 dark:border-slate-800/80 p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-3">
              <Loader className="w-4.5 h-4.5 text-teal-650 text-teal-600 animate-spin" />
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  AI Travel Agent is planning...
                </span>
                
                {/* Typing Streaming Indicators */}
                <div className="flex items-center gap-1">
                  {[0, 1, 2].map((dot) => (
                    <span
                      key={dot}
                      className="w-1.5 h-1.5 rounded-full bg-teal-600 dark:bg-teal-405 animate-bounce"
                      style={{ animationDelay: `${dot * 0.15}s` }}
                    />
                  ))}
                  <span className="text-[10px] text-slate-400 ml-1 font-bold animate-pulse">Streaming reply</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="bg-white dark:bg-[#111827] border-t border-slate-200/60 dark:border-slate-800/60 p-4 flex-shrink-0">
        <div className="max-w-3xl mx-auto space-y-3">
          
          {/* Dynamic Calendar Picker for Travel Date Selection */}
          {(() => {
            const lastMsg = chatMessages[chatMessages.length - 1];
            const isDateQuestion = lastMsg && lastMsg.role === "assistant" && (
              lastMsg.text.toLowerCase().includes("when are you planning to travel") ||
              lastMsg.text.toLowerCase().includes("when do you plan to travel") ||
              lastMsg.text.toLowerCase().includes("travel date") ||
              lastMsg.text.toLowerCase().includes("start date")
            );
            
            if (!isDateQuestion) return null;

            return (
              <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-teal-50/40 dark:bg-teal-950/15 border border-teal-100/50 dark:border-teal-900/30 text-left justify-between animate-fadeIn mb-2">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-teal-600" />
                  <span className="text-[11px] font-bold text-teal-700 dark:text-teal-400">Select Travel Start Date:</span>
                </div>
                <input
                  type="date"
                  min={new Date().toISOString().split("T")[0]}
                  onChange={(e) => {
                    if (e.target.value) {
                      setQuestion(e.target.value);
                      setTimeout(() => {
                        handleSend(e.target.value);
                      }, 100);
                    }
                  }}
                  className="px-2.5 py-1 bg-white dark:bg-[#1f2937] border border-slate-200 dark:border-slate-800 rounded-lg text-[11px] font-bold text-slate-700 dark:text-slate-300 focus:outline-none focus:border-teal-500 cursor-pointer"
                />
              </div>
            );
          })()}
          
          {/* Dynamic Quantity Selector for Stay Duration */}
          {(() => {
            const lastMsg = chatMessages[chatMessages.length - 1];
            const isDaysQuestion = lastMsg && lastMsg.role === "assistant" && (
              lastMsg.text.toLowerCase().includes("how many days") ||
              lastMsg.text.toLowerCase().includes("duration of your stay") ||
              lastMsg.text.toLowerCase().includes("how long do you plan to stay")
            );
            
            if (!isDaysQuestion) return null;

            return (
              <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-teal-50/40 dark:bg-teal-950/15 border border-teal-100/50 dark:border-teal-900/30 text-left justify-between animate-fadeIn mb-2">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-teal-600" />
                  <span className="text-[11px] font-bold text-teal-700 dark:text-teal-400">Specify Stay Duration:</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSelectedDays(prev => Math.max(1, prev - 1))}
                    className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-805 bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-extrabold flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors"
                  >
                    -
                  </button>
                  <span className="text-[11px] font-extrabold text-slate-700 dark:text-slate-300 w-12 text-center select-none">
                    {selectedDays} {selectedDays === 1 ? "Day" : "Days"}
                  </span>
                  <button
                    onClick={() => setSelectedDays(prev => Math.min(30, prev + 1))}
                    className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-805 bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-extrabold flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors"
                  >
                    +
                  </button>
                  <button
                    onClick={() => {
                      setQuestion(selectedDays.toString());
                      setTimeout(() => {
                        handleSend(selectedDays.toString());
                      }, 100);
                    }}
                    className="ml-2 px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-[10px] font-bold shadow-sm transition-colors"
                  >
                    Confirm
                  </button>
                </div>
              </div>
            );
          })()}
          
          {/* Dynamic Quantity Selector for Travelers Count */}
          {(() => {
            const lastMsg = chatMessages[chatMessages.length - 1];
            const isTravelersQuestion = lastMsg && lastMsg.role === "assistant" && (
              lastMsg.text.toLowerCase().includes("how many people") ||
              lastMsg.text.toLowerCase().includes("number of people") ||
              lastMsg.text.toLowerCase().includes("how many travelers") ||
              lastMsg.text.toLowerCase().includes("number of travelers")
            );
            
            if (!isTravelersQuestion) return null;

            return (
              <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-teal-50/40 dark:bg-teal-950/15 border border-teal-100/50 dark:border-teal-900/30 text-left justify-between animate-fadeIn mb-2">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-teal-600" />
                  <span className="text-[11px] font-bold text-teal-700 dark:text-teal-400">Specify Traveler Count:</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSelectedTravelers(prev => Math.max(1, prev - 1))}
                    className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-805 bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-extrabold flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors"
                  >
                    -
                  </button>
                  <span className="text-[11px] font-extrabold text-slate-700 dark:text-slate-300 w-16 text-center select-none">
                    {selectedTravelers} {selectedTravelers === 1 ? "Person" : "People"}
                  </span>
                  <button
                    onClick={() => setSelectedTravelers(prev => Math.min(20, prev + 1))}
                    className="w-7 h-7 rounded-lg border border-slate-200 dark:border-slate-805 bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-extrabold flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors"
                  >
                    +
                  </button>
                  <button
                    onClick={() => {
                      setQuestion(selectedTravelers.toString());
                      setTimeout(() => {
                        handleSend(selectedTravelers.toString());
                      }, 100);
                    }}
                    className="ml-2 px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-[10px] font-bold shadow-sm transition-colors"
                  >
                    Confirm
                  </button>
                </div>
              </div>
            );
          })()}
          
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-3 py-2 rounded-xl focus-within:border-teal-500 focus-within:ring-1 focus-within:ring-teal-500/20 transition-all duration-150 shadow-inner">
            
            {/* Attachment mock */}
            <button
              className="p-2 rounded-lg text-slate-400 hover:text-slate-655 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Upload Image File"
            >
              <Image className="w-4.5 h-4.5" />
            </button>

            {/* Input field */}
            <input
              type="text"
              placeholder={isListening ? "Listening... Speak your request" : "Describe where to go, budget, sights..."}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              className="flex-1 bg-transparent border-none outline-none text-xs sm:text-sm text-slate-700 dark:text-slate-305 placeholder-slate-405 font-medium"
            />

            {/* Web Speech voice */}
            <button
              onClick={toggleListening}
              className={`p-2 rounded-lg transition-colors ${
                isListening
                  ? "bg-red-50 text-red-500 dark:bg-red-950/20 animate-pulse"
                  : "text-slate-400 hover:text-slate-655 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
              aria-label="Speech to Text"
            >
              <Mic className="w-4.5 h-4.5" />
            </button>

            {/* Send */}
            <button
              onClick={() => handleSend()}
              className="p-2 rounded-lg bg-teal-650 bg-teal-600 text-white hover:bg-teal-700 transition-colors shadow-sm"
              aria-label="Send query"
            >
              <Send className="w-4 h-4" />
            </button>

          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-400 px-1 font-semibold">
            <span>{isListening ? "🎤 Web Speech Listening Active" : "Google Cloud powered travel agents"}</span>
            <span className="flex items-center gap-1">
              <Info className="w-3.5 h-3.5" />
              Markdown details supported
            </span>
          </div>

        </div>
      </div>

      {/* ── MODAL WORKFLOW DRAWERS ── */}
      {targetTripCard && (
        <>
          <ModifyDrawer
            isOpen={isModifyOpen}
            onClose={() => setIsModifyOpen(false)}
            onSaveSuccess={() => triggerToast("Itinerary modifications saved!")}
          />

          <SaveDialog
            isOpen={isSaveOpen}
            onClose={() => setIsSaveOpen(false)}
            onSaveOnly={handleSaveOnly}
            onSaveAndSync={handleSaveAndSync}
          />

          <CalendarSyncDialog
            isOpen={isSyncOpen}
            onClose={() => setIsSyncOpen(false)}
            tripName={targetTripCard.cityName}
          />

        </>
      )}

      {/* ── TOAST NOTIFICATION ALERTS ── */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-55 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-xs font-bold text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 border-slate-850 dark:border-slate-200/50"
          >
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
export default AIChat;