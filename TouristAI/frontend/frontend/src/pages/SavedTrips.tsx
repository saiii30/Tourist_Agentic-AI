import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, Users, DollarSign, ExternalLink, Trash2, Copy, Folder, Heart, Edit3, Star, Share2 } from "lucide-react";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import type { TripDetails } from "../context/TravelPlannerContext";
import { motion, AnimatePresence } from "framer-motion";
import ShareDialog from "../components/dialogs/ShareDialog";

type TripTab = "Upcoming" | "Draft" | "Completed" | "Cancelled" | "Favorites" | "Archived";

export const SavedTrips: React.FC = () => {
  const navigate = useNavigate();
  const { savedTrips, deleteTrip, duplicateTrip, setActiveTrip, updateActiveTrip } = useTravelPlanner();
  const [activeTab, setActiveTab] = useState<TripTab>("Upcoming");

  // Share Dialog state
  const [shareTrip, setShareTrip] = useState<TripDetails | null>(null);

  // Filter saved trips based on tab selection
  const filteredTrips = savedTrips.filter((trip) => {
    if (activeTab === "Favorites") {
      return trip.isFavorite;
    }
    if (activeTab === "Archived") {
      return (trip.status as string) === "Archived";
    }
    const status = trip.status || (trip.calendarSynced ? "Upcoming" : "Draft");
    // Ensure archived doesn't bleed into regular tabs
    if ((status as string) === "Archived" && (activeTab as string) !== "Archived") {
      return false;
    }
    return (status as string) === (activeTab as string);
  });

  const handleOpenTrip = (trip: TripDetails) => {
    setActiveTrip(trip);
    navigate("/planner");
  };

  const handleEditTrip = (trip: TripDetails) => {
    setActiveTrip(trip);
    navigate("/planner?edit=true");
  };

  const toggleFavorite = (tripId: string) => {
    // Check if the trip is active, update it
    updateActiveTrip((prev) => {
      if (prev && prev.id === tripId) {
        return {
          ...prev,
          isFavorite: !prev.isFavorite,
          historyTimeline: [
            {
              id: `hist-fav-${Date.now()}`,
              action: !prev.isFavorite ? "Trip marked as Favorite" : "Trip removed from Favorites",
              timestamp: "Just now",
              iconName: "heart"
            },
            ...prev.historyTimeline
          ]
        };
      }
      return prev;
    });

    // Update in saved array
    const target = savedTrips.find((t) => t.id === tripId);
    if (target) {
      const updated = {
        ...target,
        isFavorite: !target.isFavorite,
        historyTimeline: [
          {
            id: `hist-fav-${Date.now()}`,
            action: !target.isFavorite ? "Trip marked as Favorite" : "Trip removed from Favorites",
            timestamp: "Just now",
            iconName: "heart"
          },
          ...target.historyTimeline
        ]
      };
      // Save it by calling context saveTrip
      setActiveTrip(updated);
    }
  };

  const tabs: TripTab[] = ["Upcoming", "Draft", "Completed", "Cancelled", "Favorites", "Archived"];

  return (
    <div className="space-y-6 pb-20 sm:pb-8 text-left max-w-5xl mx-auto">
      
      {/* Page Header */}
      <div>
        <h2 className="font-heading text-xl sm:text-2xl font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <Folder className="w-6 h-6 text-teal-605" />
          My Saved Escapes
        </h2>
        <p className="text-xs text-slate-455 dark:text-slate-400 mt-1">
          Review, edit parameters, or synchronize schedules with Google Calendar collections.
        </p>
      </div>

      {/* Tabs Layout */}
      <div className="flex items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 pb-px overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const count = tab === "Favorites"
            ? savedTrips.filter((t) => t.isFavorite).length
            : tab === "Archived"
            ? savedTrips.filter((t) => (t.status as string) === "Archived").length
            : savedTrips.filter((t) => {
                const status = t.status || (t.calendarSynced ? "Upcoming" : "Draft");
                return (status as string) === (tab as string) && (status as string) !== "Archived";
              }).length;

          const active = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`relative px-4 py-2 text-xs font-bold transition-colors select-none flex-shrink-0 ${
                active
                  ? "text-teal-600 dark:text-teal-400"
                  : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-350"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="activeTabUnderline"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-600 dark:bg-teal-400"
                  transition={{ type: "spring", stiffness: 350, damping: 25 }}
                />
              )}
              <span className="flex items-center gap-1.5">
                {tab}
                <span className={`px-1.5 py-0.5 rounded text-[9.5px] font-extrabold ${
                  active 
                    ? "bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-teal-450" 
                    : "bg-slate-100 dark:bg-slate-900 text-slate-500"
                }`}>
                  {count}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Grid List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
        <AnimatePresence mode="wait">
          {filteredTrips.length === 0 ? (
            <motion.div
              key="empty-saved"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="col-span-full py-16 flex flex-col items-center justify-center text-center space-y-4 max-w-sm mx-auto"
            >
              <div className="w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/30 flex items-center justify-center text-teal-605">
                <Heart className="w-7 h-7 text-teal-600 dark:text-teal-400 animate-pulse" />
              </div>
              <div>
                <h4 className="font-heading text-base font-extrabold text-slate-800 dark:text-slate-150">
                  No trips yet.
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Generate your first AI trip using our advanced itinerary core to start exploring destinations.
                </p>
              </div>
              <button
                onClick={() => navigate("/")}
                className="px-5 py-2.5 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold hover-scale shadow-md shadow-teal-600/10"
              >
                Generate First Trip
              </button>
            </motion.div>
          ) : (
            filteredTrips.map((trip) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ duration: 0.2 }}
                className="group relative flex flex-col rounded-2xl overflow-hidden border border-slate-200/60 dark:border-slate-800/60 bg-white dark:bg-[#111827] shadow-sm hover:shadow-md transition-all hover-scale"
              >
                {/* Image Cover */}
                <div className="h-36 relative bg-slate-100 dark:bg-slate-800">
                  <img
                    src={trip.bannerImage}
                    alt={trip.cityName}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 to-transparent" />
                  
                  {/* Favorite Top Action Button */}
                  <button
                    onClick={() => toggleFavorite(trip.id)}
                    className="absolute top-3 left-3 p-2 rounded-xl bg-black/40 backdrop-blur-md border border-white/10 text-white hover:text-rose-500 hover:bg-black/60 transition-colors z-10"
                    aria-label="Mark Favorite"
                  >
                    <Star className={`w-4 h-4 ${trip.isFavorite ? "fill-rose-500 text-rose-500" : "text-white"}`} />
                  </button>

                  {/* Calendar Sync Status */}
                  <span className={`absolute top-3 right-3 px-2.5 py-0.5 rounded-full text-[9px] font-extrabold border backdrop-blur-md ${
                    trip.calendarSynced
                      ? "bg-emerald-50/75 text-emerald-700 border-emerald-200/30 dark:bg-emerald-950/40 dark:text-emerald-400"
                      : "bg-amber-50/75 text-amber-700 border-amber-200/30 dark:bg-amber-950/40 dark:text-amber-400"
                  }`}>
                    {trip.calendarSynced ? "Calendar Synced" : "Pending Sync"}
                  </span>

                  {/* Title & Dates */}
                  <div className="absolute bottom-3 left-4 text-white text-left space-y-0.5">
                    <h3 className="font-heading text-base font-extrabold tracking-tight">
                      {trip.cityName}
                    </h3>
                    <p className="text-[10px] text-slate-200 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-350" />
                      {trip.startDate} · {trip.durationDays} Days Plan
                    </p>
                  </div>
                </div>

                {/* Card Specs Info */}
                <div className="p-4 flex items-center justify-between border-b border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10 text-[11px]">
                  <div className="flex items-center gap-1 font-bold text-teal-700 dark:text-teal-400">
                    <DollarSign className="w-4 h-4 text-slate-400" />
                    <span>Cost: ₹{trip.estimatedCost}</span>
                  </div>
                  <div className="flex items-center gap-1 font-semibold text-slate-500 dark:text-slate-405">
                    <Users className="w-3.5 h-3.5 text-slate-450" />
                    <span>{trip.travelersCount} Travelers ({trip.budget})</span>
                  </div>
                </div>

                {/* Footer Action buttons */}
                <div className="p-3 flex items-center gap-1.5 justify-end bg-white dark:bg-[#111827]">
                  {/* Delete */}
                  <button
                    onClick={() => deleteTrip(trip.id)}
                    className="p-2 rounded-xl border border-slate-150 dark:border-slate-805 text-slate-400 hover:text-red-500 hover:bg-rose-50 dark:hover:bg-red-950/20 transition-colors mr-auto hover-scale"
                    aria-label="Delete Trip"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  {/* Share */}
                  <button
                    onClick={() => setShareTrip(trip)}
                    className="p-2 rounded-xl border border-slate-150 dark:border-slate-805 text-slate-450 hover:text-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors hover-scale"
                    aria-label="Share Trip"
                  >
                    <Share2 className="w-4 h-4" />
                  </button>

                  {/* Duplicate */}
                  <button
                    onClick={() => duplicateTrip(trip.id)}
                    className="px-3 py-2 rounded-xl border border-slate-205 dark:border-slate-800 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                  >
                    <Copy className="w-3.5 h-3.5 text-slate-505" />
                    <span>Clone</span>
                  </button>

                  {/* Edit */}
                  <button
                    onClick={() => handleEditTrip(trip)}
                    className="px-3 py-2 rounded-xl border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-355 hover:bg-slate-50 dark:hover:bg-slate-900 text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                    <span>Edit</span>
                  </button>

                  {/* Open */}
                  <button
                    onClick={() => handleOpenTrip(trip)}
                    className="px-3.5 py-2 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-[10.5px] font-bold flex items-center gap-1.5 hover-scale shadow-sm"
                  >
                    <span>Open</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>

              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Share Dialog Mount */}
      {shareTrip && (
        <ShareDialog
          isOpen={true}
          onClose={() => setShareTrip(null)}
          tripName={shareTrip.cityName}
        />
      )}

    </div>
  );
};
export default SavedTrips;
