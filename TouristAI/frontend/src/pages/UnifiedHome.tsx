import React, { useState } from "react";
import { ArrowUpRight, Bot, Bus, Car, ChevronDown, CloudSun, Compass, DollarSign, Hotel, Map, MapPin, Plane, Sparkles, TicketCheck, Train, Utensils, X } from "lucide-react";
import { AIChat } from "./AIChat";
import { useTravelPlanner } from "../context/TravelPlannerContext";

const recentTrips = [
  {
    badge: "Trip",
    title: "Trip to Chennai, August 2026",
    meta: "Chennai · 22 – 24 Aug",
    image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=900&q=85",
  },
  {
    badge: "Chat",
    title: "Chennai weather for August trip",
    meta: "Coastal weather guide",
    image: "https://images.unsplash.com/photo-1621831714462-bec8ed8dd4d8?auto=format&fit=crop&w=900&q=85",
  },
];

const maduraiPlaces = [
  {
    name: "Kumar Mess",
    type: "Indian · Restaurant",
    image: "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=85",
  },
  {
    name: "Meenakshi Amman Temple",
    type: "Attraction · Temple",
    image: "https://images.unsplash.com/photo-1600100397608-f010e423b971?auto=format&fit=crop&w=900&q=85",
  },
  {
    name: "Thirumalai Nayakkar Palace",
    type: "History · Architecture",
    image: "https://images.unsplash.com/photo-1595658658481-d53d3f999875?auto=format&fit=crop&w=900&q=85",
  },
];

const modes = [
  { value: "All", icon: Compass },
  { value: "Train", icon: Train },
  { value: "Flight", icon: Plane },
  { value: "Bus", icon: Bus },
  { value: "Car", icon: Car },
];

export default function UnifiedHome() {
  const { askAIChat, isLoadingChat } = useTravelPlanner();
  const [currentLocation, setCurrentLocation] = useState("Chennai");
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [days, setDays] = useState(3);
  const [travelers, setTravelers] = useState(2);
  const [budget, setBudget] = useState("Moderate");
  const [style, setStyle] = useState("Cultural");
  const [interests, setInterests] = useState("Culture, History, Food");
  const [travelMode, setTravelMode] = useState("All");
  const [isQuickSetupOpen, setIsQuickSetupOpen] = useState(false);

  const submitPlan = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!destination.trim() || isLoadingChat) return;
    setIsQuickSetupOpen(false);
    const query = [
      `Plan a ${days}-day ${style.toLowerCase()} trip to ${destination.trim()} for ${travelers} traveler${travelers === 1 ? "" : "s"}`,
      currentLocation.trim() ? `from ${currentLocation.trim()}` : "",
      startDate ? `starting on ${startDate}` : "",
      `with a ${budget.toLowerCase()} budget`,
      `using ${travelMode === "All" ? "the best available transport options" : travelMode}`,
      interests.trim() ? `Interests: ${interests.trim()}.` : "",
    ].filter(Boolean).join(" ");
    await askAIChat(query);
    document.getElementById("unified-chat")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const quickDestination = async (city: string) => {
    setDestination(city);
    await askAIChat(`Plan a 3-day cultural trip to ${city} for 2 travelers from Chennai with a moderate budget.`);
    document.getElementById("unified-chat")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="space-y-4 p-4 sm:p-5 pb-24 sm:pb-8">
      <section className="relative overflow-hidden rounded-[24px] bg-slate-950 p-5 text-left text-white sm:p-6">
        <img src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1600&q=85" alt="Travel landscape" className="absolute inset-0 h-full w-full object-cover opacity-35" />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/80 to-slate-900/50" />
        <div className="relative z-10 max-w-4xl space-y-3">
          <div className="space-y-3">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-teal-400/25 bg-teal-400/15 px-3 py-1 text-[10px] font-extrabold uppercase tracking-widest text-teal-300">
              <Sparkles className="h-3.5 w-3.5" /> AI Travel Agent Ready
            </span>
            <h1 className="font-heading text-2xl font-extrabold leading-tight tracking-tight sm:text-3xl">Plan your complete trip in one conversation.</h1>
            <p className="max-w-2xl text-xs font-medium leading-relaxed text-slate-300">Chat naturally or use Quick Trip to create an itinerary with stays, transport, dining, weather and budget.</p>
          </div>
          <div className="hidden flex-wrap gap-2 sm:flex">
              {[
                { label: "Hotels", icon: Hotel },
                { label: "Dining", icon: Utensils },
                { label: "Tickets", icon: TicketCheck },
                { label: "Weather", icon: CloudSun },
                { label: "Budget", icon: DollarSign },
              ].map(({ label, icon: Icon }) => (
                <span key={label} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/10 px-2.5 py-1.5 text-[10px] font-bold text-slate-200 backdrop-blur-sm"><Icon className="h-3.5 w-3.5 text-teal-300" />{label}</span>
              ))}
          </div>
        </div>
        <button
          onClick={() => setIsQuickSetupOpen(true)}
          className="quick-trip-cta group absolute right-4 top-4 z-20 inline-flex min-h-12 items-center gap-2.5 overflow-hidden rounded-2xl border border-white/25 bg-teal-400 px-4 py-3 text-xs font-extrabold text-slate-950 shadow-xl shadow-teal-950/30 backdrop-blur-sm transition hover:scale-105 hover:bg-teal-300 sm:right-6 sm:top-6 sm:min-h-14 sm:px-5 sm:py-3.5 sm:text-sm"
          aria-label="Open Quick Trip"
          title="Quick Trip"
        >
          <span className="quick-trip-shine pointer-events-none absolute inset-y-0 -left-12 w-10 rotate-12 bg-white/45 blur-sm" />
          <span className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-slate-950/10 ring-1 ring-slate-950/10 transition-transform group-hover:rotate-12 group-hover:scale-105">
            <Sparkles className="h-5 w-5" />
          </span>
          <span className="relative hidden sm:inline">Quick Trip</span>
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-amber-300 ring-2 ring-teal-500/60">
            <span className="absolute inset-0 animate-ping rounded-full bg-amber-200 opacity-70" />
          </span>
        </button>
      </section>

      <section className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.8fr)_minmax(300px,0.7fr)]">
        <div id="unified-chat" className="min-w-0 scroll-mt-20"><AIChat embedded /></div>

        <aside className="xl:sticky xl:top-20">
          <div className="overflow-hidden rounded-[24px] border border-slate-200/70 bg-[#f7f7f6] text-left shadow-sm dark:border-slate-800/70 dark:bg-[#111827]">
            <div className="space-y-6 p-4 sm:p-5">
              <section>
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <h2 className="font-heading text-base font-extrabold text-slate-900 dark:text-slate-100">Jump back in</h2>
                    <p className="mt-0.5 text-[10px] text-slate-400">Continue planning where you left off.</p>
                  </div>
                  <button type="button" className="text-[10px] font-bold text-slate-500 transition hover:text-teal-700 dark:text-slate-400">See all</button>
                </div>
                <div className="grid grid-cols-2 gap-2.5">
                  {recentTrips.map((item) => (
                    <button key={item.title} type="button" onClick={() => void quickDestination("Chennai")} disabled={isLoadingChat} className="group relative h-40 overflow-hidden rounded-2xl bg-slate-800 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg disabled:pointer-events-none disabled:opacity-60">
                      <img src={item.image} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105" />
                      <span className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/15 to-transparent" />
                      <span className="absolute inset-x-0 bottom-0 p-3 text-white">
                        <span className="mb-1 inline-flex rounded-full bg-white/20 px-2 py-0.5 text-[8px] font-extrabold uppercase tracking-wide backdrop-blur-md">{item.badge}</span>
                        <strong className="block text-xs font-extrabold leading-tight">{item.title}</strong>
                        <small className="mt-1 block truncate text-[9px] font-medium text-white/75">{item.meta}</small>
                      </span>
                    </button>
                  ))}
                </div>
              </section>

              <section>
                <div className="mb-3 flex items-center gap-2">
                  <h2 className="flex min-w-0 items-center gap-1 font-heading text-base font-extrabold text-slate-900 dark:text-slate-100">
                    For you in <button type="button" className="inline-flex items-center gap-0.5 text-teal-700 dark:text-teal-400">Madurai <ChevronDown className="h-3.5 w-3.5" /></button>
                  </h2>
                  <button type="button" className="ml-auto inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1.5 text-[9px] font-extrabold text-slate-600 transition hover:border-teal-300 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"><Map className="h-3.5 w-3.5" />Map</button>
                </div>
                <div className="flex gap-2.5 overflow-x-auto pb-1 no-scrollbar">
                  {maduraiPlaces.map((place) => (
                    <button key={place.name} type="button" onClick={() => void quickDestination("Madurai")} disabled={isLoadingChat} className="group relative h-52 min-w-[78%] overflow-hidden rounded-2xl bg-slate-800 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg disabled:pointer-events-none disabled:opacity-60 sm:min-w-[72%]">
                      <img src={place.image} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105" />
                      <span className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-black/5" />
                      <span className="absolute inset-x-0 bottom-0 p-4 text-white">
                        <strong className="block text-sm font-extrabold leading-tight">{place.name}</strong>
                        <small className="mt-1 flex items-center gap-1 text-[10px] font-medium text-white/75"><MapPin className="h-3 w-3" />{place.type}</small>
                      </span>
                      <span className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-full bg-white/90 text-slate-700 opacity-0 shadow-sm transition group-hover:opacity-100"><ArrowUpRight className="h-4 w-4" /></span>
                    </button>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200/70 bg-white p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-400"><Compass className="h-5 w-5" /></span>
                  <span className="min-w-0 flex-1"><strong className="block text-xs font-extrabold text-slate-800 dark:text-slate-100">Explore more destinations</strong><small className="mt-0.5 block text-[9px] text-slate-400">Discover places picked for your travel style.</small></span>
                  <ArrowUpRight className="h-4 w-4 text-slate-400" />
                </div>
              </section>
            </div>
          </div>
        </aside>
      </section>

      {isQuickSetupOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" role="dialog" aria-modal="true" aria-labelledby="quick-trip-title">
          <button className="absolute inset-0 bg-slate-950/65 backdrop-blur-sm" onClick={() => setIsQuickSetupOpen(false)} aria-label="Close Quick Trip" />
          <form onSubmit={submitPlan} className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-slate-200/70 bg-white p-5 text-left shadow-2xl dark:border-slate-800 dark:bg-[#111827] sm:p-6">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div><h2 id="quick-trip-title" className="font-heading text-lg font-extrabold text-slate-800 dark:text-slate-100">Quick Trip</h2><p className="mt-1 text-xs text-slate-400">Fill a few details, or close this and tell the assistant everything in one message.</p></div>
              <button type="button" onClick={() => setIsQuickSetupOpen(false)} className="rounded-xl border border-slate-200 p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-700 dark:border-slate-800 dark:hover:bg-slate-900 dark:hover:text-slate-200" aria-label="Close"><X className="h-4 w-4" /></button>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label="Current location"><input value={currentLocation} onChange={(e) => setCurrentLocation(e.target.value)} placeholder="e.g. Chennai" className="field" /></Field>
              <Field label="Destination city"><input required autoFocus value={destination} onChange={(e) => setDestination(e.target.value)} placeholder="e.g. Madurai" className="field" /></Field>
              <Field label="Start date"><input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="field" /></Field>
              <Field label="Duration (days)"><input type="number" min={1} max={30} value={days} onChange={(e) => setDays(Number(e.target.value))} className="field" /></Field>
              <Field label="Travelers"><input type="number" min={1} max={20} value={travelers} onChange={(e) => setTravelers(Number(e.target.value))} className="field" /></Field>
              <Field label="Budget"><select value={budget} onChange={(e) => setBudget(e.target.value)} className="field"><option>Low</option><option>Moderate</option><option>Luxury</option></select></Field>
              <Field label="Travel style"><select value={style} onChange={(e) => setStyle(e.target.value)} className="field"><option>Cultural</option><option>Adventure</option><option>Relaxed</option><option>Family</option></select></Field>
              <Field label="Interests"><input value={interests} onChange={(e) => setInterests(e.target.value)} placeholder="Culture, food" className="field" /></Field>
            </div>
            <div className="mt-4"><label className="mb-2 block text-[9px] font-extrabold uppercase tracking-wide text-slate-400">Travel mode</label><div className="grid grid-cols-5 gap-2">{modes.map(({ value, icon: Icon }) => <button type="button" key={value} onClick={() => setTravelMode(value)} className={`flex min-h-10 items-center justify-center gap-1.5 rounded-xl border px-2 text-[10px] font-extrabold ${travelMode === value ? "border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300" : "border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400"}`}><Icon className="h-3.5 w-3.5" /><span className="hidden sm:inline">{value}</span></button>)}</div></div>
            <button disabled={isLoadingChat} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 py-3 text-xs font-extrabold text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-60"><Bot className="h-4 w-4" />{isLoadingChat ? "Agents are planning…" : "Generate Smart Plan"}</button>
          </form>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1 block text-[9px] font-extrabold uppercase tracking-wide text-slate-400">{label}</span>{children}</label>;
}
