import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Compass, MapPin, Calendar, Sparkles, TrendingUp, ArrowRight, UserPlus } from "lucide-react";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import { WeatherCard } from "../components/shared/WeatherCard";

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { generateNewMockTrip, setActiveTrip, activeTrip, saveTrip } = useTravelPlanner();

  // Search form state
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState<"Budget" | "Moderate" | "Luxury">("Moderate");
  const [style, setStyle] = useState<"Adventure" | "Relaxed" | "Cultural" | "Family">("Cultural");

  const popularDestinations = [
    {
      city: "Madurai",
      desc: "City of Temples & Historic Festivities",
      image: "https://images.unsplash.com/photo-1600100397608-f010e423b971?auto=format&fit=crop&w=400&q=80",
      days: 3
    },
    {
      city: "Goa",
      desc: "Sandy Coastlines, Shacks & Historic Churches",
      image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80",
      days: 4
    },
    {
      city: "Chennai",
      desc: "Gateway of the South & Marina Beachfronts",
      image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=400&q=80",
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

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!destination.trim()) return;

    const newTrip = generateNewMockTrip(destination, days);
    newTrip.budget = budget;
    newTrip.travelStyle = style;
    newTrip.estimatedCost = (budget === "Budget" ? 80 : budget === "Moderate" ? 150 : 350) * days * newTrip.travelersCount;
    
    // Save to local context active state & save as draft
    setActiveTrip(newTrip);
    saveTrip(newTrip);
    navigate("/planner");
  };

  const handleQuickPlan = (city: string, daysCount: number) => {
    const newTrip = generateNewMockTrip(city, daysCount);
    setActiveTrip(newTrip);
    saveTrip(newTrip);
    navigate("/planner");
  };

  return (
    <div className="space-y-6 pb-20 sm:pb-8">
      
      {/* 1. Hero Banner */}
      <div className="relative rounded-[28px] overflow-hidden bg-slate-900 text-white min-h-[220px] sm:min-h-[280px] flex items-center p-6 sm:p-10 text-left">
        {/* Banner Cover Image */}
        <img
          src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=80"
          alt="Travel Landscape"
          className="absolute inset-0 w-full h-full object-cover opacity-40 select-none pointer-events-none"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-900/50 to-transparent" />
        
        <div className="relative z-10 max-w-lg space-y-3 sm:space-y-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/20 backdrop-blur-md border border-teal-500/30 text-[10px] font-bold text-teal-400 uppercase tracking-widest">
            <Sparkles className="w-3.5 h-3.5" />
            AI Travel Agent Ready
          </span>
          <h1 className="font-heading text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight">
            Your Next Adventure Starts Here
          </h1>
          <p className="text-xs sm:text-sm text-slate-350 dark:text-slate-300 font-medium leading-relaxed">
            Generate tailor-made daily itineraries, discover dining spots, and synchronize schedule slots instantly using AI.
          </p>
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
        <div className="lg:col-span-2 p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm text-left">
          <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 mb-4">
            <Compass className="w-5 h-5 text-teal-605" />
            AI Itinerary Generator
          </h3>

          <form onSubmit={handleSearchSubmit} className="space-y-4">
            
            {/* Destination inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">
                  Budget Target
                </label>
                <select
                  value={budget}
                  onChange={(e) => setBudget(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                >
                  <option value="Budget" className="dark:bg-[#111827]">Budget Saver</option>
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
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 hover-scale shadow-md"
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
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
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
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
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
