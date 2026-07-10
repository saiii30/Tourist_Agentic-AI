import React, { useState } from "react";
import { MapPin, Users, Plus, X } from "lucide-react";
import { AddToItineraryDialog } from "../dialogs/AddToItineraryDialog";
import CrowdMeter from "../CrowdMeter";

interface Attraction {
  id: string;
  name: string;
  category: string;
  image?: string;
  distance?: string;
  popularity?: string;
  expectedCrowd?: string;
  bestTime?: string;
  description?: string;
}

interface Props {
  attractions: Attraction[];
  durationDays: number;
  cityName: string;
  onAddToItinerary: (attraction: Attraction, dayNum: number, time: string) => void;
}

// const FALLBACK =
//   "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80";

// /** Fetch a Wikipedia thumbnail for "<name>, <city>" (or just name). Cached in-memory + localStorage. */
// const imageCache = new Map<string, string>();

// async function fetchWikiImage(name: string, city: string): Promise<string | null> {
//   const key = `wiki-img:${name}|${city}`.toLowerCase();
//   if (imageCache.has(key)) return imageCache.get(key)!;
//   try {
//     const cached = localStorage.getItem(key);
//     if (cached) {
//       imageCache.set(key, cached);
//       return cached;
//     }
//   } catch {}

//   const queries = [`${name}, ${city}`, `${name} ${city}`, name];
//   for (const q of queries) {
//     try {
//       // 1. search
//       const sr = await fetch(
//         `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(
//           q
//         )}&format=json&srlimit=1&origin=*`
//       );
//       const sj = await sr.json();
//       const title = sj?.query?.search?.[0]?.title;
//       if (!title) continue;

//       // 2. summary → thumbnail
//       const pr = await fetch(
//         `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`
//       );
//       if (!pr.ok) continue;
//       const pj = await pr.json();
//       const img = pj?.originalimage?.source || pj?.thumbnail?.source;
//       if (img) {
//         imageCache.set(key, img);
//         try {
//           localStorage.setItem(key, img);
//         } catch {}
//         return img;
//       }
//     } catch {
//       /* try next */
//     }
//   }
//   return null;
// }

// const AttractionCard: React.FC<{
//   place: Attraction;
//   cityName: string;
//   onCrowdClick: () => void;
//   onAddClick: () => void;
// }> = ({ place, cityName, onCrowdClick, onAddClick }) => {
//   const [imgSrc, setImgSrc] = useState<string>(place.image || "");

//   useEffect(() => {
//     let cancelled = false;
//     if (!place.image) {
//       fetchWikiImage(place.name, cityName).then((url) => {
//         if (!cancelled && url) setImgSrc(url);
//       });
//     }
//     return () => {
//       cancelled = true;
//     };
//   }, [place.name, cityName, place.image]);

//   return (
//     <div className="bg-white rounded-2xl overflow-hidden border shadow-sm flex flex-col">
//       <div className="h-52 overflow-hidden bg-gray-100">
//         <img
//           src={imgSrc || FALLBACK}
//           alt={place.name}
//           loading="lazy"
//           onError={(e) => ((e.target as HTMLImageElement).src = FALLBACK)}
//           className="w-full h-full object-cover"
//         />
//       </div>
//       <div className="p-4 flex-1 flex flex-col">
//         <h3 className="font-bold text-lg">{place.name}</h3>
//         <p className="text-sm text-gray-500 mt-1">{place.category}</p>
//         <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
//           <MapPin size={14} />
//           {place.distance || "Nearby"}
//         </div>
//         <div className="mt-4 flex justify-between text-sm">
//           <button
//             onClick={onCrowdClick}
//             className="flex items-center gap-1 text-blue-600 hover:underline"
//           >
//             <Users size={15} />
//              Crowd Predictor
//           </button>
//           {/* <span className="text-green-600">{places.bestTime || "Morning"}</span> */}
//         </div>
//         <div className="mt-4 flex gap-2">
//           <button
//             onClick={onAddClick}
//             className="flex-1 bg-teal-600 hover:bg-teal-700 text-white rounded-xl py-2 flex items-center justify-center gap-2"
//           >
//             <Plus size={16} />
//             Add To Itinerary
//           </button>
//           {/* <button className="px-4 border rounded-xl" title="Details">
//             <Info size={16} />
//           </button> */}
//         </div>
//       </div>
//     </div>
//   );

const AttractionCard: React.FC<{
  place: Attraction;
  onCrowdClick: () => void;
  onAddClick: () => void;
}> = ({ place, onCrowdClick, onAddClick }) => (
  <div className="bg-white rounded-2xl overflow-hidden border shadow-sm flex flex-col">
    <div className="h-52 overflow-hidden bg-gray-100">
      {place.image ? (
        <img
          src={place.image}
          alt={place.name}
          loading="lazy"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-sm text-gray-400">
          Photo unavailable
        </div>
      )}
    </div>

    <div className="p-4 flex-1 flex flex-col">
      <h3 className="font-bold text-lg">{place.name}</h3>
      <p className="text-sm text-gray-500 mt-1">{place.category}</p>

      <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
        <MapPin size={14} />
        {place.distance || "Nearby"}
      </div>

      <div className="mt-4 flex justify-between text-sm">
        <button
          onClick={onCrowdClick}
          className="flex items-center gap-1 text-blue-600 hover:underline"
        >
          <Users size={15} />
          Crowd Predictor
        </button>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={onAddClick}
          className="flex-1 bg-teal-600 hover:bg-teal-700 text-white rounded-xl py-2 flex items-center justify-center gap-2"
        >
          <Plus size={16} />
          Add To Itinerary
        </button>
      </div>
    </div>
  </div>
);


const AttractionsTab: React.FC<Props> = ({
  attractions,
  durationDays,
  cityName,
  onAddToItinerary,
}) => {
  const [selectedAttraction, setSelectedAttraction] = useState<Attraction | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [crowdPopup, setCrowdPopup] = useState<Attraction | null>(null);

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {attractions.map((place) => (
          // <AttractionCard
          //   key={place.id}
          //   place={place}
          //   cityName={cityName}
          //   onCrowdClick={() => setCrowdPopup(place)}
          //   onAddClick={() => {
          //     setSelectedAttraction(place);
          //     setShowAddDialog(true);
          //   }}
          // />changing below from codex 
          <AttractionCard
  key={place.id}
  place={place}
  onCrowdClick={() => setCrowdPopup(place)}
  onAddClick={() => {
    setSelectedAttraction(place);
    setShowAddDialog(true);
  }}
/>
        ))}
      </div>

      {/* Live Crowd popup (matches your original CrowdMeter card design) */}
      {crowdPopup && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          // className="rounded-2xl border p-6 bg-white shadow-lg w-full"
          onClick={() => setCrowdPopup(null)}
        >
          <div
            // className="relative"
            className="relative w-full max-w-3xl"
            
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setCrowdPopup(null)}
              className="absolute -top-3 -right-3 bg-white rounded-full p-1.5 shadow-md border z-10 hover:bg-gray-100"
              aria-label="Close"
            >
              <X size={16} />
            </button>
            <div className="mb-2 text-white text-sm font-medium px-1">
              {crowdPopup.name}
            </div>
            {/* <CrowdMeter city={cityName} attraction={crowdPopup.name} /> */}
            <CrowdMeter
  city={cityName}
  attraction={crowdPopup.name}
  popularity={crowdPopup.popularity}
  bestTime={crowdPopup.bestTime}
/>
          </div>
        </div>
      )}

      <AddToItineraryDialog
        isOpen={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        durationDays={durationDays}
        item={
          selectedAttraction
            ? {
                id: selectedAttraction.id,
                name: selectedAttraction.name,
                location: selectedAttraction.distance || "",
                image: selectedAttraction.image || "",
                rating: 4.5,
                type: "attraction",//changed this as attraction instead of restaurants
              }
            : null
        }
        onAdd={(dayNum, time) => {
          if (selectedAttraction) {
            onAddToItinerary(selectedAttraction, dayNum, time);
          }
        }}
      />
    </>
  );
};

export default AttractionsTab;
