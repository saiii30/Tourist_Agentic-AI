import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

export interface Activity {
  id: string;
  title: string;
  time: string;
  duration: string;
  category: "Sightseeing" | "Food" | "Adventure" | "Culture" | "Relaxation";
  rating: number;
  entryFee: string;
  description: string;
  location: string;
  image: string;
  isFavorite?: boolean;
  slot?: "Breakfast" | "Morning Activity" | "Lunch" | "Afternoon Activity" | "Evening Activity" | "Dinner" | "Hotel";
}

export interface HotelDetails {
  id: string;
  name: string;
  image: string;
  rating: number;
  pricePerNight: number;
  amenities: string[];
  distanceFromCenter: string;
  bookingUrl: string;
}

export interface RestaurantDetails {
  id: string;
  name: string;
  image: string;
  rating: number;
  cuisine: string;
  priceTier: "$$" | "$$$" | "$$$$";
  distanceFromHotel: string;
  reservationAvailable: boolean;
}

export interface EmergencyContact {
  role: string;
  number: string;
  location: string;
}

export interface PackingItem {
  id: string;
  name: string;
  checked: boolean;
}

export interface ExpenseItem {
  id: string;
  category: "Hotel" | "Food" | "Transport" | "Tickets" | "Shopping" | "Misc";
  amount: number;
  label: string;
}

export interface HistoryEvent {
  id: string;
  action: string;
  timestamp: string;
  iconName: string;
}

export interface TripDetails {
  id: string;
  cityName: string;
  bannerImage: string;
  startDate: string;
  endDate: string;
  durationDays: number;
  travelersCount: number;
  budget: "Budget" | "Moderate" | "Luxury";
  travelStyle: "Adventure" | "Relaxed" | "Cultural" | "Family";
  weatherSummary: string;
  estimatedCost: number;
  packingTips: string[];
  itinerary: Record<number, Activity[]>;
  status: "Upcoming" | "Draft" | "Completed" | "Cancelled" | "Archived";
  calendarSynced: boolean;
  calendarSyncedAt?: string;
  calendarEventsCount?: number;

  // Premium smart features properties
  isFavorite: boolean;
  hotels: HotelDetails[];
  restaurants: RestaurantDetails[];
  expenses: ExpenseItem[];
  packingChecklist: PackingItem[];
  emergencyContacts: EmergencyContact[];
  notesText: string;
  historyTimeline: HistoryEvent[];
}

export interface Message {
  role: "user" | "assistant";
  text: string;
  routes?: string[];
  tripCard?: TripDetails;
  timestamp: string;
}

interface TravelPlannerContextType {
  theme: "light" | "dark";
  toggleTheme: () => void;
  chatMessages: Message[];
  setChatMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isLoadingChat: boolean;
  setIsLoadingChat: (val: boolean) => void;
  activeTrip: TripDetails | null;
  setActiveTrip: (trip: TripDetails | null) => void;
  savedTrips: TripDetails[];
  saveTrip: (trip: TripDetails) => void;
  deleteTrip: (id: string) => void;
  duplicateTrip: (id: string) => void;
  updateActiveTrip: (updater: (prev: TripDetails | null) => TripDetails | null) => void;
  isSyncingCalendar: boolean;
  syncCalendar: (tripId: string, options?: { remove?: boolean }) => Promise<boolean>;
  askAIChat: (question: string) => Promise<void>;
  generateNewMockTrip: (city: string, days?: number) => TripDetails;
}

const TravelPlannerContext = createContext<TravelPlannerContextType | undefined>(undefined);

// Helper to push history timeline audits
const appendHistoryEvent = (history: HistoryEvent[], action: string, iconName = "sparkles"): HistoryEvent[] => {
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return [
    {
      id: `history-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      action,
      timestamp: `Today ${timeStr}`,
      iconName
    },
    ...history
  ];
};

// High-Fidelity Mock Trip Generator for fallback
const generateMockTripDetails = (city: string, daysCount = 3): TripDetails => {
  const normCity = city.charAt(0).toUpperCase() + city.slice(1);
  
  // Try to use a nice generic city-themed Unsplash image if it matches known patterns, otherwise standard travel banner
  let banner = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80";
  const cityLower = city.toLowerCase();
  if (cityLower.includes("madurai")) {
    banner = "https://images.unsplash.com/photo-1600100397608-f010e423b971?auto=format&fit=crop&w=1200&q=80";
  } else if (cityLower.includes("goa")) {
    banner = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80";
  } else if (cityLower.includes("chennai")) {
    banner = "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80";
  } else if (cityLower.includes("ooty")) {
    banner = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80";
  }

  const itinerary: Record<number, Activity[]> = {};

  // Generic trip template inserting city name dynamically
  const slotPools: Record<string, Omit<Activity, "id" | "slot">[]> = {
    "Breakfast": [
      {
        title: `Breakfast in ${normCity}`,
        time: "08:30 AM",
        duration: "1 hour",
        category: "Food",
        rating: 4.5,
        entryFee: "Free entry",
        description: `Start your day with a fresh breakfast at a recommended cafe in ${normCity}. Try their local specialties.`,
        location: `Local Cafe in ${normCity}`,
        image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Morning Activity": [
      {
        title: `Explore popular attractions in ${normCity}`,
        time: "09:30 AM",
        duration: "2.5 hours",
        category: "Sightseeing",
        rating: 4.5,
        entryFee: "Standard fees",
        description: `Visit the key cultural or natural sightseeing spots of ${normCity}. Ideal for sightseeing and photographs.`,
        location: `Popular Sights in ${normCity}`,
        image: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Lunch": [
      {
        title: `Lunch at local restaurant in ${normCity}`,
        time: "01:00 PM",
        duration: "1.5 hours",
        category: "Food",
        rating: 4.5,
        entryFee: "Standard pricing",
        description: `Enjoy a delicious lunch featuring authentic local cuisine of ${normCity}.`,
        location: `Recommended Eatery in ${normCity}`,
        image: "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Afternoon Activity": [
      {
        title: `Afternoon relaxation & stroll in ${normCity}`,
        time: "03:00 PM",
        duration: "2 hours",
        category: "Relaxation",
        rating: 4.5,
        entryFee: "Free",
        description: `Relax and take a gentle stroll around the local parks or prominent quarters of ${normCity}.`,
        location: `Scenic Area in ${normCity}`,
        image: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Evening Activity": [
      {
        title: `Evening market walk in ${normCity}`,
        time: "05:30 PM",
        duration: "1.5 hours",
        category: "Sightseeing",
        rating: 4.5,
        entryFee: "Free",
        description: `Walk through the local markets of ${normCity} to browse and discover local handicrafts.`,
        location: `Market Area in ${normCity}`,
        image: "https://images.unsplash.com/photo-1472214222541-d510753a4907?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Dinner": [
      {
        title: `Dinner in ${normCity}`,
        time: "07:30 PM",
        duration: "2 hours",
        category: "Food",
        rating: 4.5,
        entryFee: "Standard pricing",
        description: `Indulge in a relaxing dinner at a highly rated local restaurant in ${normCity}.`,
        location: `Dinner Spot in ${normCity}`,
        image: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=400&q=80"
      }
    ],
    "Hotel": [
      {
        title: `Overnight Stay: Cozy Hotel in ${normCity}`,
        time: "09:30 PM",
        duration: "Overnight",
        category: "Relaxation",
        rating: 4.5,
        entryFee: "Included",
        description: `Unwind and relax at your hotel or local homestay in ${normCity}.`,
        location: `Comfortable Stay in ${normCity}`,
        image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=400&q=80"
      }
    ]
  };

  const slots = [
    "Breakfast",
    "Morning Activity",
    "Lunch",
    "Afternoon Activity",
    "Evening Activity",
    "Dinner",
    "Hotel"
  ] as const;

  for (let d = 1; d <= daysCount; d++) {
    const dailyActs: Activity[] = [];
    slots.forEach((s) => {
      const pool = slotPools[s];
      const baseAct = pool[0];
      dailyActs.push({
        ...baseAct,
        id: `day-${d}-${s.replace(/\s+/g, "-").toLowerCase()}-${Math.random().toString(36).substr(2, 4)}`,
        slot: s,
        title: `${baseAct.title} (Day ${d})`
      });
    });
    itinerary[d] = dailyActs;
  }

  // Generic packing list items
  const packingChecklist: PackingItem[] = [
    { id: "pack-1", name: "Travel ID proof & tickets", checked: true },
    { id: "pack-2", name: "Comfortable footwear & clothing", checked: false },
    { id: "pack-3", name: "Mobile charger & Power bank", checked: false },
    { id: "pack-4", name: "Basic medical essentials", checked: false }
  ];

  // Generic emergency numbers
  const emergencyContacts: EmergencyContact[] = [
    { role: "National Helpline", number: "112", location: "Toll-free emergency help" },
    { role: "Police", number: "100", location: "Local Police Station" },
    { role: "Medical Services", number: "108", location: "Nearest Hospital Support" }
  ];

  // Audit history
  const historyTimeline: HistoryEvent[] = [
    { id: "hist-1", action: `Offline Itinerary generated for ${normCity}`, timestamp: "Just now", iconName: "sparkles" }
  ];

  return {
    id: `trip-offline-${Date.now()}`,
    cityName: normCity,
    bannerImage: banner,
    startDate: new Date(Date.now() + 86400000 * 7).toISOString().split("T")[0],
    endDate: new Date(Date.now() + 86400000 * (7 + daysCount)).toISOString().split("T")[0],
    durationDays: daysCount,
    travelersCount: 1,
    budget: "Moderate",
    travelStyle: "Cultural",
    weatherSummary: `Weather forecast for ${normCity}`,
    estimatedCost: 0,
    packingTips: [
      "Keep standard travel documentation safe.",
      "Check climate reports for appropriate clothing.",
      "Ensure basic medical kit is packed."
    ],
    itinerary,
    status: "Draft",
    calendarSynced: false,
    isFavorite: false,
    hotels: [],
    restaurants: [],
    expenses: [],
    packingChecklist,
    emergencyContacts,
    notesText: `Notes for trip to ${normCity}. (Note: Currently running in Offline Mode)`,
    historyTimeline
  };
};

export const TravelPlannerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Theme state
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const saved = localStorage.getItem("theme");
    return (saved as "light" | "dark") || "light";
  });

  // Chat message state
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [isLoadingChat, setIsLoadingChat] = useState<boolean>(false);

  // Active Trip Planner states
  const [activeTrip, setActiveTrip] = useState<TripDetails | null>(null);

  // Saved Trips state
  const [savedTrips, setSavedTrips] = useState<TripDetails[]>(() => {
    const saved = localStorage.getItem("savedTrips");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return [];
      }
    }
    return [];
  });

  // Calendar synchronization state
  const [isSyncingCalendar, setIsSyncingCalendar] = useState<boolean>(false);

  // Synchronize CSS class for dark mode
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Synchronize localStorage for saved trips
  useEffect(() => {
    localStorage.setItem("savedTrips", JSON.stringify(savedTrips));
  }, [savedTrips]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const saveTrip = (trip: TripDetails) => {
    setSavedTrips((prev) => {
      const idx = prev.findIndex((t) => t.id === trip.id);
      const updatedTrip = {
        ...trip,
        historyTimeline: appendHistoryEvent(trip.historyTimeline, "Trip Saved to Collections", "save")
      };

      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = updatedTrip;
        return updated;
      }
      return [...prev, updatedTrip];
    });

    // Keep active trip synced as well
    if (activeTrip && activeTrip.id === trip.id) {
      setActiveTrip((prev) => prev ? { ...prev, historyTimeline: appendHistoryEvent(prev.historyTimeline, "Trip Saved to Collections", "save") } : null);
    }
  };

  const deleteTrip = (id: string) => {
    setSavedTrips((prev) => prev.filter((t) => t.id !== id));
    if (activeTrip && activeTrip.id === id) {
      setActiveTrip(null);
    }
  };

  const duplicateTrip = (id: string) => {
    const target = savedTrips.find((t) => t.id === id);
    if (target) {
      const copy: TripDetails = {
        ...JSON.parse(JSON.stringify(target)),
        id: `trip-copy-${Date.now()}`,
        cityName: `${target.cityName} (Copy)`,
        calendarSynced: false,
        status: "Draft"
      };
      copy.historyTimeline = appendHistoryEvent(copy.historyTimeline, "Trip Cloned & Duplicated", "copy");
      setSavedTrips((prev) => [...prev, copy]);
    }
  };

  const updateActiveTrip = (updater: (prev: TripDetails | null) => TripDetails | null) => {
    setActiveTrip((prev) => {
      const next = updater(prev);
      if (next && savedTrips.some((t) => t.id === next.id)) {
        setSavedTrips((st) => st.map((t) => (t.id === next.id ? next : t)));
      }
      return next;
    });
  };

  const syncCalendar = async (tripId: string, options?: { remove?: boolean }): Promise<boolean> => {
    setIsSyncingCalendar(true);

    const targetTrip = savedTrips.find((t) => t.id === tripId) || activeTrip;

    if (targetTrip) {
      const isRemoval = !!options?.remove;
      const historyMsg = isRemoval ? "Google Calendar Events Removed" : "Google Calendar Synchronized";
      const countVal = isRemoval ? 0 : 7 * targetTrip.durationDays;

      // Format itinerary to markdown
      let itineraryMarkdown = "";
      Object.entries(targetTrip.itinerary).forEach(([dayNum, activities]) => {
        itineraryMarkdown += `### Day ${dayNum}\n`;
        activities.forEach((act) => {
          itineraryMarkdown += `- **${act.time}** [${act.slot}] ${act.title}: ${act.description}\n`;
        });
      });

      // Save itinerary to SQLite database via backend
      const tripName = targetTrip.cityName + " Itinerary";
      try {
        await axios.post("http://localhost:8000/calendar/save", {
          itinerary_text: itineraryMarkdown,
          trip_name: tripName
        });
      } catch (err) {
        console.warn("Backend save failed, syncing offline:", err);
      }

      // Trigger Google OAuth popup if syncing (not removing)
      if (!isRemoval) {
        const width = 600, height = 655;
        const left = window.innerWidth / 2 - width / 2;
        const top = window.innerHeight / 2 - height / 2;
        window.open(
          `http://localhost:8000/login/google?trip_id=${targetTrip.id}`,
          "Google Calendar Sync",
          `width=${width},height=${height},top=${top},left=${left}`
        );
      }

      setSavedTrips((prev) =>
        prev.map((t) =>
          t.id === tripId
            ? {
              ...t,
              calendarSynced: !isRemoval,
              calendarEventsCount: countVal,
              calendarSyncedAt: isRemoval ? undefined : "Today 10:30 AM",
              historyTimeline: appendHistoryEvent(t.historyTimeline, historyMsg, "calendar")
            }
            : t
        )
      );

      if (activeTrip && activeTrip.id === tripId) {
        setActiveTrip((prev) =>
          prev
            ? {
              ...prev,
              calendarSynced: !isRemoval,
              calendarEventsCount: countVal,
              calendarSyncedAt: isRemoval ? undefined : "Today 10:30 AM",
              historyTimeline: appendHistoryEvent(prev.historyTimeline, historyMsg, "calendar")
            }
            : null
        );
      }
    }

    setIsSyncingCalendar(false);
    return true;
  };

  const askAIChat = async (question: string) => {
    if (!question.trim()) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setChatMessages((prev) => [...prev, { role: "user", text: question, timestamp: timeStr }]);
    setIsLoadingChat(true);

    try {
      const res = await axios.post("http://localhost:8000/chat", { question });
      const answerText = res.data.answer;
      const routes = res.data.routes || [];

      let tripCard: TripDetails | undefined = undefined;
      const tripData = res.data.trip;
      if (tripData) {
        let banner = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80";
        const cityLower = tripData.city.toLowerCase();
        if (cityLower.includes("madurai")) {
          banner = "https://images.unsplash.com/photo-1600100397608-f010e423b971?auto=format&fit=crop&w=1200&q=80";
        } else if (cityLower.includes("goa")) {
          banner = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80";
        } else if (cityLower.includes("chennai")) {
          banner = "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80";
        } else if (cityLower.includes("ooty")) {
          banner = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80";
        }

        tripCard = {
          id: tripData.trip_id || `trip-real-${Date.now()}`,
          cityName: tripData.city,
          bannerImage: banner,
          startDate: new Date(Date.now() + 86400000 * 7).toISOString().split("T")[0],
          endDate: new Date(Date.now() + 86400000 * (7 + tripData.duration)).toISOString().split("T")[0],
          durationDays: tripData.duration,
          travelersCount: tripData.travelers || 1,
          budget: tripData.budget || "Moderate",
          travelStyle: tripData.travel_style || "Cultural",
          weatherSummary: tripData.weather_summary || "Weather Info from AI",
          estimatedCost: tripData.budget_summary?.estimated_cost || 0,
          packingTips: tripData.packing || [],
          itinerary: tripData.itinerary || {},
          status: "Draft",
          calendarSynced: tripData.calendar?.synced || false,
          isFavorite: false,
          hotels: tripData.hotels || [],
          restaurants: tripData.restaurants || [],
          expenses: tripData.budget_summary?.expenses || [],
          packingChecklist: tripData.packing_checklist || [],
          emergencyContacts: tripData.emergency || [],
          notesText: `Notes for trip to ${tripData.city}. Budget level: ${tripData.budget}.`,
          historyTimeline: [
            {
              id: `hist-real-${Date.now()}`,
              action: `Live Itinerary generated via ${res.data.metadata?.source || "AI"}`,
              timestamp: "Just now",
              iconName: "sparkles"
            }
          ]
        };
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: answerText, routes, tripCard, timestamp: timeStr }
      ]);
    } catch (err) {
      console.warn("Backend API not reachable, running in Offline Mode:", err);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      let detectedCity = "Madurai";
      const words = question.split(/\s+/);
      const cities = ["madurai", "chennai", "goa", "tokyo", "paris", "delhi", "agra", "mumbai", "ooty"];
      for (const w of words) {
        const cleanW = w.toLowerCase().replace(/[^a-z]/g, "");
        if (cities.includes(cleanW)) {
          detectedCity = cleanW;
          break;
        }
      }

      const tripCard = generateMockTripDetails(detectedCity);
      tripCard.status = "Draft";

      const answerText = `⚠️ **Offline Mode Active**\n\nI couldn't reach the AI Travel Agent backend server. I have created a dynamic template itinerary card for **${tripCard.cityName}** in offline mode. No real hotels or restaurants are displayed.`;
      
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: answerText, routes: ["general"], tripCard, timestamp: timeStr }
      ]);
    }

    setIsLoadingChat(false);
  };

  return (
    <TravelPlannerContext.Provider
      value={{
        theme,
        toggleTheme,
        chatMessages,
        setChatMessages,
        isLoadingChat,
        setIsLoadingChat,
        activeTrip,
        setActiveTrip,
        savedTrips,
        saveTrip,
        deleteTrip,
        duplicateTrip,
        updateActiveTrip,
        isSyncingCalendar,
        syncCalendar,
        askAIChat,
        generateNewMockTrip: generateMockTripDetails
      }}
    >
      {children}
    </TravelPlannerContext.Provider>
  );
};

export const useTravelPlanner = () => {
  const context = useContext(TravelPlannerContext);
  if (context === undefined) {
    throw new Error("useTravelPlanner must be used within a TravelPlannerProvider");
  }
  return context;
};
