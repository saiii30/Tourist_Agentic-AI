import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Compass, MapPin, Calendar, Sparkles, TrendingUp, ArrowRight, UserPlus, Plane, Train, Bus, Car, Hotel, Utensils, TicketCheck } from "lucide-react";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import { WeatherCard } from "../components/shared/WeatherCard";

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { activeTrip, generateRealAgentTrip } = useTravelPlanner();

  // Search form state
  const [currentLocation, setCurrentLocation] = useState("");
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [days, setDays] = useState(3);
  const [travelers, setTravelers] = useState(1);
  const [budget, setBudget] = useState<"Low" | "Moderate" | "Luxury">("Moderate");
  const [style, setStyle] = useState<"Adventure" | "Relaxed" | "Cultural" | "Family">("Cultural");
  const [interests, setInterests] = useState("Culture");
  const [travelMode, setTravelMode] = useState<string>("Flight");
  const [isLoading, setIsLoading] = useState(false);

  React.useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (_position) => {
          setCurrentLocation("Chennai");
        },
        () => {}
      );
    }
  }, []);

  const popularDestinations = [
    {
      city: "Madurai",
      desc: "City of Temples & Historic Festivities",
      image: "https://images.unsplash.com/photo-1600100397608-f010e423b971?auto=format&fit=crop&w=400&q=80",
      days: 3
    },
    {
      city: "Goa",
      desc: "Sun, Sand & Beachside Lounging",
      image: "https://images.unsplash.com/photo-1524492449929-c42c1196ef7b?auto=format&fit=crop&w=400&q=80",
      days: 4
    },
    {
      city: "Ooty",
      desc: "Hills, Lakes & Tea Estates",
      image: "https://images.unsplash.com/photo-1590073844006-33379778ae09?auto=format&fit=crop&w=400&q=80",
      days: 3
    },
    {
      city: "Paris",
      desc: "City of Romance, Fashion & Iconic Arts",
      image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=400&q=80",
      days: 5
    }
  ];

  const trendingTrips = [
    {
      title: "Golden Triangle Escape",
      stops: "Delhi · Agra · Jaipur",
      price: "$450 / Guest",
      image: "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=400&q=80",
      city: "Agra"
    },
    {
      title: "Tokyo Neon & Shrines Loop",
      stops: "Shibuya · Asakusa · Hakone",
      price: "$980 / Guest",
      image: "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=400&q=80",
      city: "Tokyo"
    }
  ];

  const agentStack = [
    { label: "Hotels", icon: Hotel, detail: "ranked stays" },
    { label: "Dining", icon: Utensils, detail: "local tables" },
    { label: "Tickets", icon: TicketCheck, detail: "live options" }
  ];

  const travelModes = [
    { value: "Flight", label: "Flight", icon: Plane },
    { value: "Train", label: "Train", icon: Train },
    { value: "Bus", label: "Bus", icon: Bus },
    { value: "Cab", label: "Car", icon: Car },
    { value: "All", label: "All", icon: Compass }
  ];

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!destination.trim()) return;

    setIsLoading(true);
    let generated = false;
    try {
      generated = !!(await generateRealAgentTrip({
        destination,
        days,
        budget,
        style,
        travelers,
        interests,
        travelMode,
        startDate: startDate || undefined,
        currentLocation: currentLocation || undefined
      }));
    } catch (err) {
      console.error("Error generating trip:", err);
    } finally {
      setIsLoading(false);
      if (generated) navigate("/planner");
    }
  };

  const handleQuickPlan = async (city: string, daysCount: number) => {
    setIsLoading(true);
    let generated = false;
    try {
      generated = !!(await generateRealAgentTrip({
        destination: city,
        days: daysCount,
        budget: "Moderate",
        style: "Cultural",
        travelers,
        interests: "Culture",
        travelMode
      }));
    } catch (err) {
      console.error("Error in quick plan:", err);
    } finally {
      setIsLoading(false);
      if (generated) navigate("/planner");
    }
  };

  return (
    <div className="space-y-6 pb-20 sm:pb-8">
      {isLoading && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex flex-col items-center justify-center text-center p-6">
          <div className="relative max-w-sm space-y-6">
            <div className="w-20 h-20 mx-auto rounded-full bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <Sparkles className="w-8 h-8 animate-spin" />
            </div>
            <div className="space-y-2">
              <h3 className="font-heading text-lg font-bold text-white">AI Agent is Planning Your Trip</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Running transport scrapers, compiling hotel reviews, selecting restaurants, and scheduling your itinerary slots...
              </p>
            </div>
            <div className="flex justify-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
      
      {/* 1. Hero Banner */}
      <div className="relative rounded-[28px] overflow-hidden bg-slate-900 text-white min-h-[310px] sm:min-h-[360px] flex items-center p-6 sm:p-10 text-left">
        {/* Banner Cover Image */}
        <img
          src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=80"
          alt="Travel Landscape"
          className="absolute inset-0 w-full h-full object-contain opacity-55 select-none pointer-events-none"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-900/70 to-slate-950/20" />
        
        <div className="relative z-10 grid w-full gap-8 lg:grid-cols-[1fr_320px] lg:items-end">
          <div className="max-w-xl space-y-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/20 backdrop-blur-md border border-teal-500/30 text-[10px] font-bold text-teal-400 uppercase tracking-widest">
            <Sparkles className="w-3.5 h-3.5" />
            AI Travel Agent Ready
          </span>
          <h1 className="font-heading text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            Plan the trip. See the stays, food, tickets, and route.
          </h1>
          <p className="text-sm text-slate-250 dark:text-slate-300 font-medium leading-relaxed">
            Generate a usable itinerary from your starting city, travel mode, budget, and interests. The planner opens with transport tickets, map markers, hotels, restaurants, and schedule blocks already connected.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => document.getElementById("home-trip-generator")?.scrollIntoView({ behavior: "smooth", block: "start" })}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-extrabold rounded-xl flex items-center gap-1.5 shadow-lg shadow-teal-950/30"
            >
              <Search className="w-4 h-4" />
              Build Itinerary
            </button>
            <button
              onClick={() => navigate("/chat")}
              className="px-4 py-2 bg-white/10 hover:bg-white/15 text-white text-xs font-bold rounded-xl border border-white/15 backdrop-blur-md flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4 text-teal-300" />
              Open Chat Planner
            </button>
          </div>
          </div>

          <div className="hidden lg:block space-y-3 rounded-2xl border border-white/15 bg-black/35 p-4 backdrop-blur-md">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-300">Live Planning Stack</span>
              <p className="mt-1 text-xs font-medium text-slate-300">Each generated trip is assembled from focused travel agents.</p>
            </div>
            <div className="space-y-2">
              {agentStack.map(({ label, icon: Icon, detail }) => (
                <div key={label} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/10 px-3 py-2">
                  <span className="flex items-center gap-2 text-xs font-bold">
                    <Icon className="w-4 h-4 text-teal-300" />
                    {label}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-300">{detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Continue Planning (If active draft exists) */}
      {activeTrip && (
        <div className="p-4 bg-teal-50/40 dark:bg-teal-950/10 border border-teal-150/40 dark:border-teal-900/20 rounded-2xl text-left flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-650 bg-teal-500 animate-pulse" />
              <span className="text-[10px] text-teal-650 dark:text-teal-400 font-bold uppercase tracking-wider">
                Continue Planning
              </span>
            </div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Trip to {activeTrip.cityName}
            </h4>
            <p className="text-xs text-slate-400">
              Starts on {activeTrip.startDate} · {activeTrip.durationDays} Days Itinerary
            </p>
          </div>
          <button
            onClick={() => navigate("/planner")}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 hover-scale self-start sm:self-auto"
          >
            Open Planner
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 3. Search / Trip Generator Form & Weather Side-by-Side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Search Trip Form Card */}
        <div id="home-trip-generator" className="lg:col-span-2 p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm text-left">
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                <Compass className="w-5 h-5 text-teal-605" />
                AI Itinerary Generator
              </h3>
              <p className="mt-1 text-xs font-medium text-slate-400">Start with the details that shape the actual planner output.</p>
            </div>
            <span className="self-start rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wide text-slate-500 dark:bg-slate-900 dark:text-slate-400">
              Home widget flow
            </span>
          </div>

          <form onSubmit={handleSearchSubmit} className="space-y-4">
            
            {/* Input grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Current Location */}
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1 flex items-center justify-between">
                  <span>Current Location</span>
                  {currentLocation && <span className="text-[10px] text-teal-600 dark:text-teal-400 font-bold">📍 Detected</span>}
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="e.g. Chennai, New York..."
                    value={currentLocation}
                    onChange={(e) => setCurrentLocation(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
              </div>

              {/* Destination City */}
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Destination City
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Madurai, Goa, Paris..."
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Start Date
                </label>
                <div className="relative">
                  <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
              </div>

              {/* Itinerary Duration (Days) */}
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Itinerary Duration (Days)
                </label>
                <div className="relative">
                  <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value))}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
              </div>
            </div>

            {/* Preferences filters */}
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Travelers
                </label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={travelers}
                  onChange={(e) => setTravelers(Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Budget Target
                </label>
                <select
                  value={budget}
                  onChange={(e) => setBudget(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                >
                  <option value="Low" className="dark:bg-[#111827]">Low Saver</option>
                  <option value="Moderate" className="dark:bg-[#111827]">Moderate Comfort</option>
                  <option value="Luxury" className="dark:bg-[#111827]">Premium Luxury</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Travel Style
                </label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                >
                  <option value="Cultural" className="dark:bg-[#111827]">Cultural & Historic</option>
                  <option value="Adventure" className="dark:bg-[#111827]">Adventure & Hiking</option>
                  <option value="Relaxed" className="dark:bg-[#111827]">Relaxed Leisure</option>
                  <option value="Family" className="dark:bg-[#111827]">Family Vacation</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Interests
                </label>
                <select
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                >
                  <option value="Culture" className="dark:bg-[#111827]">Culture</option>
                  <option value="Nature" className="dark:bg-[#111827]">Nature</option>
                  <option value="Adventure" className="dark:bg-[#111827]">Adventure</option>
                  <option value="History" className="dark:bg-[#111827]">History</option>
                  <option value="Food" className="dark:bg-[#111827]">Food</option>
                  <option value="Shopping" className="dark:bg-[#111827]">Shopping</option>
                  <option value="Photography" className="dark:bg-[#111827]">Photography</option>
                </select>
              </div>

              <div className="sm:col-span-5">
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Travel Mode (Transport Agent)
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {travelModes.map(({ value, label, icon: Icon }) => {
                    const selected = travelMode === value;
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setTravelMode(value)}
                        className={`min-h-10 rounded-xl border px-2 text-[10px] font-extrabold transition-all flex items-center justify-center gap-1.5 ${
                          selected
                            ? "border-teal-500 bg-teal-50 text-teal-700 shadow-sm dark:bg-teal-950/30 dark:text-teal-300"
                            : "border-slate-200 text-slate-500 hover:border-teal-300 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-900"
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-extrabold flex items-center justify-center gap-1.5 hover-scale shadow-md"
            >
              <Search className="w-4 h-4" />
              Generate Smart Plan
            </button>

          </form>
        </div>

        {/* Dynamic Weather Card */}
        <div>
          <WeatherCard location={destination || activeTrip?.cityName || "Chennai, IN"} />
        </div>

      </div>

      {/* 4. Popular Destinations */}
      <div className="space-y-3 text-left">
        <div className="flex items-center justify-between">
          <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Compass className="w-5 h-5 text-teal-605" />
            Popular Destinations
          </h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {popularDestinations.map((dest) => (
            <div
              key={dest.city}
              onClick={() => handleQuickPlan(dest.city, dest.days)}
              className="group relative h-48 rounded-2xl overflow-hidden cursor-pointer border border-slate-200/50 dark:border-slate-800/80 shadow-sm hover:shadow-md transition-all duration-200 hover-scale"
            >
              <img
                src={dest.image}
                alt={dest.city}
                className="w-full h-full object-contain bg-slate-900 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
              <div className="absolute bottom-4 left-4 right-4 text-white text-left space-y-0.5">
                <span className="text-[9px] font-bold text-teal-400 bg-teal-950/60 backdrop-blur-sm px-2 py-0.5 rounded border border-teal-500/20">
                  {dest.days} Days Itinerary
                </span>
                <h4 className="font-heading text-base font-bold tracking-tight">
                  {dest.city}
                </h4>
                <p className="text-[10px] text-slate-300 font-medium truncate">
                  {dest.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Trending Trips & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left">
        
        {/* Trending Trips */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-teal-605" />
            Trending AI Circuits
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {trendingTrips.map((trip) => (
              <div
                key={trip.title}
                onClick={() => handleQuickPlan(trip.city, 4)}
                className="group flex gap-3 p-3 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl cursor-pointer hover:border-slate-350 dark:hover:border-slate-700 transition-all hover-scale"
              >
                <div className="w-20 h-20 rounded-xl overflow-hidden flex-shrink-0 bg-slate-100 dark:bg-slate-800">
                  <img
                    src={trip.image}
                    alt={trip.title}
                    className="w-full h-full object-contain bg-slate-100 transition-transform dark:bg-slate-900"
                  />
                </div>
                <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                  <div className="space-y-0.5">
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-150 truncate">
                      {trip.title}
                    </h4>
                    <p className="text-[10px] text-slate-400 truncate">
                      {trip.stops}
                    </p>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-teal-650 dark:text-teal-400">
                      {trip.price}
                    </span>
                    <span className="text-[9px] text-slate-400 font-bold flex items-center gap-0.5">
                      Check Circuit <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions Panel */}
        <div className="space-y-3">
          <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100">
            Assistant Quick Actions
          </h3>
          <div className="p-4 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-2">
            <button
              onClick={() => navigate("/chat")}
              className="w-full flex items-center justify-between p-2.5 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/60 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-605" />
                Ask Assistant for recommendations
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            </button>
            <button
              onClick={() => navigate("/saved")}
              className="w-full flex items-center justify-between p-2.5 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/60 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
            >
              <span className="flex items-center gap-2">
                <Compass className="w-4 h-4 text-sky-505 text-sky-500" />
                Browse saved travel boards
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            </button>
            <button
              onClick={() => navigate("/profile")}
              className="w-full flex items-center justify-between p-2.5 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/60 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
            >
              <span className="flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-teal-605" />
                Connect calendar accounts
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
export default Home;
