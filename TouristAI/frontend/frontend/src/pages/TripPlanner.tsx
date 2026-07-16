import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTravelPlanner } from "../context/TravelPlannerContext";

// Dialog components
import { ModifyDrawer } from "../components/dialogs/ModifyDrawer";
import { SaveDialog } from "../components/dialogs/SaveDialog";
import { CalendarSyncDialog } from "../components/dialogs/CalendarSyncDialog";
import { RegenerateDialog } from "../components/dialogs/RegenerateDialog";
import { ShareDialog } from "../components/dialogs/ShareDialog";
import { FloatingAICopilot } from "../components/dialogs/FloatingAICopilot";
import { AddToItineraryDialog } from "../components/dialogs/AddToItineraryDialog";
import { ActivityCard } from "../components/shared/ActivityCard";

// Icons
import {
  Calendar, Users, DollarSign, Edit3, RefreshCw, Share2,
  CheckCircle2, AlertTriangle, AlertCircle, Sparkles,
  ExternalLink, ShieldAlert, BookOpen, Thermometer, FileText,
  Activity as ActivityIcon, PhoneCall, Wallet, CheckSquare, Square,
  Bell, Volume2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import VoiceNotificationService from "../services/VoiceNotificationService";

interface Notification {
  id: string;
  type: string;
  source: string;
  priority: "critical" | "high" | "medium" | "low";
  trigger: string;
  event_time: string | null;
  title: string;
  text: string;
  voice: string;
  play_voice: boolean;
  spoken: boolean;
  status: "pending" | "active" | "spoken" | "dismissed" | "expired";
  action?: { label: string; type: string } | null;
}

const parseNotificationTime = (eventTime?: string | null): number | null => {
  if (!eventTime) return null;
  const parsed = new Date(eventTime).getTime();
  return Number.isNaN(parsed) ? null : parsed;
};

const refreshRealtimeNotifications = (items: Notification[], nowMs = Date.now()): Notification[] => {
  return items.map((item) => {
    if (item.spoken || item.status === "spoken" || item.status === "dismissed") {
      return item;
    }

    const eventMs = parseNotificationTime(item.event_time);
    const isImmediate = !eventMs && ["immediate", "trip_created", "calendar_saved"].includes(item.trigger);

    if ((eventMs && eventMs <= nowMs) || isImmediate) {
      if (eventMs && nowMs - eventMs > 60 * 60 * 1000) {
        return { ...item, status: "expired" };
      }
      return { ...item, status: "active" };
    }

    return item.status === "active" ? { ...item, status: "pending" } : item;
  });
};

type PlannerTab = "Overview" | "Itinerary" | "Hotels" | "Restaurants" | "Map" | "Budget" | "Notes" | "Smart Assistant";
type PlannerTab = "Overview" | "Itinerary" | "Hotels" | "Restaurants" | "Attractions" | "Map" | "Budget" | "Notes";

export const TripPlanner: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { activeTrip, updateActiveTrip, generateNewMockTrip, saveTrip, syncCalendar } = useTravelPlanner();

  // Page load and active workspace tab
  const [activeTab, setActiveTab] = useState<PlannerTab>("Overview");
  const [activeItineraryDay, setActiveItineraryDay] = useState<number>(1);

  // Modals / Drawers states
  const [isModifyOpen, setIsModifyOpen] = useState(false);
  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [isRegenOpen, setIsRegenOpen] = useState(false);
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isAddItineraryOpen, setIsAddItineraryOpen] = useState(false);
  const [itemToAdd, setItemToAdd] = useState<{ type: 'hotel' | 'restaurant' | 'attraction', id: string, name: string, location: string, rating: number, image: string } | null>(null);
  const [mapSearchQuery, setMapSearchQuery] = useState<string | null>(null);

  // Voice alerts state and sync handlers
  const [notifications, setNotifications] = useState<Notification[]>([]);


  useEffect(() => {
    if (activeTrip?.notifications) {
      setNotifications(refreshRealtimeNotifications(activeTrip.notifications));
    }
  }, [activeTrip?.notifications]);

  useEffect(() => {
    if (!activeTrip || notifications.length === 0) return;

    const syncRealtimeStatus = () => {
      setNotifications((prev) => {
        const updated = refreshRealtimeNotifications(prev);
        const changed = updated.some((item, index) => item.status !== prev[index]?.status);
        if (changed) {
          updateActiveTrip((trip) => trip ? { ...trip, notifications: updated } : null);
        }
        return changed ? updated : prev;
      });
    };

    syncRealtimeStatus();
    const timer = window.setInterval(syncRealtimeStatus, 30000);
    return () => window.clearInterval(timer);
  }, [activeTrip?.id, notifications.length, updateActiveTrip]);

  const handlePlayVoice = (notif: Notification) => {
    VoiceNotificationService.getInstance().speak(notif.voice, () => {
      handleMarkHeard(notif);
    });
  };

  const handleMarkHeard = (notif: Notification) => {
    setNotifications((prev) => {
      const updated = prev.map((n) =>
        n.id === notif.id ? { ...n, spoken: true, status: "spoken" as const } : n
      );
      if (activeTrip && updateActiveTrip) {
        updateActiveTrip((prev) => prev ? { ...prev, notifications: updated } : null);
      }
      return updated;
    });
  };

  // Automatically trigger voice playback if active, play_voice=true, and not spoken yet
  useEffect(() => {
    const autoplay = notifications.find(n => n.play_voice && !n.spoken && n.status === "active");
    if (autoplay) {
      handlePlayVoice(autoplay);
    }
  }, [notifications]);

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      VoiceNotificationService.getInstance().stop();
    };
  }, []);

  // Currency converter variables
  const [usdAmount, setUsdAmount] = useState("100");
  const [inrAmount, setInrAmount] = useState("8350");

  // Offline status simulator
  const [isOffline, setIsOffline] = useState(false);

  // Toast status states
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error" | "info">("success");

  // Check if ?edit=true parameter is present on mount
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("edit") === "true") {
      setIsModifyOpen(true);
      navigate("/planner", { replace: true });
    }
  }, [location.search, navigate]);

  useEffect(() => {
    if (!activeTrip) return;
    const days = Object.keys(activeTrip.itinerary).map(Number).sort((a, b) => a - b);
    if (days.length > 0 && !days.includes(activeItineraryDay)) {
      setActiveItineraryDay(days[0]);
    }
  }, [activeTrip, activeItineraryDay]);

  // We removed the mock data fallback here!
  // Simply wait for the real activeTrip from the AI builder.

  const triggerToast = (msg: string, type: "success" | "error" | "info" = "success") => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  if (!activeTrip) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 dark:bg-[#0b0f19] p-8 text-center">
        <Sparkles className="w-12 h-12 text-teal-500 mb-4 animate-pulse" />
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">No Itinerary Generated Yet</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-md">
          Chat with the AI Assistant to plan your next adventure. Your custom itinerary, hotels, restaurants, and schedule will appear here. No mock data will be shown!
        </p>
      </div>
    );
  }

  // Dynamic Statistics Calculations
  const itineraryDayEntries = Object.entries(activeTrip.itinerary)
    .map(([dayStr, list]) => [Number(dayStr), list] as const)
    .sort(([dayA], [dayB]) => dayA - dayB);
  const activeDayEntry = itineraryDayEntries.find(([dayNum]) => dayNum === activeItineraryDay) || itineraryDayEntries[0];
  const activeDayNum = activeDayEntry?.[0] || 1;
  const activeDayActivities = activeDayEntry?.[1] || [];
  const allActivities = Object.values(activeTrip.itinerary).flat();

  // Average Rating
  const ratings = [
    ...allActivities.map(a => a.rating).filter(Boolean),
    ...(activeTrip.hotels || []).map(h => h.rating).filter(Boolean),
    ...(activeTrip.restaurants || []).map(r => r.rating).filter(Boolean)
  ];
  const avgRating = ratings.length > 0 
    ? (ratings.reduce((sum, val) => sum + val, 0) / ratings.length).toFixed(1)
    : "4.8";

  const discoveredPlaces = activeTrip.discoveredPlaces ?? [];
  const attractionsCount = discoveredPlaces.length;


  const restaurantsCount = activeTrip.restaurants && activeTrip.restaurants.length > 0
    ? activeTrip.restaurants.length
    : allActivities.filter(a => a.category === "Food" || a.restaurant).length;

  const hotelsCount = activeTrip.hotels && activeTrip.hotels.length > 0
    ? activeTrip.hotels.length
    : Array.from(new Set(allActivities.filter(a => a.hotel || a.category === "Relaxation").map(a => a.hotel || a.title))).length || 1;

  const totalDistance = attractionsCount > 0 ? attractionsCount * 6 + 5 : 20;
  const activeHours = activeTrip.durationDays * 8;

  const getTemp = (summary: string) => {
    if (!summary) return "26°C";
    const match = summary.match(/(\d+(?:\.\d+)?)\s*°C/);
    return match ? `${match[1]}°C` : "26°C";
  };
  const tempStr = getTemp(activeTrip.weatherSummary);

  const tripHighlights = Array.from(
    new Set(
      allActivities
        .filter((activity) => activity.category !== "Food")
        .map((activity) => activity.title || activity.location)
        .filter(Boolean)
    )
  ).slice(0, 3);
  const diningHighlights = Array.from(
    new Set(
      [
        ...(activeTrip.restaurants || []).map((restaurant) => restaurant.name),
        ...allActivities.map((activity) => activity.restaurant).filter(Boolean)
      ].filter(Boolean)
    )
  ).slice(0, 2);
  const summaryHighlights = tripHighlights.length > 0
    ? tripHighlights.join(", ")
    : `${activeTrip.travelStyle.toLowerCase()} experiences`;
  const diningSummary = diningHighlights.length > 0
    ? ` Dining highlights include ${diningHighlights.join(", ")}.`
    : "";
  const nextRealtimeNotification = notifications
    .filter((item) => item.status === "pending")
    .map((item) => ({ item, eventMs: parseNotificationTime(item.event_time) }))
    .filter(({ eventMs }) => eventMs !== null && eventMs > Date.now())
    .sort((a, b) => (a.eventMs || 0) - (b.eventMs || 0))[0]?.item;


  // Itinerary deletions and modifications
  const handleDeleteActivity = (dayNum: number, activityId: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedItinerary = { ...prev.itinerary };
      updatedItinerary[dayNum] = updatedItinerary[dayNum].filter(act => act.id !== activityId);

      const newHistory = [
        { id: `hist-del-${Date.now()}`, action: "❌ Activity removed from Day " + dayNum, timestamp: "Just now", iconName: "trash-2" },
        ...prev.historyTimeline
      ];

      triggerToast("Activity removed", "info");
      return { ...prev, itinerary: updatedItinerary, historyTimeline: newHistory };
    });
  };

  const handleFavoriteToggle = (dayNum: number, activityId: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedItinerary = { ...prev.itinerary };
      updatedItinerary[dayNum] = updatedItinerary[dayNum].map(act =>
        act.id === activityId ? { ...act, isFavorite: !act.isFavorite } : act
      );

      const act = updatedItinerary[dayNum].find(a => a.id === activityId);
      if (act) {
        triggerToast(act.isFavorite ? "Saved to favorites" : "Removed from favorites", "success");
      }
      return { ...prev, itinerary: updatedItinerary };
    });
  };

  const handleReplaceActivity = (dayNum: number, activityId: string) => {
    const alternates = [
      { title: "Indulge in Jigarthanda street sweets", desc: "Sample rich almond gum ice cream drinks, sweet halwas, and warm savory puffs in local stalls.", location: "Famous Jigarthanda Shop", entry: "₹80" },
      { title: "Tour the Thirumalai Nayakkar Palace", desc: "Gaze at the massive white architectural pillars, light/sound exhibits, and historic royal bedchambers.", location: "Nayak Palace Complex", entry: "₹300" }
    ];
    const pick = alternates[Math.floor(Math.random() * alternates.length)];

    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedItinerary = { ...prev.itinerary };
      updatedItinerary[dayNum] = updatedItinerary[dayNum].map(act => {
        if (act.id === activityId) {
          return {
            ...act,
            title: pick.title,
            description: pick.desc,
            location: pick.location,
            entryFee: pick.entry,
            rating: 4.8,
            image: "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=400&q=80"
          };
        }
        return act;
      });

      const newHistory = [
        { id: `hist-rep-${Date.now()}`, action: "🔄 Activity replaced on Day " + dayNum, timestamp: "Just now", iconName: "refresh-cw" },
        ...prev.historyTimeline
      ];

      triggerToast("Activity Replaced Successfully", "success");
      return { ...prev, itinerary: updatedItinerary, historyTimeline: newHistory };
    });
  };

  // Switch/Change Hotel from tab view directly
  const handleSwapHotel = (hotelId: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const matched = prev.hotels.find((h) => h.id === hotelId);
      const reordered = matched ? [matched, ...prev.hotels.filter((h) => h.id !== hotelId)] : prev.hotels;
      return {
        ...prev,
        hotels: reordered,
        historyTimeline: [
          { id: `hist-hot-${Date.now()}`, action: `🏨 Hotel changed: ${matched?.name}`, timestamp: "Just now", iconName: "home" },
          ...prev.historyTimeline
        ]
      };
    });
    triggerToast("Accommodation Updated Successfully!", "success");
  };

  // Reserve Restaurant Table Mock
  const handleReserveTable = (restName: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        historyTimeline: [
          { id: `hist-res-${Date.now()}`, action: `🍴 Reservation booked: ${restName}`, timestamp: "Just now", iconName: "calendar" },
          ...prev.historyTimeline
        ]
      };
    });
    triggerToast(`Table Reserved at ${restName}! Confirmation sent via SMS.`, "success");
  };

  const handleAddItemToItinerary = (dayNum: number, time: string) => {
    if (!itemToAdd) return;

    // Helper to calculate end time (1.5 hours later)
    const addIntervalToTime = (timeStr: string, minutesToAdd: number): string => {
      const match = timeStr.match(/^(\d+):(\d+)\s*(AM|PM)$/i);
      if (!match) return timeStr;
      
      let hours = parseInt(match[1], 10);
      const minutes = parseInt(match[2], 10);
      const period = match[3].toUpperCase();
      
      if (period === "PM" && hours !== 12) hours += 12;
      if (period === "AM" && hours === 12) hours = 0;
      
      const totalMinutes = hours * 60 + minutes + minutesToAdd;
      let newHours = Math.floor(totalMinutes / 60) % 24;
      const newMinutes = totalMinutes % 60;
      
      const newPeriod = newHours >= 12 ? "PM" : "AM";
      let displayHours = newHours % 12;
      if (displayHours === 0) displayHours = 12;
      
      const hStr = displayHours < 10 ? `0${displayHours}` : `${displayHours}`;
      const mStr = newMinutes < 10 ? `0${newMinutes}` : `${newMinutes}`;
      
      return `${hStr}:${mStr} ${newPeriod}`;
    };

    const endTime = addIntervalToTime(time, 90); // 1.5 hours later
    const timeRange = `${time} - ${endTime}`;

    // const newAct: any = {
    //   id: `added-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
    //   title: itemToAdd.type === 'hotel' ? `Stay at ${itemToAdd.name}` : `Dine at ${itemToAdd.name}`,
    //   time: time,
    //   duration: timeRange,
    //   category: itemToAdd.type === 'hotel' ? "Relaxation" : "Food",
    //   rating: itemToAdd.rating || 4.5,
    //   entryFee: itemToAdd.type === 'hotel' ? "Included" : "Standard pricing",
    //   description: itemToAdd.type === 'hotel' ? `Stay accommodation at ${itemToAdd.name}.` : `Enjoy meals/dining at ${itemToAdd.name}.`,
    //   location: itemToAdd.location || "",
    //   image: itemToAdd.image || "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=400&q=80",
    //   hotel: itemToAdd.type === 'hotel' ? itemToAdd.name : null,
    //   restaurant: itemToAdd.type === 'restaurant' ? itemToAdd.name : null,
    //   google_event_id: null
    // };

    const newAct: any = {
  id: `added-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,

  title:
    itemToAdd.type === "hotel"
      ? `Stay at ${itemToAdd.name}`
      : itemToAdd.type === "restaurant"
      ? `Dine at ${itemToAdd.name}`
      : `Visit ${itemToAdd.name}`,

  time,
  duration: timeRange,

  category:
    itemToAdd.type === "hotel"
      ? "Relaxation"
      : itemToAdd.type === "restaurant"
      ? "Food"
      : "Sightseeing",

  rating: itemToAdd.rating || 4.5,

  entryFee:
    itemToAdd.type === "attraction"
      ? "Free / varies"
      : itemToAdd.type === "hotel"
      ? "Included"
      : "Standard pricing",

  description:
    itemToAdd.type === "attraction"
      ? `Visit ${itemToAdd.name}.`
      : itemToAdd.type === "hotel"
      ? `Stay at ${itemToAdd.name}.`
      : `Dine at ${itemToAdd.name}.`,

  location: itemToAdd.location || "",

  image:
    itemToAdd.image ||
    "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=400&q=80",

  hotel: itemToAdd.type === "hotel" ? itemToAdd.name : null,

  restaurant:
    itemToAdd.type === "restaurant"
      ? itemToAdd.name
      : null,

  google_event_id: null,
};

    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedItinerary = { ...prev.itinerary };
      const currentDayActivities = updatedItinerary[dayNum] ? [...updatedItinerary[dayNum]] : [];

      currentDayActivities.push(newAct);

      const timeToMinutes = (timeStr: string): number => {
        if (!timeStr) return 0;
        const match = timeStr.match(/^(\d+):(\d+)\s*(AM|PM)$/i);
        if (match) {
          let hours = parseInt(match[1], 10);
          const minutes = parseInt(match[2], 10);
          const period = match[3].toUpperCase();
          if (period === "PM" && hours !== 12) hours += 12;
          if (period === "AM" && hours === 12) hours = 0;
          return hours * 60 + minutes;
        }
        const match24 = timeStr.match(/^(\d+):(\d+)$/);
        if (match24) {
          const hours = parseInt(match24[1], 10);
          const minutes = parseInt(match24[2], 10);
          return hours * 60 + minutes;
        }
        return 0;
      };

      currentDayActivities.sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time));
      updatedItinerary[dayNum] = currentDayActivities;

      const newHistory = [
        { 
          id: `hist-add-${Date.now()}`, 
          action: `➕ Added ${itemToAdd.name} to Day ${dayNum} at ${time}`, 
          timestamp: "Just now", 
          iconName: "plus" 
        },
        ...prev.historyTimeline
      ];

      return { ...prev, itinerary: updatedItinerary, historyTimeline: newHistory };
    });

    triggerToast(`${itemToAdd.name} added to Day ${dayNum}!`, "success");
  };

  const handleViewOnMap = (location: string, title: string) => {
    setMapSearchQuery(`${title}, ${location}`);
    setActiveTab("Map");
  };

  // Drag and Drop States and Event Handlers
  const [draggedActivity, setDraggedActivity] = useState<{ dayNum: number; id: string } | null>(null);

  const handleDragStart = (e: React.DragEvent, dayNum: number, activityId: string) => {
    setDraggedActivity({ dayNum, id: activityId });
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, targetDayNum: number, targetActivityId: string) => {
    e.preventDefault();
    if (!draggedActivity) return;

    const sourceDayNum = draggedActivity.dayNum;
    const sourceId = draggedActivity.id;

    if (sourceDayNum === targetDayNum && sourceId === targetActivityId) {
      setDraggedActivity(null);
      return;
    }

    updateActiveTrip((prev) => {
      if (!prev) return null;

      const updatedItinerary = { ...prev.itinerary };
      const sourceList = [...(updatedItinerary[sourceDayNum] || [])];
      
      const sourceIndex = sourceList.findIndex((item) => item.id === sourceId);
      if (sourceIndex === -1) return prev;
      
      const [movedItem] = sourceList.splice(sourceIndex, 1);

      if (sourceDayNum === targetDayNum) {
        const targetIndex = sourceList.findIndex((item) => item.id === targetActivityId);
        sourceList.splice(targetIndex === -1 ? sourceList.length : targetIndex, 0, movedItem);
        updatedItinerary[sourceDayNum] = sourceList;
      } else {
        const targetList = [...(updatedItinerary[targetDayNum] || [])];
        const targetIndex = targetList.findIndex((item) => item.id === targetActivityId);
        targetList.splice(targetIndex === -1 ? targetList.length : targetIndex, 0, movedItem);
        updatedItinerary[sourceDayNum] = sourceList;
        updatedItinerary[targetDayNum] = targetList;
      }

      return {
        ...prev,
        itinerary: updatedItinerary
      };
    });

    setDraggedActivity(null);
    triggerToast("Activity order updated!", "success");
  };

  const handleDropOnDay = (e: React.DragEvent, targetDayNum: number) => {
    e.preventDefault();
    if (!draggedActivity) return;

    const sourceDayNum = draggedActivity.dayNum;
    const sourceId = draggedActivity.id;

    if (sourceDayNum === targetDayNum) return;

    updateActiveTrip((prev) => {
      if (!prev) return null;

      const updatedItinerary = { ...prev.itinerary };
      const sourceList = [...(updatedItinerary[sourceDayNum] || [])];
      const targetList = [...(updatedItinerary[targetDayNum] || [])];

      const sourceIndex = sourceList.findIndex((item) => item.id === sourceId);
      if (sourceIndex === -1) return prev;

      const [movedItem] = sourceList.splice(sourceIndex, 1);
      targetList.push(movedItem);

      updatedItinerary[sourceDayNum] = sourceList;
      updatedItinerary[targetDayNum] = targetList;

      return {
        ...prev,
        itinerary: updatedItinerary
      };
    });

    setDraggedActivity(null);
    triggerToast(`Moved activity to Day ${targetDayNum}!`, "success");
  };

  const handleDragEnd = () => {
    setDraggedActivity(null);
  };

  // Toggle checklist checkbox items
  const handleToggleChecklist = (itemId: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedList = prev.packingChecklist.map((item) =>
        item.id === itemId ? { ...item, checked: !item.checked } : item
      );
      return { ...prev, packingChecklist: updatedList };
    });
  };

  // Offline notes text area updater
  const handleUpdateNotesText = (val: string) => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      return { ...prev, notesText: val };
    });
  };

  // Stepper calculations
  const isBudgetSet = activeTrip.budget !== undefined;
  const isTravelersSet = activeTrip.travelersCount > 0;
  const isGenerated = Object.keys(activeTrip.itinerary).length > 0;
  const isSaved = activeTrip.status === "Upcoming" || activeTrip.status === "Completed";
  const isSynced = activeTrip.calendarSynced;

  // Currency Converter calculation
  const handleUsdChange = (val: string) => {
    setUsdAmount(val);
    const numeric = parseFloat(val);
    if (!isNaN(numeric)) {
      setInrAmount((numeric * 83.5).toFixed(0));
    }
  };

  const handleInrChange = (val: string) => {
    setInrAmount(val);
    const numeric = parseFloat(val);
    if (!isNaN(numeric)) {
      setUsdAmount((numeric / 83.5).toFixed(1));
    }
  };

  // Google Calendar Removal action
  const handleRemoveCalendarEvents = async () => {
    const success = await syncCalendar(activeTrip.id, { remove: true });
    if (success) {
      triggerToast("All trip events removed from Google Calendar", "info");
    }
  };

  // Export mock PDF guide
  const handleExportPDF = () => {
    triggerToast("Itinerary exported as PDF! Check downloads folder.", "success");
  };

  // Export mock ICS file
  const handleExportICS = () => {
    triggerToast("ICS Calendar Event File Downloaded!", "success");
  };

  const handleSaveOnly = (type: "Draft" | "Completed") => {
    saveTrip({
      ...activeTrip,
      status: type
    });
    setIsSaveOpen(false);
    triggerToast("Trip Saved Successfully!", "success");
  };

  const handleSaveAndSync = () => {
    saveTrip({
      ...activeTrip,
      status: "Upcoming"
    });
    setIsSaveOpen(false);
    setTimeout(() => {
      setIsSyncOpen(true);
    }, 300);
  };

  const handleRegenerateItinerary = (keeps: { budget: boolean; style: boolean; interests: boolean; duration: boolean }) => {
    const newTrip = generateNewMockTrip(activeTrip.cityName, activeTrip.durationDays);
    if (keeps.budget) newTrip.budget = activeTrip.budget;
    if (keeps.style) newTrip.travelStyle = activeTrip.travelStyle;
    newTrip.estimatedCost = activeTrip.estimatedCost;
    newTrip.startDate = activeTrip.startDate;
    newTrip.endDate = activeTrip.endDate;
    newTrip.hotels = activeTrip.hotels;
    newTrip.restaurants = activeTrip.restaurants;

    newTrip.historyTimeline = [
      { id: `hist-regen-${Date.now()}`, action: "🔄 Itinerary regenerated by AI core", timestamp: "Just now", iconName: "refresh-cw" },
      ...activeTrip.historyTimeline
    ];

    updateActiveTrip(() => newTrip);
    triggerToast("Itinerary Regenerated Successfully", "success");
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 relative bg-slate-50 dark:bg-[#0b0f19]">

      {/* Scrollable Workspace */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 pb-28 space-y-6">

        {/* ──────── 1. OFFLINE STATUS HEADER BAR ──────── */}
        {isOffline && (
          <div className="p-3 bg-amber-500 text-slate-950 rounded-2xl flex items-center justify-between text-xs font-bold shadow-md">
            <span className="flex items-center gap-1.5">
              <ShieldAlert className="w-4.5 h-4.5" />
              Offline Mode Active (Itinerary cached in local SQLite sync hubs)
            </span>
            <button
              onClick={() => setIsOffline(false)}
              className="px-3 py-1 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              Go Online
            </button>
          </div>
        )}

        {/* ──────── 2. TOP HERO STATS BLOCK ──────── */}
        <div className="relative rounded-3xl overflow-hidden border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#111827] shadow-sm text-left">
          {/* Banner Image */}
          <div className="h-44 sm:h-52 relative bg-slate-100 dark:bg-slate-800">
            <img
              src={activeTrip.bannerImage}
              alt={activeTrip.cityName}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />

            <div className="absolute bottom-4 left-5 text-white">
              <span className="text-[10px] font-extrabold text-teal-400 bg-teal-950/60 backdrop-blur-sm px-2.5 py-0.5 rounded border border-teal-500/20 uppercase tracking-widest inline-block mb-1">
                Active Itinerary
              </span>
              <h2 className="font-heading text-xl sm:text-2xl font-extrabold tracking-tight">
                Trip to {activeTrip.cityName}
              </h2>
              <p className="text-xs text-slate-250 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  {activeTrip.startDate} to {activeTrip.endDate}
                </span>
                <span>·</span>
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  {activeTrip.travelersCount} Guests
                </span>
                <span>·</span>
                <span className="font-bold text-teal-450 uppercase">{activeTrip.travelStyle} Style</span>
              </p>
            </div>

            <div className="absolute top-4 right-4 flex gap-2">
              <span className="px-3 py-1 bg-black/40 backdrop-blur-md text-[10px] font-bold text-white border border-white/10 rounded-full flex items-center gap-1">
                <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                {tempStr} Weather
              </span>
              <span className="px-3 py-1 bg-teal-500 text-slate-950 text-[10px] font-extrabold rounded-full shadow-sm">
                ₹{activeTrip.estimatedCost} Cost
              </span>
            </div>
          </div>

          {/* Stepper Progress bar */}
          <div className="p-4 bg-slate-50/50 dark:bg-slate-900/10 border-b border-slate-100 dark:border-slate-850">
            <div className="flex flex-wrap items-center justify-around gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              <div className="flex items-center gap-1 text-teal-600 dark:text-teal-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Destination</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isBudgetSet ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isBudgetSet ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Budget</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isTravelersSet ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isTravelersSet ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Travelers</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className="flex items-center gap-1 text-teal-600 dark:text-teal-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Interests</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isGenerated ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isGenerated ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Generated</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isSaved ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isSaved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Saved</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isSynced ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isSynced ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Synced</span>
              </div>
            </div>
          </div>

          {/* Quick Statistics badges */}
          <div className="p-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3.5 bg-white dark:bg-[#111827]">
            {[
              { label: "Rating", val: `⭐ ${avgRating}`, color: "text-amber-500" },
              { label: "Attractions", val: `📍 ${attractionsCount} Place${attractionsCount !== 1 ? 's' : ''}`, color: "text-sky-505 text-sky-600" },
              { label: "Restaurants", val: `🍽 ${restaurantsCount} Dining${restaurantsCount !== 1 ? 's' : ''}`, color: "text-rose-505 text-rose-600" },
              { label: "Hotels", val: `🏨 ${hotelsCount} Stay${hotelsCount !== 1 ? 's' : ''}`, color: "text-teal-505 text-teal-600" },
              { label: "Distance", val: `🚗 ${totalDistance} km`, color: "text-slate-600" },
              { label: "Est Budget", val: `💰 ₹${activeTrip.estimatedCost.toLocaleString('en-IN')}`, color: "text-emerald-600" },
              { label: "Active hours", val: `⏱ ${activeHours} Hours`, color: "text-purple-600" },
              { label: "Forecast", val: `🌤 ${tempStr}`, color: "text-amber-505 text-amber-600" }
            ].map((stat) => (
              <div key={stat.label} className="p-2 border border-slate-100 dark:border-slate-800/80 rounded-xl bg-slate-50/50 dark:bg-slate-900/10">
                <span className="block text-[9px] text-slate-400 font-bold uppercase">{stat.label}</span>
                <span className={`block text-xs font-extrabold mt-0.5 ${stat.color}`}>{stat.val}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ──────── 3. WORKSPACE TABS SELECTOR ──────── */}
        <div className="flex items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 overflow-x-auto no-scrollbar pb-px">
          {(["Overview", "Itinerary", "Hotels", "Restaurants", "Attractions", "Map", "Budget", "Notes", "Smart Assistant"] as const).map((tab) => {
            const active = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative px-4 py-2.5 text-xs font-bold transition-colors select-none flex-shrink-0 ${active ? "text-teal-655 text-teal-600 dark:text-teal-400" : "text-slate-455 text-slate-400 hover:text-slate-700 dark:hover:text-slate-350"
                  }`}
              >
                {active && (
                  <motion.div
                    layoutId="plannerTabGlow"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-600 dark:bg-teal-400"
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                  />
                )}
                {tab}
              </button>
            );
          })}
        </div>

        {/* ──────── 4. DYNAMIC TAB VIEW WORKSPACE PANELS ──────── */}
        <div className="min-h-[300px]">
          <AnimatePresence mode="wait">

            {/* TAB: OVERVIEW */}
            {activeTab === "Overview" && (
              <motion.div
                key="tab-overview"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left"
              >
                {/* Left Side: Summary and packing checklist */}
                <div className="md:col-span-2 space-y-6">

                  {/* Trip Summary Block */}
                  <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-3">
                    <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                      <BookOpen className="w-4.5 h-4.5 text-teal-600" />
                      Trip Summary
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-medium">
                      An immersive {activeTrip.durationDays}-day {activeTrip.travelStyle.toLowerCase()} experience in {activeTrip.cityName}, starting {activeTrip.startDate}. Includes {summaryHighlights}.{diningSummary}
                    </p>
                  </div>

                  {/* Packing Checklist */}
                  <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-3">
                    <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                      <CheckSquare className="w-4.5 h-4.5 text-teal-600" />
                      Packing Checklist
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {activeTrip.packingChecklist.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleToggleChecklist(item.id)}
                          className="flex items-center gap-2 p-2.5 border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-350 select-none text-left"
                        >
                          {item.checked ? (
                            <CheckSquare className="w-4 h-4 text-teal-600 flex-shrink-0" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          )}
                          <span className={item.checked ? "line-through text-slate-400 font-medium" : ""}>
                            {item.name}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Trip Audit Trail History Timeline */}
                  <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
                    <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                      <ActivityIcon className="w-4.5 h-4.5 text-teal-600" />
                      Trip History Event logs (Audit Trail)
                    </h3>
                    <div className="space-y-4 pl-2 relative border-l border-slate-100 dark:border-slate-800">
                      {activeTrip.historyTimeline.map((ev) => (
                        <div key={ev.id} className="relative pl-6">
                          {/* Dot indicator */}
                          <span className="absolute left-[-5px] top-1.5 w-2.5 h-2.5 rounded-full bg-teal-500 border border-white dark:border-[#111827]" />
                          <div className="text-xs">
                            <span className="font-bold text-slate-700 dark:text-slate-205">{ev.action}</span>
                            <span className="block text-[9.5px] text-slate-400 mt-0.5">{ev.timestamp}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>

                {/* Right Side: Widgets (Countdown, emergency list, weather converter) */}
                <div className="md:col-span-1 space-y-6">

                  {/* Trip Countdown Timer */}
                  {(() => {
                    const getCountdown = (startDateStr: string) => {
                      try {
                        const now = new Date();
                        const start = new Date(startDateStr);
                        const diffMs = start.getTime() - now.getTime();
                        if (diffMs <= 0) {
                          return { days: "00", hours: "00", minutes: "00" };
                        }
                        const totalMins = Math.floor(diffMs / 60000);
                        const mins = totalMins % 60;
                        const totalHours = Math.floor(totalMins / 60);
                        const hours = totalHours % 24;
                        const days = Math.floor(totalHours / 24);
                        
                        return {
                          days: days.toString().padStart(2, "0"),
                          hours: hours.toString().padStart(2, "0"),
                          minutes: mins.toString().padStart(2, "0")
                        };
                      } catch {
                        return { days: "00", hours: "00", minutes: "00" };
                      }
                    };
                    const countdown = getCountdown(activeTrip.startDate);
                    return (
                      <div className="p-4 bg-teal-650 bg-teal-600 text-white rounded-2xl shadow-sm text-center space-y-2">
                        <h4 className="text-[10px] font-extrabold uppercase tracking-widest text-teal-200">
                          Departure Countdown
                        </h4>
                        <div className="grid grid-cols-3 gap-1 py-1">
                          <div>
                            <span className="block text-lg font-black leading-none">{countdown.days}</span>
                            <span className="text-[8.5px] font-bold text-teal-200 uppercase">Days</span>
                          </div>
                          <div>
                            <span className="block text-lg font-black leading-none">{countdown.hours}</span>
                            <span className="text-[8.5px] font-bold text-teal-200 uppercase">Hours</span>
                          </div>
                          <div>
                            <span className="block text-lg font-black leading-none">{countdown.minutes}</span>
                            <span className="text-[8.5px] font-bold text-teal-200 uppercase">Mins</span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Currency Converter */}
                  <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-3">
                    <h4 className="font-heading text-xs font-bold text-slate-800 dark:text-slate-105 flex items-center gap-1">
                      <Wallet className="w-4 h-4 text-emerald-500" />
                      Currency Converter (USD to INR)
                    </h4>
                    <div className="space-y-2.5">
                      <div>
                        <span className="block text-[9.5px] font-bold text-slate-400 uppercase mb-1">USD ($)</span>
                        <input
                          type="number"
                          value={usdAmount}
                          onChange={(e) => handleUsdChange(e.target.value)}
                          className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-300 outline-none"
                        />
                      </div>
                      <div>
                        <span className="block text-[9.5px] font-bold text-slate-400 uppercase mb-1">INR (₹)</span>
                        <input
                          type="number"
                          value={inrAmount}
                          onChange={(e) => handleInrChange(e.target.value)}
                          className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-300 outline-none"
                        />
                      </div>
                      <p className="text-[9px] text-slate-400 italic">Conversion rate: 1 USD ≈ 83.5 INR</p>
                    </div>
                  </div>

                  {/* Emergency Contacts Directory */}
                  <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-3">
                    <h4 className="font-heading text-xs font-bold text-slate-800 dark:text-slate-105 flex items-center gap-1">
                      <PhoneCall className="w-4 h-4 text-rose-500 animate-pulse" />
                      Emergency Contacts
                    </h4>
                    <div className="space-y-2">
                      {activeTrip.emergencyContacts.map((contact) => (
                        <div key={contact.role} className="p-2 border border-slate-100 dark:border-slate-850 rounded-xl text-left text-xs bg-slate-50/50 dark:bg-slate-900/10">
                          <p className="font-bold text-slate-700 dark:text-slate-300 leading-none">{contact.role}</p>
                          <p className="text-teal-600 font-extrabold mt-1 text-[11px]">{contact.number}</p>
                          <p className="text-[9.5px] text-slate-400 truncate mt-0.5">{contact.location}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              </motion.div>
            )}

            {/* TAB: ITINERARY TIMELINE */}
            {activeTab === "Itinerary" && (
              <motion.div
                key="tab-itinerary"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-4xl mx-auto space-y-6"
              >
                <div className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm overflow-hidden">
                  <div className="flex items-center gap-1 overflow-x-auto p-2 border-b border-slate-100 dark:border-slate-850 no-scrollbar">
                    {itineraryDayEntries.map(([dayNum, list]) => {
                      const active = activeDayNum === dayNum;
                      return (
                        <button
                          key={dayNum}
                          onClick={() => setActiveItineraryDay(dayNum)}
                          className={`relative flex-shrink-0 px-4 py-2.5 text-xs font-bold transition-colors select-none rounded-xl ${
                            active
                              ? "bg-teal-600 text-white shadow-sm"
                              : "text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-200"
                          }`}
                        >
                          Day {dayNum}
                          <span className={`ml-2 text-[9px] font-extrabold ${active ? "text-teal-100" : "text-slate-400"}`}>
                            {list.length}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Day Header */}
                  <div className="flex items-center justify-between gap-3 p-4 text-left">
                    <div>
                      <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100">
                        Day {activeDayNum} Timeline
                      </h3>
                      <p className="text-[10px] text-slate-400 mt-0.5">Review, reorder, or edit this day's schedule</p>
                    </div>
                    <span className="px-3 py-1 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 text-[10px] font-extrabold rounded-lg border border-teal-100 dark:border-teal-900/30">
                      {activeDayActivities.length} Slots
                    </span>
                  </div>
                </div>

                {/* Active day activity list with drop zone mapping */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`day-${activeDayNum}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="space-y-4 pl-4 border-l-2 border-slate-200 dark:border-slate-800 min-h-[60px] transition-all duration-200"
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDropOnDay(e, activeDayNum)}
                  >
                    {activeDayActivities.map((act) => (
                      <div
                        key={act.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, activeDayNum, act.id)}
                        onDragEnd={handleDragEnd}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, activeDayNum, act.id)}
                        className={`cursor-grab active:cursor-grabbing transition-all duration-200 ${
                          draggedActivity?.id === act.id
                            ? "opacity-30 scale-95 border-2 border-dashed border-teal-500 dark:border-teal-400 rounded-2xl shadow-inner bg-teal-50/10"
                            : "hover:border-slate-300 dark:hover:border-slate-700"
                        }`}
                      >
                        <ActivityCard
                          activity={act}
                          onDelete={(id: string) => handleDeleteActivity(activeDayNum, id)}
                          onFavoriteToggle={(id: string) => handleFavoriteToggle(activeDayNum, id)}
                          onReplace={(id: string) => handleReplaceActivity(activeDayNum, id)}
                          onViewOnMap={handleViewOnMap}
                        />
                      </div>
                    ))}
                  </motion.div>
                </AnimatePresence>
              </motion.div>
            )}

            {/* TAB: HOTELS ACCOMMODATION */}
            {activeTab === "Hotels" && (
              <motion.div
                key="tab-hotels"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left"
              >
                {activeTrip.hotels.map((h, idx) => {
                  const isCurrent = idx === 0;
                  return (
                    <div key={h.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                      {/* Cover Photo */}
                      <div className="h-44 relative bg-slate-100 dark:bg-slate-800">
                        <img src={h.image} className="w-full h-full object-cover" alt="" />
                        {isCurrent && (
                          <span className="absolute top-3 left-3 bg-teal-600 text-white px-2.5 py-0.5 text-[9px] font-extrabold uppercase rounded-lg shadow">
                            Current Stay
                          </span>
                        )}
                        <span className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md text-[10px] font-bold text-white px-2 py-0.5 rounded">
                          ★ {h.rating.toFixed(1)}
                        </span>
                      </div>

                      <div className="p-5 space-y-4">
                        <div>
                          <h4 className="font-heading font-extrabold text-sm text-slate-805 dark:text-slate-100 truncate">
                            {h.name}
                          </h4>
                          <span className="text-[10px] text-slate-455 dark:text-slate-400 block mt-0.5">{h.distanceFromCenter}</span>
                        </div>

                        {/* Amenities lists */}
                        <div className="flex flex-wrap gap-1">
                          {h.amenities.map((item) => (
                            <span key={item} className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">
                              {item}
                            </span>
                          ))}
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-850 text-xs">
                          <div className="font-bold text-teal-700 dark:text-teal-400">
                            <span>₹{h.pricePerNight} </span>
                            <span className="text-[10px] text-slate-400 font-semibold">/ night</span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => {
                                setItemToAdd({
                                  type: "hotel",
                                  id: h.id,
                                  name: h.name,
                                  image: h.image,
                                  rating: h.rating,
                                  location: h.distanceFromCenter
                                });
                                setIsAddItineraryOpen(true);
                              }}
                              className="px-3 py-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded-xl text-[10.5px] font-bold hover-scale border border-teal-100 dark:border-teal-900/50"
                            >
                              Add to Itinerary
                            </button>
                            {!isCurrent && (
                              <button
                                onClick={() => handleSwapHotel(h.id)}
                                className="px-3 py-1.5 border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold hover-scale"
                              >
                                Swap Hotel Stay
                              </button>
                            )}
                            <a
                              href={h.bookingUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-750 text-white rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                            >
                              Book Resort
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </motion.div>
            )}

            {/* TAB: RESTAURANTS */}
            {activeTab === "Restaurants" && (
              <motion.div
                key="tab-restaurants"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left"
              >
                {activeTrip.restaurants.map((r) => (
                  <div key={r.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                    <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
                      <img src={r.image} className="w-full h-full object-cover" alt="" />
                      <span className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-md text-[9px] font-bold text-white px-2 py-0.5 rounded">
                        {r.cuisine}
                      </span>
                      <span className="absolute top-3 right-3 bg-black/60 backdrop-blur-md text-[10px] font-bold text-white px-2 py-0.5 rounded">
                        ★ {r.rating.toFixed(1)}
                      </span>
                    </div>

                    <div className="p-4 space-y-3">
                      <div>
                        <h4 className="font-heading font-bold text-xs sm:text-sm text-slate-800 dark:text-slate-100 truncate">
                          {r.name}
                        </h4>
                        <p className="text-[10px] text-slate-400 mt-0.5">Price range: {r.priceTier} · {r.distanceFromHotel} from hotel</p>
                      </div>

                      <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-850">
                        <span className="text-[9px] font-bold text-slate-450 dark:text-slate-500 uppercase">
                          {r.reservationAvailable ? "Tables Available" : "Walk-in Only"}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => {
                              setItemToAdd({
                                type: "restaurant",
                                id: r.id,
                                name: r.name,
                                image: r.image,
                                rating: r.rating,
                                location: `${r.cuisine} · ${r.distanceFromHotel} from hotel`
                              });
                              setIsAddItineraryOpen(true);
                            }}
                            className="px-3 py-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded-xl text-[10px] font-bold hover-scale border border-teal-100 dark:border-teal-900/50"
                          >
                            Add to Itinerary
                          </button>
                          {r.reservationAvailable && (
                            <button
                              onClick={() => handleReserveTable(r.name)}
                              className="px-3 py-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded-xl text-[10px] font-bold hover-scale"
                            >
                              Reserve Table
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}


{activeTab === "Attractions" && (
  <motion.div
    key="tab-attractions"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left"
  >
    {discoveredPlaces.length === 0 && (
      <p className="col-span-full text-sm text-slate-400">
        No attractions yet. Ask the AI Chat "places to visit in {activeTrip.cityName}".
      </p>
    )}

    {discoveredPlaces.map((p) => {
      const img = p.googlePhotoName
        ? `${import.meta.env.VITE_API_BASE_URL ?? ""}/place-photo?photo_name=${encodeURIComponent(p.googlePhotoName)}&maxwidth=600`
        : p.image;
      return (
        <div key={p.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
          <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
            {img ? (
              <img src={img} className="w-full h-full object-cover" alt={p.name} />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-500 text-[10px]">Photo unavailable</div>
            )}
            {p.rating != null && (
              <span className="absolute top-3 right-3 bg-black/60 text-[10px] font-bold text-white px-2 py-0.5 rounded">
                ★ {p.rating.toFixed(1)}
              </span>
            )}
          </div>

          <div className="p-4 space-y-3">
            <div>
              <h4 className="font-heading font-bold text-xs sm:text-sm text-slate-800 dark:text-slate-100 truncate">{p.name}</h4>
              {p.address && <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{p.address}</p>}
            </div>
            {p.description && (
              <p className="text-[10.5px] text-slate-500 dark:text-slate-400 line-clamp-2">{p.description}</p>
            )}

            <div className="flex items-center justify-end pt-1 border-t border-slate-100 dark:border-slate-850">
              {/* NOTE: no "Tables Available" / "Reserve Table" here (attractions) */}
              <button
                onClick={() => {
                  setItemToAdd({
                    type: "attraction",
                    id: p.id,
                    name: p.name,
                    image: img || "",
                    rating: p.rating ?? 4.5,
                    location: p.address || "",
                  });
                  setIsAddItineraryOpen(true);
                }}
                className="px-3 py-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded-xl text-[10px] font-bold border border-teal-100 dark:border-teal-900/50"
              >
                Add to Itinerary
              </button>
            </div>
          </div>
        </div>
      );
    })}
  </motion.div>
)}




            {/* TAB: MAP INTERACTIVE OVERLAYS */}
            {activeTab === "Map" && (
              <motion.div
                key="tab-map"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-4xl mx-auto space-y-4 text-left"
              >
                {/* Map Control Badge Bar */}
                <div className="p-3 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl flex flex-wrap gap-2 items-center justify-between text-xs">
                  <span className="font-bold text-slate-700 dark:text-slate-300">
                    Location: <span className="text-teal-600 dark:text-teal-400 font-extrabold">{mapSearchQuery || activeTrip.cityName}</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      onClick={() => setMapSearchQuery(activeTrip.cityName)}
                      className="px-3 py-1 rounded-lg border border-slate-150 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-[10px] font-bold text-slate-500 dark:text-slate-400 cursor-pointer hover:border-teal-500 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-all"
                    >
                      Center City
                    </button>
                    <button
                      onClick={() => setMapSearchQuery(`Hotels in ${activeTrip.cityName}`)}
                      className="px-3 py-1 rounded-lg border border-slate-150 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-[10px] font-bold text-slate-500 dark:text-slate-400 cursor-pointer hover:border-teal-500 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-all"
                    >
                      Show Stays
                    </button>
                    <button
                      onClick={() => setMapSearchQuery(`Restaurants in ${activeTrip.cityName}`)}
                      className="px-3 py-1 rounded-lg border border-slate-150 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-[10px] font-bold text-slate-500 dark:text-slate-400 cursor-pointer hover:border-teal-500 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-all"
                    >
                      Show Restaurants
                    </button>
                  </div>
                </div>

                <div className="h-[450px] relative rounded-3xl overflow-hidden border border-slate-205 dark:border-slate-805 bg-slate-100 dark:bg-slate-900 flex flex-col shadow-inner">
                  <iframe
                    title="Google Map Search"
                    width="100%"
                    height="100%"
                    style={{ border: 0 }}
                    loading="lazy"
                    allowFullScreen
                    src={`https://maps.google.com/maps?q=${encodeURIComponent(mapSearchQuery || activeTrip.cityName)}&t=&z=14&ie=UTF8&iwloc=&output=embed`}
                    className="w-full h-full rounded-3xl dark:invert dark:hue-rotate-180 dark:contrast-[0.9] dark:opacity-[0.85]"
                  />
                </div>
              </motion.div>
            )}

            {/* TAB: BUDGET DASHBOARD */}
            {activeTab === "Budget" && (
              <motion.div
                key="tab-budget"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="max-w-xl mx-auto p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-5 text-left"
              >
                <div>
                  <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                    <DollarSign className="w-4.5 h-4.5 text-emerald-500" />
                    Budget Dashboard Breakdown
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">Progress status based on Moderate Tier calculations.</p>
                </div>

                {/* Progress bars categories */}
                <div className="space-y-4 pt-1">
                  {[
                    { cat: "Hotel Accommodations", val: 4500, limit: 9000, color: "bg-teal-500" },
                    { cat: "Dining & Food", val: 1800, limit: 3000, color: "bg-rose-500" },
                    { cat: "Transport", val: 900, limit: 1500, color: "bg-blue-500" },
                    { cat: "Tickets", val: 250, limit: 800, color: "bg-purple-500" },
                    { cat: "Shopping", val: 1000, limit: 2500, color: "bg-amber-500" }
                  ].map((item) => {
                    const percentage = Math.min(100, (item.val / item.limit) * 100);
                    return (
                      <div key={item.cat} className="space-y-1">
                        <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                          <span>{item.cat}</span>
                          <span>₹{item.val} / ₹{item.limit}</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-105 bg-slate-100 dark:bg-slate-850 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${percentage}%` }}
                            className={`h-full ${item.color} rounded-full`}
                          />
                        </div>
                      </div>
                    );
                  })}

                  <hr className="border-slate-100 dark:border-slate-850" />

                  <div className="flex justify-between items-center text-xs font-extrabold pt-1">
                    <span className="text-slate-500 dark:text-slate-400">Total Estimated Expenses</span>
                    <span className="text-lg text-emerald-600 dark:text-emerald-450">₹8,450 INR</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB: NOTES (SQLITE SYNC) */}
            {activeTab === "Notes" && (
              <motion.div
                key="tab-notes"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-xl mx-auto p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4 text-left"
              >
                <div>
                  <h3 className="font-heading text-sm font-extrabold text-slate-805 dark:text-slate-100 flex items-center gap-1.5">
                    <FileText className="w-4.5 h-4.5 text-teal-600" />
                    Trip Personal Notes
                  </h3>
                  <p className="text-[10.5px] text-slate-450 dark:text-slate-500 mt-0.5">
                    Write important numbers, flight check-ins, or requests. Auto-synchronized offline with local database storage.
                  </p>
                </div>

                <div className="relative">
                  <textarea
                    rows={6}
                    value={activeTrip.notesText}
                    onChange={(e) => handleUpdateNotesText(e.target.value)}
                    className="w-full p-3.5 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-slate-50/50 dark:bg-slate-900/10 text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500 resize-none font-medium leading-relaxed"
                    placeholder="Enter itinerary details, co-traveler contact directories, airport locations..."
                  />
                  <div className="absolute bottom-2.5 right-3 text-[9px] text-slate-450 font-bold bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-205 dark:border-slate-750">
                    Synced with SQLite
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB: SMART ASSISTANT */}
            {activeTab === "Smart Assistant" && (
              <motion.div
                key="tab-smart-assistant"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-3xl mx-auto space-y-6 text-left"
              >
                {/* Header panel details */}
                <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                      <Bell className="w-4.5 h-4.5 text-teal-600 animate-bounce" />
                      AI Travel Companion Speech & Alerts
                    </h3>
                    <p className="text-[10.5px] text-slate-400 dark:text-slate-500 mt-0.5 leading-relaxed">
                      Proactive screen alerts and natural-sounding speech notifications aligned with your itinerary and Google Calendar events.
                    </p>
                  </div>
                  
                  {/* Speech playback controls */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={() => VoiceNotificationService.getInstance().pause()}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[10px] font-bold bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-300"
                    >
                      Pause
                    </button>
                    <button
                      onClick={() => VoiceNotificationService.getInstance().resume()}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[10px] font-bold bg-white dark:bg-[#1f2937] hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-300"
                    >
                      Resume
                    </button>
                    <button
                      onClick={() => {
                        VoiceNotificationService.getInstance().stop();
                        triggerToast("Speech queue cleared");
                      }}
                      className="px-2.5 py-1.5 rounded-lg border border-red-200 dark:border-red-950/20 text-red-500 bg-red-50/20 hover:bg-red-50 text-[10px] font-bold transition-colors"
                    >
                      Stop
                    </button>
                  </div>
                </div>

                {/* Realtime Monitor Status */}
                <div className="p-4 bg-teal-50/30 dark:bg-teal-950/10 border border-teal-100/60 dark:border-teal-900/30 rounded-2xl text-left">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <h4 className="text-xs font-bold text-teal-700 dark:text-teal-400 flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5" />
                        Realtime Alert Monitor
                      </h4>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                        Alerts now activate automatically from itinerary event times while this planner is open.
                      </p>
                    </div>
                    <span className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-[#1f2937] border border-teal-100 dark:border-teal-900/40 text-[10px] font-extrabold text-teal-700 dark:text-teal-400">
                      <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
                      Live checks every 30s
                    </span>
                  </div>

                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px]">
                    <div className="p-2.5 rounded-xl bg-white/70 dark:bg-[#111827]/70 border border-slate-100 dark:border-slate-800">
                      <span className="block font-bold text-slate-400 uppercase">Source</span>
                      <span className="font-extrabold text-slate-700 dark:text-slate-300">AI + itinerary times</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white/70 dark:bg-[#111827]/70 border border-slate-100 dark:border-slate-800">
                      <span className="block font-bold text-slate-400 uppercase">Active Voice</span>
                      <span className="font-extrabold text-slate-700 dark:text-slate-300">Browser speech</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white/70 dark:bg-[#111827]/70 border border-slate-100 dark:border-slate-800">
                      <span className="block font-bold text-slate-400 uppercase">Next Alert</span>
                      <span className="font-extrabold text-slate-700 dark:text-slate-300">
                        {nextRealtimeNotification?.title || "No pending timed alert"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Notifications Lists Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {/* COLUMN 1: Today's Active Alerts */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between px-1">
                      <h4 className="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Today's Active
                      </h4>
                      <span className="text-[10px] font-bold bg-rose-50 dark:bg-rose-950/20 text-rose-600 px-2 py-0.5 rounded-full">
                        {notifications.filter(n => n.status === "active" || (n.status === "pending" && n.priority === "critical")).length}
                      </span>
                    </div>
                    <div className="space-y-2.5">
                      {notifications.filter(n => n.status === "active" || (n.status === "pending" && n.priority === "critical")).map((notif) => (
                        <NotificationCard key={notif.id} notif={notif} onPlay={handlePlayVoice} onMarkHeard={handleMarkHeard} />
                      ))}
                      {notifications.filter(n => n.status === "active" || (n.status === "pending" && n.priority === "critical")).length === 0 && (
                        <div className="p-5 text-center border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-[11px] text-slate-400 bg-white dark:bg-[#111827]">
                          No active notifications.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* COLUMN 2: Upcoming Alerts */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between px-1">
                      <h4 className="text-xs font-bold text-slate-700 dark:text-slate-350 flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        Upcoming
                      </h4>
                      <span className="text-[10px] font-bold bg-slate-100 dark:bg-slate-850 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded-full">
                        {notifications.filter(n => n.status === "pending" && n.priority !== "critical").length}
                      </span>
                    </div>
                    <div className="space-y-2.5">
                      {notifications.filter(n => n.status === "pending" && n.priority !== "critical").map((notif) => (
                        <NotificationCard key={notif.id} notif={notif} onPlay={handlePlayVoice} onMarkHeard={handleMarkHeard} />
                      ))}
                      {notifications.filter(n => n.status === "pending" && n.priority !== "critical").length === 0 && (
                        <div className="p-5 text-center border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-[11px] text-slate-400 bg-white dark:bg-[#111827]">
                          No upcoming notifications.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* COLUMN 3: Completed / Spoken History */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between px-1">
                      <h4 className="text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Completed History
                      </h4>
                      <span className="text-[10px] font-bold bg-teal-50 dark:bg-teal-950/20 text-teal-605 px-2 py-0.5 rounded-full">
                        {notifications.filter(n => n.status === "spoken" || n.spoken || n.status === "expired").length}
                      </span>
                    </div>
                    <div className="space-y-2.5">
                      {notifications.filter(n => n.status === "spoken" || n.spoken || n.status === "expired").map((notif) => (
                        <NotificationCard key={notif.id} notif={notif} onPlay={handlePlayVoice} onMarkHeard={handleMarkHeard} />
                      ))}
                      {notifications.filter(n => n.status === "spoken" || n.spoken || n.status === "expired").length === 0 && (
                        <div className="p-5 text-center border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-[11px] text-slate-400 bg-white dark:bg-[#111827]">
                          Announcements history empty.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>

      </div>

      {/* ──────── 5. STICKY ACTION CONTROL BAR ──────── */}
      {activeTab === "Itinerary" && (
        <div className="fixed bottom-16 sm:bottom-0 left-0 right-0 sm:left-20 lg:left-68 bg-white/95 dark:bg-[#111827]/95 backdrop-blur-md border-t border-slate-200/60 dark:border-slate-800/60 p-4 flex items-center justify-between sm:justify-around px-5 z-40">

          {/* Sync calendar connected summary */}
          <div className="hidden lg:block text-left">
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              {activeTrip.calendarSynced ? "✔ Calendar Connected" : "Calendar Pending"}
            </p>
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mt-0.5">
              {activeTrip.calendarSynced ? `Last Synced: ${activeTrip.calendarSyncedAt}` : `Sync calendar slots`}
            </h4>
          </div>

          {/* Action strip buttons */}
          <div className="flex items-center gap-1.5 sm:gap-2.5 overflow-x-auto no-scrollbar w-full sm:w-auto">
            {/* Modify button */}
            <button
              onClick={() => setIsModifyOpen(true)}
              className="flex-1 sm:flex-initial px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
            >
              <Edit3 className="w-4 h-4 text-teal-605" />
              <span>Modify</span>
            </button>

            {/* Regenerate */}
            <button
              onClick={() => setIsRegenOpen(true)}
              className="flex-1 sm:flex-initial px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-850 text-slate-700 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
            >
              <RefreshCw className="w-4 h-4 text-teal-605" />
              <span>Regenerate</span>
            </button>

            {/* Google Calendar sync/unsync buttons */}
            {activeTrip.calendarSynced ? (
              <button
                onClick={handleRemoveCalendarEvents}
                className="px-3.5 py-2.5 rounded-xl border border-rose-200 dark:border-rose-950/20 text-rose-605 bg-rose-50/20 hover:bg-rose-50 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
              >
                <Calendar className="w-4 h-4 text-rose-500" />
                <span>Unsync</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  setIsSaveOpen(false);
                  setIsSyncOpen(true);
                }}
                className="px-3.5 py-2.5 rounded-xl border border-slate-205 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
              >
                <Calendar className="w-4 h-4 text-teal-600" />
                <span>Calendar</span>
              </button>
            )}

            {/* Share */}
            <button
              onClick={() => setIsShareOpen(true)}
              className="px-3.5 py-2.5 rounded-xl border border-slate-205 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
            >
              <Share2 className="w-4 h-4 text-slate-450" />
              <span className="hidden sm:inline">Share</span>
            </button>
          </div>

        </div>
      )}

      {/* ──────── 6. FLOATING AI ASSISTANT FAB BUTTON ──────── */}
      <div className="fixed bottom-24 right-5 sm:right-6 z-45">
        <button
          onClick={() => setIsCopilotOpen(true)}
          className="flex items-center gap-2 px-4.5 py-3 rounded-full bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-950 text-xs font-heading font-extrabold shadow-xl hover-scale group"
        >
          <Sparkles className="w-4.5 h-4.5 text-teal-400 dark:text-teal-600 animate-pulse group-hover:scale-110 transition-transform" />
          <span>✨ Ask AI</span>
        </button>
      </div>

      {/* ──────── DRAWERS, DIALOGS, COPILOTS WORKSPACE MOUNT ──────── */}
      <ModifyDrawer
        isOpen={isModifyOpen}
        onClose={() => setIsModifyOpen(false)}
        onSaveSuccess={() => triggerToast("Itinerary updated successfully", "success")}
      />

      <SaveDialog
        isOpen={isSaveOpen}
        onClose={() => setIsSaveOpen(false)}
        onSaveOnly={handleSaveOnly}
        onSaveAndSync={handleSaveAndSync}
        onDownloadPDF={handleExportPDF}
        onExportICS={handleExportICS}
      />

      <CalendarSyncDialog
        isOpen={isSyncOpen}
        onClose={() => setIsSyncOpen(false)}
        tripName={activeTrip.cityName}
      />

      <RegenerateDialog
        isOpen={isRegenOpen}
        onClose={() => setIsRegenOpen(false)}
        onRegenerate={handleRegenerateItinerary}
      />

      <ShareDialog
        isOpen={isShareOpen}
        onClose={() => setIsShareOpen(false)}
        tripName={activeTrip.cityName}
      />

      <FloatingAICopilot
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        onApplySuccess={(title) => triggerToast(`Copilot applied: ${title}`, "success")}
      />

      <AddToItineraryDialog
        isOpen={isAddItineraryOpen}
        onClose={() => setIsAddItineraryOpen(false)}
        item={itemToAdd}
        durationDays={activeTrip.durationDays}
        onAdd={handleAddItemToItinerary}
      />

      {/* ──────── TOAST NOTIFICATIONS ──────── */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-55 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-xs font-bold text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 border-slate-850 dark:border-slate-200/50"
          >
            {toastType === "success" && <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500" />}
            {toastType === "info" && <AlertCircle className="w-4.5 h-4.5 text-sky-505 text-sky-600" />}
            {toastType === "error" && <AlertTriangle className="w-4.5 h-4.5 text-rose-500 animate-bounce" />}
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
export default TripPlanner;

const NotificationCard: React.FC<{
  notif: any;
  onPlay: (n: any) => void;
  onMarkHeard: (n: any) => void;
}> = ({ notif, onPlay, onMarkHeard }) => {
  const getPriorityBadge = (p: string) => {
    switch (p) {
      case "critical":
        return <span className="inline-flex items-center gap-1 text-[9px] font-bold text-rose-600 dark:text-rose-455 bg-rose-50/50 dark:bg-rose-950/20 px-2 py-0.5 rounded border border-rose-100/50 dark:border-rose-900/30">🔴 Critical</span>;
      case "high":
        return <span className="inline-flex items-center gap-1 text-[9px] font-bold text-orange-600 bg-orange-50/50 dark:bg-orange-950/20 px-2 py-0.5 rounded border border-orange-100/50 dark:border-orange-900/30">🟠 High</span>;
      case "medium":
        return <span className="inline-flex items-center gap-1 text-[9px] font-bold text-teal-650 dark:text-teal-400 bg-teal-50/50 dark:bg-teal-950/20 px-2 py-0.5 rounded border border-teal-100/50 dark:border-teal-900/30">🔵 Medium</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[9px] font-bold text-slate-500 bg-slate-50 dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200/50 dark:border-slate-800">⚪ Low</span>;
    }
  };

  const getSourceLabel = (s: string) => {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : "Trip";
  };

  return (
    <div className="p-3.5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-xl hover:border-slate-350 dark:hover:border-slate-700 shadow-sm transition-all duration-200 space-y-2.5 relative group text-left w-full">
      <div className="flex items-center justify-between gap-1.5 flex-wrap">
        <div className="flex items-center gap-1.5">
          {getPriorityBadge(notif.priority)}
          <span className="text-[8px] uppercase tracking-wider font-extrabold text-slate-400 border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 px-1.5 py-0.5 rounded">
            {getSourceLabel(notif.source)}
          </span>
        </div>
        {notif.event_time && (
          <span className="text-[9px] font-bold text-slate-400 dark:text-slate-550">
            {new Date(notif.event_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      <div>
        <h5 className="text-xs font-extrabold text-slate-800 dark:text-slate-200 leading-snug">
          {notif.title}
        </h5>
        <p className="text-[10.5px] text-slate-550 dark:text-slate-400 leading-relaxed mt-0.5">
          {notif.text}
        </p>
      </div>

      <div className="flex items-center justify-end gap-1.5 pt-1.5 border-t border-slate-50 dark:border-slate-850/60">
        {!notif.spoken && notif.status !== "expired" && (
          <button
            onClick={() => onMarkHeard(notif)}
            className="px-2 py-1 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-650 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 text-[9px] font-bold transition-colors"
          >
            Mark Heard
          </button>
        )}
        <button
          onClick={() => onPlay(notif)}
          className="px-2 py-1 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-[9px] font-bold flex items-center gap-1 transition-colors"
        >
          <Volume2 className="w-3 h-3" />
          <span>{notif.spoken ? "Replay" : "Play Voice"}</span>
        </button>
      </div>
    </div>
  );
};
