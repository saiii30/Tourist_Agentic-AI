import React, { useState, useEffect } from "react";
import { X, Calendar, DollarSign, Compass, Users, FileText, Check, Plus, Zap, RotateCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTravelPlanner } from "../../context/TravelPlannerContext";
import type { TripDetails, Activity } from "../../context/TravelPlannerContext";

interface ModifyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveSuccess?: () => void;
}

export const ModifyDrawer: React.FC<ModifyDrawerProps> = ({ isOpen, onClose, onSaveSuccess }) => {
  const { activeTrip, updateActiveTrip, setChatMessages } = useTravelPlanner();

  // Local form states
  const [budget, setBudget] = useState<TripDetails["budget"]>("Moderate");
  const [travelStyle, setTravelStyle] = useState<TripDetails["travelStyle"]>("Cultural");
  const [travelersCount, setTravelersCount] = useState<number>(4);
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [activitiesByDay, setActivitiesByDay] = useState<Record<number, Activity[]>>({});
  
  // Undo cache simulation
  const [undoCache, setUndoCache] = useState<TripDetails | null>(null);

  // Custom action toggles
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [selectedHotelId, setSelectedHotelId] = useState("");
  const [selectedRestId, setSelectedRestId] = useState("");

  useEffect(() => {
    if (activeTrip && isOpen) {
      setBudget(activeTrip.budget);
      setTravelStyle(activeTrip.travelStyle);
      setTravelersCount(activeTrip.travelersCount);
      setStartDate(activeTrip.startDate);
      setEndDate(activeTrip.endDate);
      setNotes(activeTrip.notesText || "");
      setActivitiesByDay(JSON.parse(JSON.stringify(activeTrip.itinerary)));
      if (activeTrip.hotels.length > 0) {
        setSelectedHotelId(activeTrip.hotels[0].id);
      }
      setUndoCache(JSON.parse(JSON.stringify(activeTrip)));
    }
  }, [activeTrip, isOpen]);

  const handleSaveChanges = () => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) || 1;

    updateActiveTrip((prev) => {
      if (!prev) return null;

      // Sync updated hotel selection
      const matchedHotel = prev.hotels.find((h) => h.id === selectedHotelId);
      const updatedHotels = matchedHotel ? [matchedHotel, ...prev.hotels.filter((h) => h.id !== selectedHotelId)] : prev.hotels;

      return {
        ...prev,
        budget,
        travelStyle,
        travelersCount,
        startDate,
        endDate,
        durationDays: diffDays,
        itinerary: activitiesByDay,
        hotels: updatedHotels,
        notesText: notes,
        estimatedCost: (budget === "Low" ? 4000 : budget === "Moderate" ? 8450 : 19000),
        historyTimeline: [
          {
            id: `hist-mod-${Date.now()}`,
            action: "Trip parameters and activities modified",
            timestamp: "Just now",
            iconName: "edit"
          },
          ...prev.historyTimeline
        ]
      };
    });

    if (activeTrip) {
      const matchedHotel = activeTrip.hotels.find((h) => h.id === selectedHotelId);
      const updatedHotels = matchedHotel ? [matchedHotel, ...activeTrip.hotels.filter((h) => h.id !== selectedHotelId)] : activeTrip.hotels;

      setChatMessages((prevMessages) => {
        return prevMessages.map((msg) => {
          if (msg.tripCard && msg.tripCard.id === activeTrip.id) {
            return {
              ...msg,
              tripCard: {
                ...msg.tripCard,
                budget,
                travelStyle,
                travelersCount,
                startDate,
                endDate,
                durationDays: diffDays,
                itinerary: activitiesByDay,
                hotels: updatedHotels,
                notesText: notes,
                estimatedCost: (budget === "Low" ? 4000 : budget === "Moderate" ? 8450 : 19000),
              }
            };
          }
          return msg;
        });
      });
    }

    if (onSaveSuccess) onSaveSuccess();
    onClose();
  };

  const handleUndo = () => {
    if (undoCache) {
      setBudget(undoCache.budget);
      setTravelStyle(undoCache.travelStyle);
      setTravelersCount(undoCache.travelersCount);
      setStartDate(undoCache.startDate);
      setEndDate(undoCache.endDate);
      setNotes(undoCache.notesText || "");
      setActivitiesByDay(JSON.parse(JSON.stringify(undoCache.itinerary)));
      if (undoCache.hotels.length > 0) {
        setSelectedHotelId(undoCache.hotels[0].id);
      }
      alert("Undo successful: Restored previous changes.");
    }
  };

  const handleOptimizeRoute = async () => {
    setIsOptimizing(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsOptimizing(false);
    
    // Shuffle slightly to simulate optimization
    setActivitiesByDay(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(day => {
        const list = [...updated[Number(day)]];
        if (list.length > 2) {
          // Move morning activity to index 1 and breakfast to 0
          const morning = list.find(a => a.slot === "Morning Activity");
          const rest = list.filter(a => a.slot !== "Morning Activity");
          if (morning) {
            rest.splice(1, 0, morning);
          }
          updated[Number(day)] = rest;
        }
      });
      return updated;
    });

    alert("✨ Route Optimized! Connected timeline path reordered for minimal travel time & distance.");
  };

  const handleAddRestaurantActivity = () => {
    if (!selectedRestId || !activeTrip) return;
    const rest = activeTrip.restaurants.find((r) => r.id === selectedRestId);
    if (!rest) return;

    const newAct: Activity = {
      id: `rest-act-${Date.now()}`,
      title: `Dine at ${rest.name} (${rest.cuisine})`,
      time: "02:00 PM",
      duration: "1.5 hours",
      category: "Food",
      rating: rest.rating,
      entryFee: "Pay per dish",
      description: `Premium dining visit. Distance: ${rest.distanceFromHotel} from hotel.`,
      location: rest.name,
      image: rest.image,
      slot: "Lunch"
    };

    setActivitiesByDay((prev) => {
      const updated = { ...prev };
      updated[1] = [newAct, ...(updated[1] || [])];
      return updated;
    });

    setSelectedRestId("");
    alert(`🍽 Added ${rest.name} restaurant stop to Day 1 itinerary timeline.`);
  };



  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Drawer Sheet */}
          <motion.div
            initial={{
              x: window.innerWidth >= 640 ? "100%" : 0,
              y: window.innerWidth < 640 ? "100%" : 0
            }}
            animate={{ x: 0, y: 0 }}
            exit={{
              x: window.innerWidth >= 640 ? "100%" : 0,
              y: window.innerWidth < 640 ? "100%" : 0
            }}
            transition={{ type: "spring", damping: 30, stiffness: 260 }}
            className="fixed z-50 bg-white dark:bg-[#111827] shadow-2xl flex flex-col
              w-full h-[90vh] bottom-0 left-0 rounded-t-[28px] 
              sm:w-[480px] sm:h-screen sm:top-0 sm:right-0 sm:left-auto sm:rounded-t-none sm:rounded-l-[28px] border-l border-slate-200 dark:border-slate-800"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
              <div>
                <h3 className="font-heading text-lg font-bold text-slate-800 dark:text-slate-100">
                  Modify Trip Experience
                </h3>
                <p className="text-xs text-slate-400 font-medium">
                  Refine parameters or optimize timeline maps
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-xl text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
              >
                <X className="w-5.5 h-5.5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 no-scrollbar">
              
              {/* Premium Operation Shortcuts */}
              <div className="space-y-2.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
                  Quick Tasks
                </span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={handleOptimizeRoute}
                    disabled={isOptimizing}
                    className="p-3 bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/30 rounded-xl text-left flex items-center gap-2 hover:bg-teal-50 transition-colors group"
                  >
                    <Zap className={`w-4 h-4 text-teal-605 group-hover:scale-110 transition-transform ${isOptimizing ? "animate-bounce" : ""}`} />
                    <div className="text-left">
                      <p className="text-[11px] font-bold text-teal-800 dark:text-teal-400">
                        {isOptimizing ? "Optimizing..." : "Optimize Route"}
                      </p>
                      <p className="text-[9px] text-slate-450 truncate">Reorders timeline path</p>
                    </div>
                  </button>

                  <button
                    onClick={handleUndo}
                    className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-205 dark:border-slate-800 rounded-xl text-left flex items-center gap-2 hover:bg-slate-100 transition-colors"
                  >
                    <RotateCcw className="w-4 h-4 text-slate-550" />
                    <div className="text-left">
                      <p className="text-[11px] font-bold text-slate-700 dark:text-slate-300">Undo Action</p>
                      <p className="text-[9px] text-slate-400">Reverts last changes</p>
                    </div>
                  </button>
                </div>
              </div>

              <hr className="border-slate-100 dark:border-slate-800/80" />

              {/* Trip Preferences */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-slate-450 uppercase tracking-wider">
                  Modify Preferences
                </h4>
                
                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                      Start Date
                    </label>
                    <div className="relative">
                      <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-transparent text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                      End Date
                    </label>
                    <div className="relative">
                      <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-transparent text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Travelers Count */}
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                    Number of Travelers
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setTravelersCount(c => Math.max(1, c - 1))}
                      className="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center justify-center font-bold text-slate-655"
                    >
                      -
                    </button>
                    <span className="w-8 text-center text-xs font-bold text-slate-800 dark:text-slate-200">
                      {travelersCount}
                    </span>
                    <button
                      onClick={() => setTravelersCount(c => c + 1)}
                      className="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center justify-center font-bold text-slate-655"
                    >
                      +
                    </button>
                    <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      Travelers
                    </span>
                  </div>
                </div>

                {/* Budget */}
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">
                    Budget Tier
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(["Low", "Moderate", "Luxury"] as const).map((tier) => (
                      <button
                        key={tier}
                        onClick={() => setBudget(tier)}
                        className={`py-2 px-3 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${
                          budget === tier
                            ? "border-teal-600 bg-teal-50/50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-450 shadow-sm"
                            : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850 text-slate-500 dark:text-slate-400"
                        }`}
                      >
                        <DollarSign className="w-4 h-4" />
                        {tier}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Travel Style */}
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">
                    Travel Style
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {(["Adventure", "Relaxed", "Cultural", "Family"] as const).map((style) => (
                      <button
                        key={style}
                        onClick={() => setTravelStyle(style)}
                        className={`py-2 px-3 rounded-xl border text-xs font-semibold flex items-center gap-2 transition-all ${
                          travelStyle === style
                            ? "border-teal-605 bg-teal-50/50 dark:bg-teal-950/20 text-teal-750 dark:text-teal-400"
                            : "border-slate-200 dark:border-slate-805 hover:bg-slate-50 dark:hover:bg-slate-850 text-slate-500 dark:text-slate-400"
                        }`}
                      >
                        <Compass className="w-4.5 h-4.5" />
                        {style}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <hr className="border-slate-100 dark:border-slate-800/80" />

              {/* Accommodation Selector */}
              {activeTrip && activeTrip.hotels.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-405 uppercase tracking-wider">
                    Change Accommodations
                  </h4>
                  <div className="space-y-2">
                    {activeTrip.hotels.map((h) => {
                      const active = selectedHotelId === h.id;
                      return (
                        <button
                          key={h.id}
                          onClick={() => setSelectedHotelId(h.id)}
                          className={`w-full p-3 rounded-xl border text-left flex items-start gap-3 transition-all ${
                            active
                              ? "border-teal-600 bg-teal-50/30 dark:bg-teal-950/15"
                              : "border-slate-200 dark:border-slate-805 hover:bg-slate-50 dark:hover:bg-slate-900/60"
                          }`}
                        >
                          <div className="w-12 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-slate-100 dark:bg-slate-800">
                            <img src={h.image} className="w-full h-full object-contain bg-slate-100 dark:bg-slate-900" alt="" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-[11px] font-bold text-slate-700 dark:text-slate-300 truncate">{h.name}</p>
                            <p className="text-[9.5px] text-slate-400">₹{h.pricePerNight} / night · {h.distanceFromCenter}</p>
                          </div>
                          <div className={`w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 mt-2 ${
                            active ? "border-teal-500 bg-teal-500 text-white" : "border-slate-300"
                          }`}>
                            {active && <Check className="w-3 h-3" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <hr className="border-slate-100 dark:border-slate-800/80" />

              {/* Restaurant Selector */}
              {activeTrip && activeTrip.restaurants.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-405 uppercase tracking-wider">
                    Add Restaurant Stop
                  </h4>
                  <div className="flex gap-2">
                    <select
                      value={selectedRestId}
                      onChange={(e) => setSelectedRestId(e.target.value)}
                      className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-transparent text-slate-700 dark:text-slate-350 outline-none"
                    >
                      <option value="" className="dark:bg-[#111827]">-- Select Dining --</option>
                      {activeTrip.restaurants.map((r) => (
                        <option key={r.id} value={r.id} className="dark:bg-[#111827]">
                          {r.name} ({r.cuisine} - {r.priceTier})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={handleAddRestaurantActivity}
                      className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 hover-scale shadow-sm"
                    >
                      <Plus className="w-4 h-4" />
                      Add Stop
                    </button>
                  </div>
                </div>
              )}

              <hr className="border-slate-100 dark:border-slate-800/80" />

              {/* Notes */}
              <div>
                <label className="block text-xs font-bold text-slate-450 uppercase tracking-wider mb-2">
                  Trip Notes (Offline SQLite Sync)
                </label>
                <div className="relative">
                  <FileText className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                  <textarea
                    rows={3}
                    placeholder="Add emergency contacts, flight details, restaurant suggestions..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-transparent text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500 resize-none"
                  />
                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="p-5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-end gap-2 flex-shrink-0">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-805 text-xs font-semibold text-slate-500 dark:text-slate-450 hover:bg-slate-50 dark:hover:bg-slate-850 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveChanges}
                className="px-4 py-2 rounded-xl bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white shadow-md shadow-teal-600/10 text-xs font-semibold flex items-center gap-1.5 hover-scale"
              >
                <Check className="w-4 h-4" />
                Apply Changes
              </button>
            </div>

          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
export default ModifyDrawer;
