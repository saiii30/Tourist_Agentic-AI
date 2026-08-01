import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { apiUrl } from "../api/config";
// export type NearbyPlace = {//added new code for nearby agent from line 3
//   id: string;
//   name: string;
//   address: string;
//   rating: number | null;
//   ratingCount: number | null;
//   description: string;
//   image: string | null;
//   googlePhotoName?: string | null;
//   wikiUrl: string | null;
//   wikiSearchFallback?: boolean;
//   mapsUrl?: string | null;
//   website?: string | null;
// };
export type NearbyPlace = {
  id: string;
  name: string;
  address: string;
  rating: number | null;
  ratingCount: number | null;
  description: string;
  image: string | null;
  googlePhotoName?: string | null;
  wikiUrl: string | null;
  wikiSearchFallback?: boolean;
  mapsUrl?: string | null;
  website?: string | null;
  phone?: string | null;              // new
  hours?: string[];                    // new
  accessibility?: Record<string, boolean>; // new
  parking?: Record<string, boolean>;   // new
  payment?: Record<string, boolean>;   // new
  priceLevel?: string | null;          // new
};


export type NearbyCategory = {
  key: string;
  label: string;
  icon: string;
  places: NearbyPlace[];
};

export type NearbyResult = {
  location: string;
  categories: NearbyCategory[];
  followUp?: string;
};//added new code for nearbyagent till line 27

export interface Activity {
  id: string;
  title: string;
  time: string;
  duration: string;
  category: "Sightseeing" | "Food" | "Adventure" | "Culture" | "Relaxation" | "Hotel" | "Transport";
  rating: number;
  entryFee: string;
  description: string;
  location: string;
  image: string;
  latitude?: number;
  longitude?: number;
  isFavorite?: boolean;
  slot?: "Breakfast" | "Morning Activity" | "Lunch" | "Afternoon Activity" | "Evening Activity" | "Dinner" | "Hotel";
  restaurant?: string | null;
  hotel?: string | null;
  google_event_id?: string | null;
  googlePhotoName?: string | null;
  travel?: {
    mode?: string;
    duration?: string;
    distance?: string;
  };
}

export interface HotelDetails {
  id: string;
  name: string;
  image: string;
  photos?: string[];
  rating: number;
  pricePerNight: number;
  amenities: string[];
  distanceFromCenter: string;
  bookingUrl: string;
  googlePhotoName?: string | null;
  reviews?: number;
  hotelType?: string | null;
  roomTypes?: string[];
  parking?: string | null;
}

export interface RestaurantDetails {
  id: string;
  name: string;
  image: string;
  photos?: string[];
  rating: number;
  reviews?: number;
  cuisine: string;
  priceTier: "$" | "$$" | "$$$" | "$$$$";
  distanceFromHotel: string;
  reservationAvailable: boolean;
  googlePhotoName?: string | null;
  address?: string | null;
  website?: string | null;
  mapsUrl?: string | null;
  phone?: string | null;
  hours?: string[];
  diningOptions?: string[];
  servesVegetarian?: boolean;
  servesBreakfast?: boolean;
  servesLunch?: boolean;
  servesDinner?: boolean;
  takeout?: boolean;
  delivery?: boolean;
  dineIn?: boolean;
  goodForChildren?: boolean;
  goodForGroups?: boolean;
  allowsDogs?: boolean;
  accessibility?: Record<string, boolean>;
  parking?: Record<string, boolean>;
  summary?: string | null;
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
  currentLocation?: string;
  travelMode?: string;
  budget: "Low" | "Moderate" | "Luxury";
  travelStyle: "Adventure" | "Relaxed" | "Cultural" | "Family";
  weatherSummary: string;
  weatherIntelligence?: any;
  estimatedCost: number;
  packingTips: string[];
  itinerary: Record<number, Activity[]>;
  status: "Upcoming" | "Draft" | "Completed" | "Cancelled" | "Archived";
  calendarSynced: boolean;
  calendarSyncedAt?: string;
  calendarEventsCount?: number;
  user_id?: string;
  specialInterests?: string[];
  budgetSummary?: any;

  // Premium smart features properties
  isFavorite: boolean;
  hotels: HotelDetails[];
  restaurants: RestaurantDetails[];
  expenses: ExpenseItem[];
  packingChecklist: PackingItem[];
  emergencyContacts: EmergencyContact[];
  notesText: string;
  historyTimeline: HistoryEvent[];
  notifications?: any[];
  discoveredPlaces?: NearbyPlace[];//added new fro nearby agent
  tickets?: any[];
  transport_status?: any;
}

export interface TravelProfile {
  fullName: string;
  email: string;
  mobileNumber: string;
  countryRegion: string;
  dateOfBirth?: string;
  homeCity: string;
  preferredLanguage: string;
  currency: string;
  budgetType: "Low" | "Moderate" | "Luxury";
  favoriteTravelStyles: string[];
  preferredTransport: "Flight" | "Train" | "Bus" | "Car";
  preferredHotel: string;
  preferredFood: string;
  accessibilityNeeds: string[];
  companionType: string;
  averageGroupSize: string;
  travelBehavior: string[];
  favoriteAirline: string;
  preferredTrainClass: string;
  hotelChainPreference: string;
  carRentalPreference: string;
  notificationPreferences: string[];
  aiMemoryEnabled: boolean;
}

export const DEFAULT_TRAVEL_PROFILE: TravelProfile = {
  fullName: "",
  email: "",
  mobileNumber: "",
  countryRegion: "India",
  dateOfBirth: "",
  homeCity: "Chennai",
  preferredLanguage: "English",
  currency: "INR",
  budgetType: "Moderate",
  favoriteTravelStyles: ["Culture"],
  preferredTransport: "Train",
  preferredHotel: "3-Star",
  preferredFood: "Vegetarian",
  accessibilityNeeds: [],
  companionType: "Family",
  averageGroupSize: "4",
  travelBehavior: ["Usually books in advance"],
  favoriteAirline: "",
  preferredTrainClass: "3AC",
  hotelChainPreference: "",
  carRentalPreference: "",
  notificationPreferences: ["Weather alerts", "Flight/train reminders", "Hotel check-in reminders"],
  aiMemoryEnabled: true,
};

export interface QuestionnaireProgress {
  agent: string;
  completed: number;
  total: number;
  progress: number;
}

export interface Message {
  role: "user" | "assistant";
  text: string;
  routes?: string[];
  tripCard?: TripDetails;
  nearbyResult?: NearbyResult;   // added this for nearby agent 133
  questionnaire?: QuestionnaireProgress;
  retryQuestion?: string;
  imageUrl?: string;
  imageUrls?: string[];
  timestamp: string;
}

interface TravelPlannerContextType {
  theme: "light" | "dark";
  toggleTheme: () => void;
  colorTheme: "emerald" | "midnight" | "desert";
  setColorTheme: (theme: "emerald" | "midnight" | "desert") => void;
  travelProfile: TravelProfile;
  setTravelProfile: React.Dispatch<React.SetStateAction<TravelProfile>>;
  chatMessages: Message[];
  setChatMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isLoadingChat: boolean;
  setIsLoadingChat: (val: boolean) => void;
  chatProgressStage: string | null;
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
  generateRealAgentTrip: (params: {
    destination: string;
    days: number;
    budget: string;
    style: string;
    travelers?: number;
    interests?: string;
    startDate?: string;
    currentLocation?: string;
    travelMode?: string;
  }) => Promise<TripDetails | null>;
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

const KNOWLEDGE_QUERY_PATTERNS = [
  "what is",
  "what are",
  "what does",
  "tell me about",
  "explain",
  "dress code",
  "entry fee",
  "timings",
  "opening hours",
  "tourist spots",
  "tourist places",
  "known for",
  "special about",
  "official website",
  "incredible india",
  "tamil nadu tourism",
  "archaeological survey",
  "asi monuments",
];

const CURRENT_TRIP_ACTION_PATTERNS = [
  "change",
  "modify",
  "update",
  "edit",
  "replace",
  "remove",
  "add",
  "save",
  "sync",
  "calendar",
  "my trip",
  "my itinerary",
  "this trip",
  "current trip",
  "day 1",
  "day 2",
  "day 3",
  "day 4",
  "day 5",
];

const shouldSendActiveTripContext = (
  question: string,
  hasActiveTrip: boolean,
  isStartTrip: boolean,
  isOngoingQuestionnaire: boolean | undefined
) => {
  if (!hasActiveTrip || isStartTrip || isOngoingQuestionnaire) {
    return false;
  }

  const qLower = question.trim().toLowerCase();
  const isKnowledgeQuery = KNOWLEDGE_QUERY_PATTERNS.some((pattern) => qLower.includes(pattern));
  const isCurrentTripAction = CURRENT_TRIP_ACTION_PATTERNS.some((pattern) => qLower.includes(pattern));

  if (isKnowledgeQuery && !isCurrentTripAction) {
    return false;
  }

  return isCurrentTripAction;
};

const normalizeItineraryTravel = (itinerary: Record<number, Activity[]> = {}) => {
  return Object.fromEntries(
    Object.entries(itinerary).map(([day, activities]) => [
      day,
      (activities || []).map((activity: any) => ({
        ...activity,
        travel: activity.travel || {
          mode: activity.transport,
          duration: activity.travel_time,
          distance: activity.distance,
        },
      })),
    ])
  ) as Record<number, Activity[]>;
};

// High-Fidelity Mock Trip Generator for fallback
const generateMockTripDetails = (city: string, daysCount = 3): TripDetails => {
  const normCity = city.charAt(0).toUpperCase() + city.slice(1);

  // Try to use a nice generic city-themed Wikimedia image if it matches known patterns, otherwise standard travel banner
  let banner = "https://upload.wikimedia.org/wikipedia/commons/b/b8/Pangong_Tso_lake_in_Ladakh_India.jpg";
  const cityLower = city.toLowerCase();
  if (cityLower.includes("madurai")) {
    banner = "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg";
  } else if (cityLower.includes("goa")) {
    banner = "https://upload.wikimedia.org/wikipedia/commons/f/fe/Calangute_Beach_Goa.jpg";
  } else if (cityLower.includes("chennai")) {
    banner = "https://upload.wikimedia.org/wikipedia/commons/1/15/Chennai_Central_Railway_Station_front_view_2014.jpg";
  } else if (cityLower.includes("ooty")) {
    banner = "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg";
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

  // Color Accent Theme State
  const [colorTheme, setColorTheme] = useState<"emerald" | "midnight" | "desert">(() => {
    const saved = localStorage.getItem("colorTheme");
    return (saved as "emerald" | "midnight" | "desert") || "emerald";
  });

  const [travelProfile, setTravelProfile] = useState<TravelProfile>(() => {
    const saved = localStorage.getItem("travelProfile");
    if (saved) {
      try {
        return { ...DEFAULT_TRAVEL_PROFILE, ...JSON.parse(saved) };
      } catch {
        return DEFAULT_TRAVEL_PROFILE;
      }
    }
    return DEFAULT_TRAVEL_PROFILE;
  });

  // Chat message state
  const [chatMessages, setChatMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem("chatMessages");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return [];
      }
    }
    return [];
  });
  const [isLoadingChat, setIsLoadingChat] = useState<boolean>(false);
  const [chatProgressStage, setChatProgressStage] = useState<string | null>(null);

  // Active Trip Planner states
  const [activeTrip, setActiveTrip] = useState<TripDetails | null>(() => {
    const saved = localStorage.getItem("activeTrip");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

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

  // Synchronize color accent theme class
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("theme-emerald", "theme-midnight", "theme-desert");
    root.classList.add(`theme-${colorTheme}`);
    localStorage.setItem("colorTheme", colorTheme);
  }, [colorTheme]);

  useEffect(() => {
    localStorage.setItem("travelProfile", JSON.stringify(travelProfile));
  }, [travelProfile]);

  // Synchronize localStorage for saved trips
  useEffect(() => {
    localStorage.setItem("savedTrips", JSON.stringify(savedTrips));
  }, [savedTrips]);

  // Synchronize localStorage for active trip
  useEffect(() => {
    if (activeTrip) {
      localStorage.setItem("activeTrip", JSON.stringify(activeTrip));
    } else {
      localStorage.removeItem("activeTrip");
    }
  }, [activeTrip]);

  // Synchronize localStorage for chat messages
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(chatMessages));
  }, [chatMessages]);

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

    if (!targetTrip) {
      setIsSyncingCalendar(false);
      return false;
    }

    const isRemoval = !!options?.remove;
    const historyMsg = isRemoval ? "Google Calendar Events Removed" : "Google Calendar Synchronized";
    const countVal = isRemoval ? 0 : 7 * targetTrip.durationDays;

    return new Promise<boolean>(async (resolve) => {
      try {
        const payload: any = {
          trip_id: targetTrip.id,
          user_id: targetTrip.user_id || "guest_user",
          city: targetTrip.cityName,
          duration: targetTrip.durationDays,
          budget: targetTrip.budget,
          travel_style: targetTrip.travelStyle,
          travelers: targetTrip.travelersCount || 1,
          interests: targetTrip.specialInterests ? targetTrip.specialInterests.join(", ") : "None",
          travel_date: targetTrip.startDate,
          status: isRemoval ? "ARCHIVED" : "SAVED",
          itinerary: {},
          metadata: {
            weather_summary: targetTrip.weatherSummary,
            packing: targetTrip.packingTips,
            packing_checklist: targetTrip.packingChecklist,
            budget_summary: targetTrip.budgetSummary,
            emergency: targetTrip.emergencyContacts,
            hotels: targetTrip.hotels,
            restaurants: targetTrip.restaurants
          }
        };

        Object.entries(targetTrip.itinerary).forEach(([dayNum, activities]) => {
          payload.itinerary[dayNum] = activities.map((act) => {
            let startTime = "09:00";
            let endTime = "12:00";
            if (act.duration && act.duration.includes("-")) {
              const parts = act.duration.split("-");
              startTime = parts[0].trim();
              endTime = parts[1].trim();
            }
            return {
              activity_id: act.id,
              day: parseInt(dayNum),
              start_time: startTime,
              end_time: endTime,
              activity: act.title,
              location: act.location || "",
              category: act.category || "Sightseeing",
              restaurant: act.restaurant || null,
              hotel: act.hotel || null,
              notes: act.description || "",
              google_event_id: act.google_event_id || null
            };
          });
        });

        const res = await axios.post(apiUrl("/calendar/save-and-sync"), payload);
        const data = res.data;

        if (data.needs_auth && data.auth_url && !isRemoval) {
          const width = 600, height = 655;
          const left = window.innerWidth / 2 - width / 2;
          const top = window.innerHeight / 2 - height / 2;

          const handleAuthMessage = async (event: MessageEvent) => {
            if (event.data && event.data.type === 'GOOGLE_AUTH_SUCCESS' && event.data.trip_id === targetTrip.id) {
              window.removeEventListener('message', handleAuthMessage);
              try {
                const finalRes = await axios.post(apiUrl("/calendar/save-and-sync"), payload);

                // Update local state
                setSavedTrips((prev) =>
                  prev.map((t) =>
                    t.id === tripId
                      ? {
                        ...t,
                        calendarSynced: true,
                        calendarEventsCount: countVal,
                        calendarSyncedAt: "Today 10:30 AM",
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
                        calendarSynced: true,
                        calendarEventsCount: countVal,
                        calendarSyncedAt: "Today 10:30 AM",
                        historyTimeline: appendHistoryEvent(prev.historyTimeline, historyMsg, "calendar")
                      }
                      : null
                  );
                }

                setIsSyncingCalendar(false);
                resolve(finalRes.data.synced);
              } catch (e) {
                console.error("Failed to sync after auth:", e);
                setIsSyncingCalendar(false);
                resolve(false);
              }
            }
          };
          window.addEventListener('message', handleAuthMessage);

          window.open(
            data.auth_url,
            "Google Calendar Sync",
            `width=${width},height=${height},top=${top},left=${left}`
          );
        } else {
          // Already authenticated or simulated sync completed
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

          setIsSyncingCalendar(false);
          resolve(data.synced);
        }
      } catch (err) {
        console.warn("Backend save & sync failed, syncing offline:", err);
        setIsSyncingCalendar(false);
        resolve(false);
      }
    });
  };

  const askAIChat = async (question: string) => {
    if (!question.trim()) return;

    if (question.trim().toLowerCase() === "exit") {
      try {
        await axios.post(apiUrl("/chat"), { question });
      } catch (err) {
        console.warn("Backend error on exit:", err);
      }
      setChatMessages([]);
      localStorage.removeItem("chatMessages");
      return;
    }

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setChatMessages((prev) => [...prev, { role: "user", text: question, timestamp: timeStr }]);
    setIsLoadingChat(true);
    setChatProgressStage("Understanding your travel request");

    try {
      const payload: any = { question };
      if (travelProfile.aiMemoryEnabled) {
        payload.travel_profile = travelProfile;
      }
      const qLower = question.trim().toLowerCase();
      const isStartTrip = ["trip", "plan", "itinerary", "vacation", "holiday", "tour", "reset", "start over"].some((k) => qLower.includes(k));

      const lastAssistantMsg = [...chatMessages].reverse().find((m) => m.role === "assistant");
      const isOngoingQuestionnaire = lastAssistantMsg && (
        !!lastAssistantMsg.questionnaire ||
        lastAssistantMsg.routes?.includes("merge") ||
        lastAssistantMsg.routes?.includes("questionnaire") ||
        (lastAssistantMsg.text && (
          lastAssistantMsg.text.includes("When are you planning to travel") ||
          lastAssistantMsg.text.includes("How many days") ||
          lastAssistantMsg.text.includes("What is your budget") ||
          lastAssistantMsg.text.includes("What is your travel style")
        ))
      );

      const includeActiveTripContext = shouldSendActiveTripContext(
        question,
        !!activeTrip,
        isStartTrip,
        !!isOngoingQuestionnaire
      );

      if (activeTrip && includeActiveTripContext) {
        payload.destination = activeTrip.cityName;
        payload.city = activeTrip.cityName;
        payload.days = activeTrip.durationDays;
        payload.budget = activeTrip.budget;
        payload.travel_style = activeTrip.travelStyle;
        payload.interests = activeTrip.specialInterests ? activeTrip.specialInterests.join(", ") : "None";
        payload.travel_mode = activeTrip.travelMode;
        payload.current_location = activeTrip.currentLocation;
        payload.travel_date = activeTrip.startDate;
      }
      let responseData: any = null;
      const streamResponse = await fetch(apiUrl("/chat/stream"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!streamResponse.ok || !streamResponse.body) {
        const fallbackResponse = await axios.post(apiUrl("/chat"), payload);
        responseData = fallbackResponse.data;
      } else {
        const reader = streamResponse.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            const event = JSON.parse(trimmed);
            if (event.type === "progress") {
              setChatProgressStage(event.message || "Planning your trip");
            } else if (event.type === "final") {
              responseData = event.data;
            } else if (event.type === "error") {
              throw new Error(event.message || "Streaming chat failed");
            }
          }
        }

        if (buffer.trim()) {
          const event = JSON.parse(buffer.trim());
          if (event.type === "final") {
            responseData = event.data;
          }
        }
      }

      if (!responseData) {
        throw new Error("No chat response received");
      }

      const answerText = responseData.answer;
      const routes = responseData.routes || [];
      const questionnaire = responseData.questionnaire;
      const imageUrl =
        responseData.image_url ??
        responseData.imageUrl ??
        responseData.metadata?.image_url ??
        responseData.metadata?.imageUrl;
      const imageUrls =
        responseData.image_urls ??
        responseData.imageUrls ??
        responseData.metadata?.image_urls ??
        responseData.metadata?.imageUrls ??
        (imageUrl ? [imageUrl] : undefined);
      const nearbyResult: NearbyResult | undefined =
        responseData.nearbyResult ?? responseData.nearby_result;
      const discoveredPlaces =
        nearbyResult?.categories.flatMap((category) => category.places) ??
        responseData.trip?.discoveredPlaces ??
        responseData.trip?.attractions ??
        [];

      let tripCard: TripDetails | undefined = undefined;
      const tripData = responseData.trip;
      if (tripData) {
        let banner = "https://upload.wikimedia.org/wikipedia/commons/b/b8/Pangong_Tso_lake_in_Ladakh_India.jpg";
        const cityLower = tripData.city.toLowerCase();
        if (cityLower.includes("madurai")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg";
        } else if (cityLower.includes("goa")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/f/fe/Calangute_Beach_Goa.jpg";
        } else if (cityLower.includes("chennai")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/1/15/Chennai_Central_Railway_Station_front_view_2014.jpg";
        } else if (cityLower.includes("ooty")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg";
        }

        const tripStart = tripData.travel_date || new Date(Date.now() + 86400000 * 7).toISOString().split("T")[0];
        const parsedStart = new Date(tripStart);
        const parsedEnd = new Date(parsedStart.getTime() + 86400000 * Math.max(0, (tripData.duration || 1) - 1));
        const tripEnd = parsedEnd.toISOString().split("T")[0];

        tripCard = {
          id: tripData.trip_id || `trip-real-${Date.now()}`,
          cityName: tripData.city,
          bannerImage: banner,
          startDate: tripStart,
          endDate: tripEnd,
          durationDays: tripData.duration,
          travelersCount: tripData.travelers || 1,
          budget: tripData.budget || "Moderate",
          travelStyle: tripData.travel_style || "Cultural",
          weatherSummary: tripData.weather_summary || "Weather Info from AI",
          weatherIntelligence: tripData.weather_intelligence || undefined,
          specialInterests: typeof tripData.interests === "string" && tripData.interests !== "None"
            ? tripData.interests.split(",").map((item: string) => item.trim()).filter(Boolean)
            : [],
          estimatedCost: tripData.budget_summary?.estimated_cost || 0,
          packingTips: tripData.packing || [],
          itinerary: normalizeItineraryTravel(tripData.itinerary || {}),
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
              action: `Live Itinerary generated via ${responseData.metadata?.source || "AI"}`,
              timestamp: "Just now",
              iconName: "sparkles"
            }
          ],
          notifications: tripData.notifications || [],
          discoveredPlaces,
          tickets: tripData.tickets || [],
          transport_status: tripData.transport_status || { status: "success", reason: "" }
        };
      }

      if (nearbyResult) {
        updateActiveTrip((prev) =>
          prev
            ? {
                ...prev,
                discoveredPlaces
              }
            : prev
        );
      }

      if (tripData && (Array.isArray(tripData.tickets) || tripData.transport_status)) {
        updateActiveTrip((prev) =>
          prev
            ? {
                ...prev,
                tickets: Array.isArray(tripData.tickets) ? tripData.tickets : prev.tickets,
                transport_status: tripData.transport_status || prev.transport_status
              }
            : tripCard || prev
        );
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: answerText, routes, tripCard, nearbyResult, questionnaire, imageUrl, imageUrls, timestamp: timeStr }
      ]);//added nearbyagent in 734 above near tripcard..
    } catch (err) {
      console.warn("Backend API not reachable, running in Offline Mode:", err);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      let detectedCity = "Madurai";
      const userMsgs = chatMessages.filter(m => m.role === "user").map(m => m.text);
      const allText = [...userMsgs, question].join(" ");
      const words = allText.split(/\s+/);
      const knownCities = ["madurai", "chennai", "goa", "tokyo", "paris", "delhi", "agra", "mumbai", "ooty", "theni", "wayanad", "coorg", "kodaikanal", "munnar", "mysore"];
      for (const w of words) {
        const cleanW = w.toLowerCase().replace(/[^a-z]/g, "");
        if (knownCities.includes(cleanW) && cleanW.length >= 3) {
          detectedCity = cleanW;
          break;
        }
      }

      const tripCard = generateMockTripDetails(detectedCity);
      tripCard.status = "Draft";

      const answerText = `⚠️ **Offline Mode Active**\n\nI couldn't reach the AI Travel Agent backend server. I have created a dynamic template itinerary card for **${tripCard.cityName}** in offline mode. No real hotels or restaurants are displayed.`;

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: answerText, routes: ["offline"], tripCard, retryQuestion: question, timestamp: timeStr }
      ]);
    }

    setIsLoadingChat(false);
    setChatProgressStage(null);
  };

  const generateRealAgentTrip = async (params: {
    destination: string;
    days: number;
    budget: string;
    style: string;
    travelers?: number;
    interests?: string;
    startDate?: string;
    currentLocation?: string;
    travelMode?: string;
  }): Promise<TripDetails | null> => {
    const query = `Plan a ${params.days} day trip to ${params.destination} starting on ${params.startDate || 'next week'}. Budget: ${params.budget}, Style: ${params.style}, Travelers: ${params.travelers || 1}, Interests: ${params.interests || 'Any'}, Current Location: ${params.currentLocation || 'None'}, Travel Mode: ${params.travelMode || 'Flight'}.`;
    
    setIsLoadingChat(true);
    try {
      const res = await axios.post(apiUrl("/chat"), {
        question: query,
        destination: params.destination,
        city: params.destination,
        days: params.days,
        budget: params.budget,
        travelers: params.travelers || 1,
        travel_style: params.style,
        interests: params.interests || "Any",
        travel_mode: params.travelMode || "Flight",
        current_location: params.currentLocation || "Chennai",
        travel_date: params.startDate,
        travel_profile: travelProfile.aiMemoryEnabled ? travelProfile : undefined
      });
      const tripData = res.data.trip;
      if (tripData) {
        let banner = "https://upload.wikimedia.org/wikipedia/commons/b/b8/Pangong_Tso_lake_in_Ladakh_India.jpg";
        const cityLower = tripData.city.toLowerCase();
        if (cityLower.includes("madurai")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg";
        } else if (cityLower.includes("goa")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/f/fe/Calangute_Beach_Goa.jpg";
        } else if (cityLower.includes("chennai")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/1/15/Chennai_Central_Railway_Station_front_view_2014.jpg";
        } else if (cityLower.includes("ooty")) {
          banner = "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg";
        }

        const tripStart = tripData.travel_date || new Date(Date.now() + 86400000 * 7).toISOString().split("T")[0];
        const parsedStart = new Date(tripStart);
        const parsedEnd = new Date(parsedStart.getTime() + 86400000 * Math.max(0, (tripData.duration || 1) - 1));
        const tripEnd = parsedEnd.toISOString().split("T")[0];

        const tripCard: TripDetails = {
          id: tripData.trip_id || `trip-real-${Date.now()}`,
          cityName: tripData.city,
          bannerImage: banner,
          startDate: tripStart,
          endDate: tripEnd,
          durationDays: tripData.duration,
          travelersCount: tripData.travelers || 1,
          currentLocation: tripData.current_location || undefined,
          travelMode: params.travelMode || tripData.travel_mode || "Flight",
          budget: tripData.budget || "Moderate",
          travelStyle: tripData.travel_style || "Cultural",
          weatherSummary: tripData.weather_summary || "Weather Info from AI",
          weatherIntelligence: tripData.weather_intelligence || undefined,
          specialInterests: typeof tripData.interests === "string" && tripData.interests !== "None"
            ? tripData.interests.split(",").map((item: string) => item.trim()).filter(Boolean)
            : [],
          estimatedCost: tripData.budget_summary?.estimated_cost || 0,
          packingTips: tripData.packing || [],
          itinerary: normalizeItineraryTravel(tripData.itinerary || {}),
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
          ],
          notifications: tripData.notifications || [],
          discoveredPlaces: tripData.discoveredPlaces || tripData.attractions || [],
          tickets: tripData.tickets || [],
          transport_status: tripData.transport_status || { status: "success", reason: "" }
        };

        setActiveTrip(tripCard);
        saveTrip(tripCard);
        setIsLoadingChat(false);
        return tripCard;
      }
      setIsLoadingChat(false);
      return null;
    } catch (err) {
      console.error("Error generating real agent trip:", err);
      setIsLoadingChat(false);
      return null;
    }
  };

  return (
    <TravelPlannerContext.Provider
      value={{
        theme,
        toggleTheme,
        colorTheme,
        setColorTheme,
        travelProfile,
        setTravelProfile,
        chatMessages,
        setChatMessages,
        isLoadingChat,
        setIsLoadingChat,
        chatProgressStage,
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
        generateNewMockTrip: generateMockTripDetails,
        generateRealAgentTrip
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
