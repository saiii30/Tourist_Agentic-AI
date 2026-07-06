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
  FaParking,
  FaStar,
  FaConciergeBell,
  FaChevronLeft,
  FaChevronRight,
  FaChevronDown,
  FaPhone,
  FaCheckCircle,
  FaCreditCard,
  FaWheelchair,
} from "react-icons/fa";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination } from "swiper/modules";

import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";
import "./App.css";
type Message = {
  role: "user" | "assistant";
  text: string;
  routes?: string[];
};

type ConversationSummary = {
  id: number;
  title: string;
  created_at?: string;
};

function ImageSlider({ images }: { images: string[] }) {
  const swiperRef = useRef<any>(null);
  const showNav = images.length > 3;

  return (
    <div className="flex justify-center my-2 px-3">
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
              <img
                src={img}
                alt={`Photo ${index + 1}`}
                className="w-full h-24 object-cover rounded-lg"
                loading="lazy"
              />
            </SwiperSlide>
          ))}
        </Swiper>

        {showNav && (
          <>
            <button
              onClick={() => swiperRef.current?.slidePrev()}
              aria-label="Previous"
              className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 z-10 w-6 h-6 rounded-full bg-white shadow-md border border-black/10 flex items-center justify-center text-gray-600 hover:bg-gray-50"
            >
              <FaChevronLeft className="text-[9px]" />
            </button>
            <button
              onClick={() => swiperRef.current?.slideNext()}
              aria-label="Next"
              className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 z-10 w-6 h-6 rounded-full bg-white shadow-md border border-black/10 flex items-center justify-center text-gray-600 hover:bg-gray-50"
            >
              <FaChevronRight className="text-[9px]" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ==========================================================
// PlaceCard — redesigned to match the "Grand Pavilion" mock:
// Title / rating / address up top, brand logo badge top-right,
// image carousel, description paragraph, then a filled "View
// Map" button next to an outlined "Visit Website" button.
// ==========================================================
function PlaceCard({ lines }: { lines: string[] }) {
  const [tab, setTab] = useState<"overview" | "info" | "accessibility" | "parkingOptions" | "paymentOptions" | "dining">("overview");
  const [hoursOpen, setHoursOpen] = useState(false);

  const title = lines[0] || "";
  const details = lines.slice(1);

  const imageRegex = /!\[.*?\]\((.*?)\)/;
  const mapRegex = /\[View Map\]\((.*?)\)/;
  const websiteRegex = /\[Visit Website\]\((.*?)\)/;

  const images = details.map(line => line.match(imageRegex)?.[1]).filter(Boolean) as string[];
  const mapUrl = details.find(line => mapRegex.test(line))?.match(mapRegex)?.[1];
  const websiteUrl = details.find(line => websiteRegex.test(line))?.match(websiteRegex)?.[1];

  const otherDetails = details.filter(line =>
    !imageRegex.test(line) && !mapRegex.test(line) && !websiteRegex.test(line)
  );

  const ratingLine = otherDetails.find(l => /⭐|★/.test(l));
  const locationLine = otherDetails.find(l => /📍/.test(l));
  const hoursLines = otherDetails.filter(l => /🕒/.test(l));
  const phoneLine = otherDetails.find(l => /📞|phone/i.test(l));
  const paymentLine = otherDetails.find(l => /💳/.test(l));
  const parkingLine = otherDetails.find(l => /🅿/.test(l));
  const accessibilityLine = otherDetails.find(l => /♿/.test(l));
  const priceLine = otherDetails.find(
    l =>
      (/₹/.test(l) || /price level/i.test(l) || /💰/.test(l)) &&
      l !== ratingLine &&
      l !== locationLine
  );

  // Description = longer free-text lines (e.g. "📝 Tasting menu of...")
  // Amenities = short tag-like lines (e.g. "✅ Open", "🧒 Good for children")
  const remaining = otherDetails.filter(
    l =>
      l !== ratingLine &&
      l !== locationLine &&
      l !== priceLine &&
      l !== phoneLine &&
      !hoursLines.includes(l) &&
      l !== paymentLine &&
      l !== accessibilityLine &&
      l !== parkingLine
  );

  const diningKeywords = /(serves|available|serves breakfast|serves lunch|serves dinner|serves beer|serves wine|serves vegetarian|takeout|delivery|dine-in|breakfast restaurant|🍽️|🍳|🥗|🍺|🍷|🥦|🥡|🚚|🍴)/i;
  const diningLines = remaining.filter(l => diningKeywords.test(l));


  const descriptionLines = remaining.filter(l => l.replace(/^\W+/, "").length > 45);
  const amenityLines = remaining.filter(l => !descriptionLines.includes(l) && !diningLines.includes(l));

  let ratingValue = "";
  let reviewCount = "";
  if (ratingLine) {
    const ratingMatch = ratingLine.match(/(\d+(\.\d+)?)/);
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

  const locationText = locationLine
    ? locationLine.replace(/📍/g, "").replace(/^\s*Address:\s*/i, "").trim()
    : "";

  const phoneText = phoneLine
    ? phoneLine.replace(/📞/g, "").replace(/^\s*Phone:\s*/i, "").trim()
    : "";

  const paymentText = paymentLine
    ? paymentLine.replace(/💳/g, "").trim()
    : "";

  const parkingText = parkingLine
    ? parkingLine.replace(/🅿/g, "").trim()
    : "";

  const accessibilityText = accessibilityLine
    ? accessibilityLine.replace(/♿/g, "").trim()
    : "";

  let websiteDomain = "";
  try {
    websiteDomain = websiteUrl ? new URL(websiteUrl).hostname : "";
  } catch {
    websiteDomain = "";
  }
  const websiteLogo = websiteDomain
    ? `https://www.google.com/s2/favicons?sz=128&domain=${websiteDomain}`
    : "";

  // Today's hours = first hoursLine, rest shown when expanded
  const todayHours = hoursLines[0]
    ? hoursLines[0].replace(/🕒\s*Hours?:?\s*/i, "")
    : "";
  const isOpen = /open/i.test(todayHours) || amenityLines.some(l => /✅|open now/i.test(l));

  const hasAmenities = amenityLines.length > 0;

  return (
    <div className="bg-white border border-black/[0.07] rounded-2xl shadow-sm overflow-hidden my-4 text-left max-w-md">
      {/* Header */}
      <div className="p-3.5 text-left">
        <div className="flex justify-between items-start gap-2.5">
          <div className="flex-1 min-w-0 text-left">
            <h3
              className="text-sm font-semibold text-gray-900 leading-snug text-left"
              dangerouslySetInnerHTML={{ __html: inlineMd(title) }}
            />

            {(ratingValue || priceValue) && (
              <div className="flex items-center gap-1.5 text-[11px] text-gray-600 mt-1.5">
                {ratingValue && (
                  <>
                    <FaStar className="text-yellow-400 text-[10px]" />
                    <span className="font-semibold text-gray-800">{ratingValue}</span>
                  </>
                )}
                {ratingValue && priceValue && <span className="text-gray-300">|</span>}
                {priceValue && (
                  <span className="font-semibold text-[#1D9E75]">{priceValue}</span>
                )}
                {(ratingValue || priceValue) && reviewCount && (
                  <span className="text-gray-300">|</span>
                )}
                {reviewCount && <span>{reviewCount} Reviews</span>}
              </div>
            )}

            {/* Collapsible hours pill */}
            {hoursLines.length > 0 && (
              <button
                onClick={() => setHoursOpen(!hoursOpen)}
                className={`mt-2 inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  isOpen ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-600"
                }`}
              >
                {todayHours || "Hours"}
                <FaChevronDown
                  className={`text-[9px] transition-transform ${hoursOpen ? "rotate-180" : ""}`}
                />
              </button>
            )}
            {hoursOpen && hoursLines.length > 0 && (
              <div className="mt-1.5 pl-1 space-y-0.5 text-[11px] text-gray-500 leading-relaxed">
                {hoursLines.map((line, idx) => (
                  <div key={idx}>{line.replace(/🕒\s*Hours?:?\s*/i, "")}</div>
                ))}
              </div>
            )}
          </div>

          {websiteUrl && (
            
            <a
              href={websiteUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 w-9 h-9 rounded-lg border border-black/10 bg-white flex items-center justify-center overflow-hidden shadow-sm"
            >
              <img src={websiteLogo} alt="Website" className="w-6 h-6 object-contain" />
            </a>
          )}
        </div>
      </div>

      {/* Image Slider */}
      {images.length > 0 && (
        <>
          <div className="border-t border-black/[0.07]" />
          <div className="bg-gray-50/50">
            <ImageSlider images={images} />
          </div>
        </>
      )}

      {/* Tabs */}
      {hasAmenities && (
        <div className="border-t border-black/[0.07] flex">
          <button
            onClick={() => setTab("overview")}
            className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${
              tab === "overview"
                ? "text-gray-900 border-b-2 border-[#1D9E75]"
                : "text-gray-400 border-b-2 border-transparent"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setTab("info")}
            className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${
              tab === "info"
                ? "text-gray-900 border-b-2 border-[#1D9E75]"
                : "text-gray-400 border-b-2 border-transparent"
            }`}
          >
            Information
          </button>
          {accessibilityText && (
            <button

              onClick={() => setTab("accessibility")}
              className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${
                tab === "accessibility"

                  ? "text-gray-900 border-b-2 border-[#1D9E75]"
                  : "text-gray-400 border-b-2 border-transparent"
              }`}
            >
              Accessibility
            </button>
          )}
          {paymentLine && (
            <button

              onClick={() => setTab("paymentOptions")}
              className={`flex-1 py-2 text-[11px] font-semibold transition-colors ${
                tab === "paymentOptions"

                  ? "text-gray-900 border-b-2 border-[#1D9E75]"
                  : "text-gray-400 border-b-2 border-transparent"
              }`}
            >
              Payment 
            </button>
          )}
          {parkingLine && (
            <button
              onClick={() => setTab("parkingOptions")}
              className={`flex-1 py-2 text-[11px] font-semibold transition-colors truncate ${
                tab === "parkingOptions"
                  ? "text-gray-900 border-b-2 border-[#1D9E75]"
                  : "text-gray-400 border-b-2 border-transparent"
              }`}
            >
              Parking 
            </button>
          )}
          {diningLines.length > 0 && (
            <button
              onClick={() => setTab("dining")}
              className={`flex-1 py-2 text-[11px] font-semibold transition-colors truncate ${
                tab === "dining"
                  ? "text-gray-900 border-b-2 border-[#1D9E75]"
                  : "text-gray-400 border-b-2 border-transparent"
              }`}
            >
              Dining
            </button>
          )}

          
        </div>
      )}

      {/* Panel content */}
      <div className="px-3.5 py-2.5">
        {tab === "overview" ? (
          <div className="space-y-2 text-left">
            {descriptionLines.map((line, i) => (
              <p
                key={i}
                className="text-[11.5px] text-gray-500 leading-relaxed text-left"
                dangerouslySetInnerHTML={{ __html: inlineMd(line) }}
              />
            ))}
            {locationText && (
              <div className="flex items-start gap-1.5 text-[11px] text-gray-500">
                <FaMapMarkerAlt className="mt-0.5 flex-shrink-0 text-gray-400 text-[10px]" />
                <span
                  className="flex-1"
                  dangerouslySetInnerHTML={{ __html: inlineMd(locationText) }}
                />
              </div>
            )}
            {phoneText && (
              <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
                <FaPhone className="flex-shrink-0 text-gray-400 text-[9px]" />
                <span>{phoneText}</span>
              </div>
            )}
          </div>
        ) : tab === "info" ? (
          <div className="grid grid-cols-2 gap-2">
            {amenityLines.map((line, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                <FaCheckCircle className="flex-shrink-0 text-[#1D9E75] text-[10px]" />
                <span
                  dangerouslySetInnerHTML={{
                    __html: inlineMd(line.replace(/^[^\w]+/, "").trim()),
                  }}
                />
              </div>
            ))}
          </div>
        ) : tab === "accessibility" ? (
          <div className="grid grid-cols-2 gap-2">
            {accessibilityText.split(',').map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                <FaWheelchair className="flex-shrink-0 text-[#1D9E75] text-[10px]" />
                <span dangerouslySetInnerHTML={{ __html: inlineMd(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "paymentOptions" ? (
          <div className="grid grid-cols-2 gap-2">
            {paymentText.replace(/^Accepts\s/i, '').split(',').map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                <FaCreditCard className="flex-shrink-0 text-[#1D9E75] text-[10px]" />
                <span dangerouslySetInnerHTML={{ __html: inlineMd(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "parkingOptions" ? (
          <div className="grid grid-cols-2 gap-2">
            {parkingText.replace(/^Parking:\s/i, '').split(',').map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                <FaParking className="flex-shrink-0 text-[#1D9E75] text-[10px]" />
                <span dangerouslySetInnerHTML={{ __html: inlineMd(item.trim()) }} />
              </div>
            ))}
          </div>
        ) : tab === "dining" ? (
          <div className="grid grid-cols-2 gap-2">
            {diningLines.map((item, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px] text-gray-600">
                <FaConciergeBell className="flex-shrink-0 text-[#1D9E75] text-[10px]" />
                <span
                  dangerouslySetInnerHTML={{ __html: inlineMd(item.replace(/^[^\w]+/, "").trim()) }}
                />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No details available.</p>
        )}
      </div>

      {/* Footer buttons */}
      {(mapUrl || websiteUrl) && (
        <>
          <div className="border-t border-black/[0.07]" />
          <div className="p-2.5 flex items-center gap-2">
            {mapUrl && (
              
              <a
                href={mapUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-semibold text-white transition-opacity hover:opacity-90"
                style={{ background: "#1D9E75" }}
              >
                <FaMapMarkerAlt className="text-[10px]" /> View Map
              </a>
            )}
            {websiteUrl && (
              
              <a
                href={websiteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md border text-[11px] font-semibold transition-colors hover:bg-[#1D9E75]/5"
                style={{ borderColor: "#1D9E75", color: "#1D9E75" }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
                Visit Website
              </a>
            )}
          </div>
        </>
      )}
    </div>
  );
}
function MarkdownContent({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  const imageRegex = /^!\[(.*?)\]\((.*?)\)$/;

  while (i < lines.length) {
    const line = lines[i];

    // ==========================
    // Place Card (for numbered lists)
    // ==========================
    if (/^\d+\. /.test(line.trim())) {
      const cardLines: string[] = [];
      // Extract the first line without the number, e.g., "1. **Name**" -> "**Name**"
      cardLines.push(line.replace(/^\d+\. /, "").trim());

      // Consume subsequent lines until we hit the next numbered item or end of text
      i++;
      while (i < lines.length && !/^\d+\. /.test(lines[i].trim()) && lines[i].trim() !== "") {
        cardLines.push(lines[i].trim());
        i++;
      }
      elements.push(<PlaceCard key={`card-${i}`} lines={cardLines} />);
      continue;
    }

    // ==========================
    // Image Slider
    // ==========================
    if (imageRegex.test(line.trim())) {
      const images: string[] = [];

      while (
        i < lines.length &&
        imageRegex.test(lines[i].trim())
      ) {
        const match = lines[i].match(imageRegex);

        if (match) {
          images.push(match[2]);
        }

        i++;
      }

      elements.push(
        <ImageSlider
          key={`slider-${i}`}
          images={images}
        />
      );

      continue;
    }

    // Skip empty lines
    if (line.trim() === "") {
      i++;
      continue;
    }

    // H1 heading
    if (/^# /.test(line)) {
      elements.push(
        <p key={i} className="text-base font-semibold text-gray-900 mt-3 mb-1">
          {line.replace(/^# /, "")}
        </p>
      );
      i++;
      continue;
    }

    // H2 / H3
    if (/^#{2,3} /.test(line)) {
      elements.push(
        <p key={i} className="text-sm font-semibold text-gray-800 mt-3 mb-1">
          {line.replace(/^#{2,3} /, "")}
        </p>
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
        <ul key={`ul-${i}`} className="mt-1 mb-2 space-y-1.5 pl-1">
          {bullets.map((b, bi) => (
            <li
              key={bi}
              className="flex items-start gap-2 text-sm text-gray-700"
            >
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#1D9E75] flex-shrink-0" />
              <span
                dangerouslySetInnerHTML={{
                  __html: inlineMd(b),
                }}
              />
            </li>
          ))}
        </ul>
      );

      continue;
    }

    // Numbered list
    if (/^\d+\. /.test(line)) {
      const items: { num: string; content: string }[] = [];

      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        const numMatch = lines[i].match(/^(\d+)\. /);

        items.push({
          num: numMatch ? numMatch[1] : "1",
          content: lines[i].replace(/^\d+\. /, ""),
        });

        i++;
      }

      elements.push(
        <ol key={`ol-${i}`} className="mt-1 mb-2 space-y-1.5 pl-1">
          {items.map((it, ii) => (
            <li
              key={ii}
              className="flex items-start gap-2.5 text-sm text-gray-700"
            >
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#1D9E75]/10 text-[#1D9E75] text-[10px] font-semibold flex items-center justify-center mt-0.5">
                {it.num}
              </span>

              <span
                dangerouslySetInnerHTML={{
                  __html: inlineMd(it.content),
                }}
              />
            </li>
          ))}
        </ol>
      );

      continue;
    }

    // Bold heading
    if (/^\*\*[^*]+\*\*:?$/.test(line.trim())) {
      elements.push(
        <p
          key={i}
          className="text-sm font-semibold text-gray-800 mt-3 mb-0.5"
        >
          {line.replace(/\*\*/g, "").replace(/:$/, "")}
        </p>
      );

      i++;
      continue;
    }

    // Paragraph
    elements.push(
      <p
        key={i}
        className="text-sm text-gray-700 leading-relaxed mb-1"
        dangerouslySetInnerHTML={{
          __html: inlineMd(line),
        }}
      />
    );

    i++;
  }

  return <div className="space-y-0.5">{elements}</div>;
}
// Convert inline markdown: **bold**, *italic*, `code`
function inlineMd(text: string): string {
  return text
    .replace(/\[View Map\]\((.+?)\)/g, '') // These are now handled by the PlaceCard component
    .replace(/\[Visit Website\]\((.+?)\)/g, '') // These are now handled by the PlaceCard component
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
    case "transport":
      return { label: "Transport Agent", icon: <FaSearch className="text-[9px]" />, bg: "rgba(99, 102, 241, 0.07)", color: "#6366f1", borderColor: "rgba(99, 102, 241, 0.12)" };
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
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [progressStep, setProgressStep] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [savedTrips, setSavedTrips] = useState<Record<number, { tripName: string; loading: boolean }>>({});
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = async () => {
    try {
      const res = await axios.get("http://localhost:8000/conversations");
      setConversations(res.data);
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  const loadConversation = async (conversationId: number) => {
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/conversation/${conversationId}`);
      setActiveConversationId(conversationId);
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error("Failed to load conversation", err);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

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

  useEffect(() => {
    loadConversations();
  }, []);

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
    const userQuestion = (text || question).trim();
    if (!userQuestion) return;

    const isNewChat = activeConversationId === null;
    setMessages((prev) => [...prev, { role: "user", text: userQuestion }]);
    setQuestion("");
    setLoading(true);

    try {
      let conversationId = activeConversationId;

      if (isNewChat) {
        const createRes = await axios.post("http://localhost:8000/conversation", {
          title: userQuestion,
        });
        conversationId = createRes.data.id;
        setActiveConversationId(conversationId);
        setConversations((prev) => [{ id: conversationId!, title: createRes.data.title }, ...prev]);
      }

      const res = await axios.post("http://localhost:8000/chat", {
        question: userQuestion,
        conversation_id: conversationId,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.data.answer, routes: res.data.routes },
      ]);
      await loadConversations();
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
    <div className={`h-screen flex font-sans transition-colors duration-200 ${theme === "dark" ? "bg-[#0f172a] text-slate-100" : "bg-[#F5F4F0] text-[#1a1a1a]"}`}>

      {/* ── Sidebar ── */}
      <aside className={`w-64 border-r flex flex-col flex-shrink-0 transition-colors duration-200 ${theme === "dark" ? "bg-slate-900 border-slate-800" : "bg-white border-black/[0.08]"}`}>

        {/* Logo */}
        <div className={`p-5 border-b ${theme === "dark" ? "border-slate-800" : "border-black/[0.07]"}`}>
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
            onClick={() => {
              setMessages([]);
              setActiveConversationId(null);
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-sm transition-all duration-150 ${theme === "dark" ? "border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600" : "border-black/10 text-gray-600 hover:bg-gray-50 hover:border-black/20"}`}
          >
            <FaPlus className="text-xs text-gray-400" />
            New chat
          </button>
        </div>

        <div className="px-3 pb-3 flex-1 overflow-y-auto">
          <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-2">
            Recent chats
          </p>
          <div className="space-y-1.5">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => loadConversation(conversation.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-all duration-150 ${
                  activeConversationId === conversation.id
                    ? "bg-[#1D9E75]/10 text-[#1D9E75]"
                    : theme === "dark"
                      ? "text-slate-300 hover:bg-slate-800"
                      : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <div className="truncate">{conversation.title}</div>
              </button>
            ))}
          </div>
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
        <div className={`mt-auto p-4 border-t flex items-center gap-2.5 ${theme === "dark" ? "border-slate-800" : "border-black/[0.07]"}`}>
          <div className={`w-7 h-7 rounded-full border flex items-center justify-center ${theme === "dark" ? "bg-slate-800 border-slate-700" : "bg-gray-100 border-black/10"}`}>
            <FaUser className={`text-[11px] ${theme === "dark" ? "text-slate-400" : "text-gray-400"}`} />
          </div>
          <span className={`text-xs flex-1 ${theme === "dark" ? "text-slate-400" : "text-gray-500"}`}>Traveller</span>
          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${theme === "dark" ? "bg-slate-800 text-slate-200 hover:bg-slate-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
          >
            {theme === "light" ? "🌙 Dark" : "☀️ Light"}
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Topbar */}
        <header className={`h-14 border-b flex items-center justify-between px-5 flex-shrink-0 transition-colors duration-200 ${theme === "dark" ? "bg-slate-900 border-slate-800" : "bg-white border-black/[0.07]"}`}>
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-[#1D9E75] flex-shrink-0" />
            <div>
              <p className={`text-sm font-medium ${theme === "dark" ? "text-slate-100" : "text-gray-800"}`}>
                Tourist AI Assistant
              </p>
              <p className={`text-[11px] ${theme === "dark" ? "text-slate-500" : "text-gray-400"}`}>
                Powered by AI · Tamil Nadu & beyond
              </p>
            </div>
          </div>
          <FaRobot className={`text-base ${theme === "dark" ? "text-slate-500" : "text-gray-300"}`} />
        </header>

        {/* Chat */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
                   style={{ background: "linear-gradient(135deg, rgba(29,158,117,0.1) 0%, rgba(24,95,165,0.1) 100%)", border: "1px solid rgba(29,158,117,0.2)" }}>
                <FaMapMarkerAlt className="text-2xl text-[#1D9E75]" />
              </div>
              <h1 className={`text-2xl font-medium mb-2 ${theme === "dark" ? "text-slate-100" : "text-gray-800"}`}>
                Where to next?
              </h1>
              <p className={`text-sm max-w-xs leading-relaxed ${theme === "dark" ? "text-slate-500" : "text-gray-400"}`}>
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
                      : theme === "dark"
                        ? "bg-slate-800 border border-slate-700"
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
                  className={`max-w-[90%] px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "text-white rounded-2xl rounded-br-[4px]"
                      : theme === "dark"
                        ? "bg-slate-800 border border-slate-700 text-slate-100 rounded-2xl rounded-bl-[4px]"
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
              <div className={`px-4 py-3 rounded-2xl rounded-bl-[4px] flex flex-col gap-1.5 min-w-[220px] ${theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white border border-black/[0.07]"}`}>
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
        <div className={`border-t p-4 flex-shrink-0 transition-colors duration-200 ${theme === "dark" ? "bg-slate-900 border-slate-800" : "bg-white border-black/[0.07]"}`}>
          <div className="max-w-3xl mx-auto">
            <div className={`flex items-center gap-2 rounded-xl px-3 py-2 border transition-all duration-150 ${theme === "dark" ? "bg-slate-800 border-slate-700 focus-within:border-[#1D9E75] focus-within:ring-1 focus-within:ring-[#1D9E75]/20" : "bg-gray-50 border-black/[0.09] focus-within:border-[#1D9E75] focus-within:ring-1 focus-within:ring-[#1D9E75]/20"}`}>
              <FaSearch className="text-gray-300 text-xs flex-shrink-0" />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") askAI(); }}
                placeholder="Ask about your trip…"
                className={`flex-1 bg-transparent outline-none text-sm ${theme === "dark" ? "text-slate-100 placeholder-slate-500" : "text-gray-800 placeholder-gray-400"}`}
              />
              <button
                onClick={startVoice}
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-150 ${
                  isListening
                    ? "bg-red-50 text-red-500 animate-pulse"
                    : theme === "dark"
                      ? "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
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
            <p className={`text-center text-[11px] mt-2 ${theme === "dark" ? "text-slate-500" : "text-gray-400"}`}>
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
