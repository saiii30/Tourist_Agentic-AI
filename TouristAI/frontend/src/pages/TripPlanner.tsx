import React, { useState, useEffect, useRef, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import type { Activity } from "../context/TravelPlannerContext";

// Dialog components
import { ModifyDrawer } from "../components/dialogs/ModifyDrawer";
import { SaveDialog } from "../components/dialogs/SaveDialog";
import { CalendarSyncDialog } from "../components/dialogs/CalendarSyncDialog";
import { RegenerateDialog } from "../components/dialogs/RegenerateDialog";
import { ShareDialog } from "../components/dialogs/ShareDialog";
import { FloatingAICopilot } from "../components/dialogs/FloatingAICopilot";
import { AddToItineraryDialog } from "../components/dialogs/AddToItineraryDialog";
import { LocalTransportBookingCard } from "../components/shared/LocalTransportBookingCard";
import { NearbyExplorerWidget } from "../components/shared/NearbyExplorerWidget";
import { CrowdDensityWidget } from "../components/shared/CrowdDensityWidget";
import { ImageSlider } from "../components/chat/ImageSlider";
import { API_BASE_URL } from "../api/config";

// Icons
import {
  Calendar, Users, DollarSign, Edit3, RefreshCw, Share2, Save,
  CheckCircle2, AlertTriangle, AlertCircle, Sparkles,
  ExternalLink, ShieldAlert, BookOpen, Thermometer, FileText,
  Activity as ActivityIcon, Wallet, CheckSquare, Square,
  Bell, Volume2, X, LayoutDashboard, Hotel, Utensils, Landmark,
  MapPin, Plane, BedDouble, Coffee, Camera, Clock, MoreVertical,
  GripVertical, Plus, SlidersHorizontal, ArrowUpDown, Star, Wifi, Car, Waves, Dumbbell, Accessibility, Briefcase, Baby, Dog, Route, Zap
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

type PlannerTab = "Overview" | "Itinerary" | "Tickets" | "Hotels" | "Restaurants" | "Attractions" | "Map" | "Budget" | "Notes" | "Smart Assistant";

type HotelBudgetFilter = "all" | "budget" | "moderate" | "luxury";
type HotelRatingFilter = "all" | "3" | "4";
type HotelSortMode = "recommended" | "lowest" | "highest" | "rating" | "bestValue";
type RestaurantPriceFilter = "all" | "$" | "$$" | "$$$" | "$$$$";
type RestaurantRatingFilter = "all" | "3" | "4";
type RestaurantSortMode = "recommended" | "rating" | "lowest" | "highest" | "reviews";
type AttractionSortMode = "recommended" | "rating" | "reviews" | "nearby";
type AttractionRatingFilter = "all" | "3" | "4";
type HotelImpact = {
  hotel: any;
  averageDistanceKm: number;
  extraDistanceKm: number;
  extraTravelMin: number;
  taxiCostPerDay: number;
  walkability: "High" | "Medium" | "Low";
  reasons: string[];
  betterHotelName?: string;
  betterHotelDistanceKm?: number;
};

const HOTEL_TYPE_FILTERS = ["Hotel", "Resort", "Homestay", "Villa", "Hostel", "Apartment", "Business"] as const;
const HOTEL_AMENITY_FILTERS = [
  { key: "wifi", label: "Wi-Fi", icon: Wifi, terms: ["wi-fi", "wifi", "internet"] },
  { key: "breakfast", label: "Breakfast", icon: Coffee, terms: ["breakfast", "buffet"] },
  { key: "parking", label: "Parking", icon: Car, terms: ["parking", "valet"] },
  { key: "pool", label: "Pool", icon: Waves, terms: ["pool", "swimming"] },
  { key: "gym", label: "Gym", icon: Dumbbell, terms: ["gym", "fitness"] },
  { key: "spa", label: "Spa", icon: Sparkles, terms: ["spa", "sauna", "wellness"] },
  { key: "restaurant", label: "Restaurant", icon: Utensils, terms: ["restaurant", "dining"] },
  { key: "room_service", label: "Room Service", icon: BedDouble, terms: ["room service"] },
  { key: "ac", label: "AC", icon: Thermometer, terms: ["air conditioning", "ac"] },
] as const;

const HOTEL_GUEST_FILTERS = [
  { key: "family", label: "Family", icon: Baby, terms: ["family", "suite", "extra bed"] },
  { key: "business", label: "Business", icon: Briefcase, terms: ["business", "conference", "meeting"] },
  { key: "pet", label: "Pet Friendly", icon: Dog, terms: ["pet"] },
  { key: "accessible", label: "Accessible", icon: Accessibility, terms: ["wheelchair", "accessible", "elevator", "lift"] },
] as const;

const RESTAURANT_CUISINE_FILTERS = ["South Indian", "North Indian", "Chinese", "Italian", "Seafood", "Fast Food", "Cafe", "Bakery"] as const;
const RESTAURANT_FOOD_FILTERS = [
  { key: "vegetarian", label: "Vegetarian", icon: CheckCircle2, terms: ["vegetarian", "veg"] },
  { key: "vegan", label: "Vegan", icon: CheckCircle2, terms: ["vegan"] },
  { key: "jain", label: "Jain", icon: CheckCircle2, terms: ["jain"] },
  { key: "halal", label: "Halal", icon: CheckCircle2, terms: ["halal"] },
  { key: "non_veg", label: "Non-Veg", icon: Utensils, terms: ["non veg", "non-veg", "chicken", "mutton", "seafood", "biryani"] },
] as const;
const RESTAURANT_DINING_FILTERS = [
  { key: "breakfast", label: "Breakfast", icon: Coffee, terms: ["breakfast"] },
  { key: "lunch", label: "Lunch", icon: Utensils, terms: ["lunch"] },
  { key: "dinner", label: "Dinner", icon: Utensils, terms: ["dinner"] },
  { key: "cafe", label: "Cafe", icon: Coffee, terms: ["cafe", "coffee"] },
  { key: "buffet", label: "Buffet", icon: Utensils, terms: ["buffet"] },
  { key: "fine_dining", label: "Fine Dining", icon: Star, terms: ["fine dining", "premium", "luxury"] },
  { key: "street_food", label: "Street Food", icon: MapPin, terms: ["street food", "snack", "chaat"] },
] as const;
const RESTAURANT_AMENITY_FILTERS = [
  { key: "parking", label: "Parking", icon: Car, terms: ["parking", "valet"] },
  { key: "ac", label: "AC", icon: Thermometer, terms: ["air conditioning", "ac"] },
  { key: "outdoor", label: "Outdoor", icon: MapPin, terms: ["outdoor", "terrace", "garden"] },
  { key: "rooftop", label: "Rooftop", icon: Landmark, terms: ["rooftop", "terrace"] },
  { key: "family", label: "Family", icon: Baby, terms: ["family", "children", "kids", "groups"] },
  { key: "accessible", label: "Accessible", icon: Accessibility, terms: ["wheelchair", "accessible"] },
] as const;

const ATTRACTION_CATEGORY_FILTERS = [
  { key: "heritage", label: "Heritage", terms: ["heritage", "historical", "monument", "fort", "palace", "museum"] },
  { key: "temples", label: "Spiritual", terms: ["temple", "shrine", "church", "mosque", "cathedral"] },
  { key: "nature", label: "Nature", terms: ["nature", "park", "garden", "lake", "wildlife", "waterfall"] },
  { key: "beaches", label: "Beaches", terms: ["beach", "coast", "shore", "sea"] },
  { key: "mountains", label: "Viewpoints", terms: ["mountain", "hill", "viewpoint", "valley", "trek"] },
  { key: "shopping", label: "Shopping", terms: ["shopping", "market", "mall", "bazaar"] },
  { key: "museums", label: "Museums", terms: ["museum", "gallery", "art"] },
] as const;

const getHotelSearchText = (hotel: any) => [
  hotel.name,
  hotel.hotelType,
  hotel.parking,
  hotel.distanceFromCenter,
  ...(hotel.amenities || []),
  ...(hotel.roomTypes || []),
].filter(Boolean).join(" ").toLowerCase();

const inferHotelType = (hotel: any) => {
  const text = getHotelSearchText(hotel);
  if (text.includes("resort")) return "Resort";
  if (text.includes("homestay") || text.includes("home stay")) return "Homestay";
  if (text.includes("villa")) return "Villa";
  if (text.includes("hostel")) return "Hostel";
  if (text.includes("apartment") || text.includes("serviced")) return "Apartment";
  if (text.includes("business")) return "Business";
  return "Hotel";
};

const hotelMatchesTerms = (hotel: any, terms: readonly string[]) => {
  const text = getHotelSearchText(hotel);
  return terms.some((term) => text.includes(term));
};

const getHotelRecommendationScore = (hotel: any) => {
  const rating = Number(hotel.rating) || 0;
  const reviews = Number(hotel.reviews) || 0;
  const price = Number(hotel.pricePerNight) || 3000;
  const reviewWeight = Math.min(reviews / 1000, 1.5);
  const valueWeight = price > 0 ? Math.min(5000 / price, 2) : 1;
  return rating * 12 + reviewWeight * 8 + valueWeight * 6;
};

const getRestaurantSearchText = (restaurant: any) => [
  restaurant.name,
  restaurant.cuisine,
  restaurant.priceTier,
  restaurant.distanceFromHotel,
  restaurant.address,
  restaurant.summary,
  ...(restaurant.diningOptions || []),
  restaurant.servesVegetarian ? "vegetarian veg" : "",
  restaurant.servesBreakfast ? "breakfast" : "",
  restaurant.servesLunch ? "lunch" : "",
  restaurant.servesDinner ? "dinner" : "",
  restaurant.goodForChildren ? "family children kids" : "",
  restaurant.goodForGroups ? "family groups" : "",
  restaurant.allowsDogs ? "pet dog" : "",
  Object.values(restaurant.parking || {}).some(Boolean) ? "parking valet" : "",
  Object.values(restaurant.accessibility || {}).some(Boolean) ? "wheelchair accessible" : "",
].filter(Boolean).join(" ").toLowerCase();

const restaurantMatchesTerms = (restaurant: any, terms: readonly string[]) => {
  const text = getRestaurantSearchText(restaurant);
  return terms.some((term) => text.includes(term));
};

const getRestaurantRecommendationScore = (restaurant: any) => {
  const rating = Number(restaurant.rating) || 0;
  const reviews = Number(restaurant.reviews) || 0;
  const priceRank = Math.max(1, String(restaurant.priceTier || "$$").length);
  const reviewWeight = Math.min(reviews / 1000, 1.5);
  const priceWeight = Math.max(0.5, 2.2 - priceRank * 0.35);
  const amenityWeight =
    (restaurant.servesVegetarian ? 1 : 0) +
    (restaurant.goodForChildren ? 0.8 : 0) +
    (Object.values(restaurant.parking || {}).some(Boolean) ? 0.8 : 0) +
    (restaurant.reservationAvailable ? 0.5 : 0);
  return rating * 35 + reviewWeight * 15 + priceWeight * 15 + amenityWeight * 10;
};

const getRestaurantReasons = (restaurant: any) => {
  const reasons: string[] = [];
  if (restaurant.servesVegetarian) reasons.push("Matches vegetarian preference");
  if (restaurant.goodForChildren || restaurant.goodForGroups) reasons.push("Good for family or groups");
  if (Object.values(restaurant.parking || {}).some(Boolean)) reasons.push("Parking available");
  if (restaurant.rating >= 4.5) reasons.push("Excellent rating");
  if ((restaurant.reviews || 0) > 500) reasons.push("Strong review volume");
  if (restaurant.reservationAvailable) reasons.push("Reservation action available");
  if (restaurant.servesBreakfast || restaurant.servesLunch || restaurant.servesDinner) {
    reasons.push(`Serves ${(restaurant.diningOptions || []).slice(0, 2).join(" and ") || "planned meals"}`);
  }
  return reasons.slice(0, 5);
};

const getAttractionSearchText = (place: any) => [
  place.name,
  place.address,
  place.description,
  place.categoryKey,
  place.categoryLabel,
  ...(place.types || []),
].filter(Boolean).join(" ").toLowerCase();

const inferAttractionCategory = (place: any) => {
  const categoryKey = String(place.categoryKey || "").toLowerCase();
  const direct = ATTRACTION_CATEGORY_FILTERS.find((item) => item.key === categoryKey);
  if (direct) return direct.label;
  const text = getAttractionSearchText(place);
  return ATTRACTION_CATEGORY_FILTERS.find((item) => item.terms.some((term) => text.includes(term)))?.label || "Attraction";
};

const getAttractionScore = (place: any) => {
  const rating = Number(place.rating) || 0;
  const reviews = Number(place.ratingCount || place.reviews) || 0;
  const reviewWeight = Math.min(reviews / 1000, 1.5);
  const dataWeight = (place.image || place.googlePhotoName ? 1 : 0) + (readCoordinates(place) ? 1 : 0) + (place.description ? 0.5 : 0);
  return rating * 35 + reviewWeight * 18 + dataWeight * 8;
};

const getAttractionReasons = (place: any) => {
  const reasons: string[] = [];
  if (place.rating >= 4.5) reasons.push("Highly rated by visitors");
  if ((place.ratingCount || place.reviews || 0) > 500) reasons.push("Strong review volume");
  if (place.description) reasons.push("Has useful place context");
  if (place.wikiUrl) reasons.push("Verified with Wikimedia context");
  if (readCoordinates(place)) reasons.push("Can be routed on the trip map");
  return reasons.slice(0, 4);
};

interface TripCountdownProps {
  startDateStr: string;
  compact?: boolean;
}

const TripCountdown: React.FC<TripCountdownProps> = ({ startDateStr, compact = false }) => {
  const [countdown, setCountdown] = useState({ days: "00", hours: "00", minutes: "00", seconds: "00", started: false });

  useEffect(() => {
    const getCountdown = () => {
      try {
        const now = new Date();
        let start: Date;
        if (startDateStr && startDateStr.includes("-")) {
          const parts = startDateStr.split("-");
          start = new Date(
            parseInt(parts[0], 10),
            parseInt(parts[1], 10) - 1,
            parseInt(parts[2], 10)
          );
        } else {
          start = new Date(startDateStr);
        }
        const diffMs = start.getTime() - now.getTime();
        if (diffMs <= 0) {
          return { days: "00", hours: "00", minutes: "00", seconds: "00", started: true };
        }
        const totalSecs = Math.floor(diffMs / 1000);
        const secs = totalSecs % 60;
        const totalMins = Math.floor(totalSecs / 60);
        const mins = totalMins % 60;
        const totalHours = Math.floor(totalMins / 60);
        const hours = totalHours % 24;
        const days = Math.floor(totalHours / 24);
        
        return {
          days: days.toString().padStart(2, "0"),
          hours: hours.toString().padStart(2, "0"),
          minutes: mins.toString().padStart(2, "0"),
          seconds: secs.toString().padStart(2, "0"),
          started: false,
        };
      } catch {
        return { days: "00", hours: "00", minutes: "00", seconds: "00", started: false };
      }
    };

    setCountdown(getCountdown());

    const interval = setInterval(() => {
      setCountdown(getCountdown());
    }, 1000);

    return () => clearInterval(interval);
  }, [startDateStr]);

  if (compact) {
    const days = Number(countdown.days);
    const label = countdown.started
      ? "Trip started"
      : days > 1
        ? `Departs in ${days} days`
        : days === 1
          ? "Departs tomorrow"
          : `Departs in ${Number(countdown.hours)}h ${Number(countdown.minutes)}m`;
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-white/50 bg-white/90 px-2.5 py-1 text-[9.5px] font-extrabold text-teal-800 shadow-sm backdrop-blur-md">
        <Clock className="h-3 w-3 text-teal-600" />
        {label}
      </span>
    );
  }

  return (
    <div className="p-4 bg-teal-600 text-white rounded-2xl shadow-sm text-center space-y-2">
      <h4 className="text-[10px] font-extrabold uppercase tracking-widest text-teal-200">
        Departure Countdown
      </h4>
      <div className="grid grid-cols-4 gap-1 py-1">
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
        <div>
          <span className="block text-lg font-black leading-none">{countdown.seconds}</span>
          <span className="text-[8.5px] font-bold text-teal-200 uppercase">Secs</span>
        </div>
      </div>
    </div>
  );
};

const isUnsplashImage = (value?: string | null): boolean => Boolean(value && /unsplash\.com/i.test(value));

const getFallbackImage = (cityName: string, kind: "banner" | "itinerary" | "hotel" | "restaurant" | "attraction", label?: string) => {
  const city = (cityName || "india").toLowerCase();
  const normalizedLabel = (label || "").toLowerCase();

  if (kind === "banner") {
    if (city.includes("madurai")) return "https://upload.wikimedia.org/wikipedia/commons/e/ea/Madurai_Meenakshi_Temple_West_Tower.jpg";
    if (city.includes("goa")) return "https://upload.wikimedia.org/wikipedia/commons/f/fe/Calangute_Beach_Goa.jpg";
    if (city.includes("chennai")) return "https://upload.wikimedia.org/wikipedia/commons/1/15/Chennai_Central_Railway_Station_front_view_2014.jpg";
    if (city.includes("ooty")) return "https://upload.wikimedia.org/wikipedia/commons/a/a6/Nilgiri_Mountain_Railway_train%2C_India.jpg";
    if (city.includes("mumbai")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Mumbai_Skyline.jpg/1280px-Mumbai_Skyline.jpg";
    if (city.includes("delhi")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/New_Delhi_India_Gate.jpg/1280px-New_Delhi_India_Gate.jpg";
    if (city.includes("bangalore")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Bangalore_Palace.jpg/1280px-Bangalore_Palace.jpg";
    if (city.includes("kerala")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Backwaters_of_Kerala.jpg/1280px-Backwaters_of_Kerala.jpg";
    if (city.includes("jaipur")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Hawa_Mahal_in_Jaipur.jpg/1280px-Hawa_Mahal_in_Jaipur.jpg";
    if (city.includes("agra")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Taj_Mahal_Agra.jpg/1280px-Taj_Mahal_Agra.jpg";
    if (city.includes("varanasi")) return "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Varanasi_Ghats.jpg/1280px-Varanasi_Ghats.jpg";
    return "https://upload.wikimedia.org/wikipedia/commons/b/b8/Pangong_Tso_lake_in_Ladakh_India.jpg";
  }

  if (kind === "hotel") {
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Indian_hotel.jpg/400px-Indian_hotel.jpg";
  }

  if (kind === "restaurant") {
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Indian_dinner.jpg/400px-Indian_dinner.jpg";
  }

  if (kind === "attraction") {
    if (normalizedLabel.includes("temple") || normalizedLabel.includes("mandir") || normalizedLabel.includes("shrine")) {
      return "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Temple_of_India.jpg/400px-Temple_of_India.jpg";
    }
    if (normalizedLabel.includes("beach") || normalizedLabel.includes("coast") || normalizedLabel.includes("sea")) {
      return "https://upload.wikimedia.org/wikipedia/commons/f/fe/Calangute_Beach_Goa.jpg";
    }
    if (normalizedLabel.includes("fort") || normalizedLabel.includes("palace") || normalizedLabel.includes("museum") || normalizedLabel.includes("monument")) {
      return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tourism_in_India.jpg/400px-Tourism_in_India.jpg";
    }
    if (normalizedLabel.includes("park") || normalizedLabel.includes("garden") || normalizedLabel.includes("lake") || normalizedLabel.includes("waterfall")) {
      return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Indian_park.jpg/400px-Indian_park.jpg";
    }
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tourism_in_India.jpg/400px-Tourism_in_India.jpg";
  }

  return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tourism_in_India.jpg/400px-Tourism_in_India.jpg";
};

const resolveImageUrl = (src: string | undefined | null, cityName: string, kind: "banner" | "itinerary" | "hotel" | "restaurant" | "attraction", label?: string) => {
  if (src?.startsWith("/place-photo")) return `${API_BASE_URL}${src}`;
  if (src && src.trim() && !isUnsplashImage(src)) return src;
  return getFallbackImage(cityName, kind, label);
};

const googlePlacePhotoUrl = (photoName?: string | null, maxwidth = 800, maxheight = 800): string | null => {
  if (!photoName) return null;
  return `${API_BASE_URL}/place-photo?photo_name=${encodeURIComponent(photoName)}&maxwidth=${maxwidth}&maxheight=${maxheight}`;
};

const resolvePlaceImageUrl = (
  src: string | undefined | null,
  googlePhotoName: string | undefined | null,
  cityName: string,
  kind: "banner" | "itinerary" | "hotel" | "restaurant" | "attraction",
  label?: string,
  maxwidth = 800,
  maxheight = 800
) => {
  return googlePlacePhotoUrl(googlePhotoName, maxwidth, maxheight) || resolveImageUrl(src, cityName, kind, label);
};

type MapPointKind = "hotel" | "restaurant" | "attraction" | "itinerary";

type MapPoint = {
  id: string;
  name: string;
  lat: number;
  lng: number;
  kind: MapPointKind;
  subtitle?: string;
  day?: number;
};

type CoordinatePair = { lat: number; lng: number };

const getApiBaseUrl = () => API_BASE_URL;

const toFiniteNumber = (value: unknown): number | null => {
  const num = typeof value === "number" ? value : Number(value);
  return Number.isFinite(num) ? num : null;
};

const getCityCenter = (cityName: string): CoordinatePair => {
  const city = cityName.toLowerCase();
  const centers: Array<[string[], { lat: number; lng: number }]> = [
    [["dindigul", "dindugal"], { lat: 10.3673, lng: 77.9803 }],
    [["madurai"], { lat: 9.9252, lng: 78.1198 }],
    [["chennai"], { lat: 13.0827, lng: 80.2707 }],
    [["coimbatore"], { lat: 11.0168, lng: 76.9558 }],
    [["ooty", "udhagamandalam"], { lat: 11.4102, lng: 76.6950 }],
    [["kodaikanal"], { lat: 10.2381, lng: 77.4892 }],
    [["theni"], { lat: 10.0104, lng: 77.4768 }],
    [["trichy", "tiruchirappalli"], { lat: 10.7905, lng: 78.7047 }],
    [["bangalore", "bengaluru"], { lat: 12.9716, lng: 77.5946 }],
    [["mysore"], { lat: 12.2958, lng: 76.6394 }],
    [["coorg", "madikeri"], { lat: 12.4244, lng: 75.7382 }],
    [["goa"], { lat: 15.2993, lng: 74.1240 }],
    [["mumbai"], { lat: 19.0760, lng: 72.8777 }],
    [["delhi"], { lat: 28.6139, lng: 77.2090 }],
  ];

  return centers.find(([keys]) => keys.some((key) => city.includes(key)))?.[1] ?? { lat: 20.5937, lng: 78.9629 };
};

const getActivityMapKind = (activity: Activity): MapPointKind => {
  if (activity.hotel) return "hotel";
  if (activity.restaurant) return "restaurant";

  const text = `${activity.category} ${activity.slot || ""} ${activity.title || ""} ${activity.location || ""}`.toLowerCase();
  if (text.includes("hotel") || text.includes("stay") || text.includes("resort")) return "hotel";
  if (activity.category === "Food" || text.includes("restaurant") || text.includes("breakfast") || text.includes("lunch") || text.includes("dinner") || text.includes("cafe")) return "restaurant";
  return "attraction";
};

const getItineraryMapTypeLabel = (activity: Activity): string => {
  const kind = getActivityMapKind(activity);
  if (kind === "hotel") return "Hotel in itinerary";
  if (kind === "restaurant") return "Restaurant in itinerary";
  return "Place in itinerary";
};

const getItineraryMapName = (activity: Activity): string => {
  if (activity.hotel) return activity.hotel;
  if (activity.restaurant) return activity.restaurant;
  return activity.title || "Itinerary stop";
};

const getRoadmapMeta = (activity: Activity) => {
  const text = `${activity.category} ${activity.slot || ""} ${activity.title || ""}`.toLowerCase();
  if (activity.category === "Transport" || text.includes("flight") || text.includes("train") || text.includes("travel")) {
    return { icon: Plane, label: "Travel", dot: "bg-blue-500", tone: "text-blue-600 bg-blue-50 dark:bg-blue-950/25 dark:text-blue-300" };
  }
  if (activity.category === "Hotel" || activity.hotel || text.includes("stay") || text.includes("check-in")) {
    return { icon: BedDouble, label: "Stay", dot: "bg-orange-500", tone: "text-orange-600 bg-orange-50 dark:bg-orange-950/25 dark:text-orange-300" };
  }
  if (activity.category === "Food" || text.includes("breakfast") || text.includes("lunch") || text.includes("dinner")) {
    return { icon: text.includes("breakfast") ? Coffee : Utensils, label: "Food", dot: "bg-amber-500", tone: "text-amber-600 bg-amber-50 dark:bg-amber-950/25 dark:text-amber-300" };
  }
  return { icon: Camera, label: "Place", dot: "bg-emerald-500", tone: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/25 dark:text-emerald-300" };
};

const getRoadmapImageKind = (activity: Activity): "hotel" | "restaurant" | "attraction" | "itinerary" => {
  const kind = getActivityMapKind(activity);
  if (kind === "hotel") return "hotel";
  if (kind === "restaurant") return "restaurant";
  if (activity.category === "Transport") return "itinerary";
  return "attraction";
};

const getRoadmapSubtitle = (activity: Activity) => {
  if (activity.description) return activity.description;
  if (activity.location) return activity.location;
  return activity.category === "Transport" ? "Travel segment" : "Planned itinerary stop";
};

interface RoadmapEventCardProps {
  activity: Activity;
  cityName: string;
  onDelete: (id: string) => void;
  onReplace: (id: string) => void;
  onViewOnMap: (location: string, title: string) => void;
  compactTimeline?: boolean;
}

const RoadmapEventCard: React.FC<RoadmapEventCardProps> = ({
  activity,
  cityName,
  onDelete,
  onReplace,
  onViewOnMap,
  compactTimeline = false,
}) => {
  const meta = getRoadmapMeta(activity);
  const isTransport = activity.category === "Transport";
  const imageKind = getRoadmapImageKind(activity);
  const fallbackImage = resolveImageUrl(null, cityName, imageKind, activity.title);
  const [imageFailed, setImageFailed] = useState(false);
  const image = imageFailed ? fallbackImage : resolvePlaceImageUrl(activity.image, activity.googlePhotoName, cityName, imageKind, activity.title);

  if (compactTimeline) {
    return (
      <div className="group flex items-stretch gap-3 rounded-xl border border-slate-200/80 bg-white p-2.5 shadow-sm transition hover:border-teal-200 hover:shadow-md dark:border-slate-800 dark:bg-[#111827]">
        <div className="h-24 w-28 shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-900 sm:w-32">
          <img src={image} alt={activity.title} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setImageFailed(true)} className="h-full w-full object-cover" />
        </div>
        <div className="min-w-0 flex-1 py-0.5 text-left">
          <div className="flex items-center gap-2">
            <span className={`rounded-md px-2 py-0.5 text-[9px] font-extrabold ${meta.tone}`}>{meta.label}</span>
            <span className="text-[10px] font-bold text-slate-400">{activity.time} · {activity.duration}</span>
            <div className="ml-auto flex items-center gap-0.5 text-slate-400">
              <button type="button" onClick={() => onReplace(activity.id)} className="rounded-md p-1 hover:bg-slate-100 hover:text-blue-600 dark:hover:bg-slate-800" aria-label="Replace event"><RefreshCw className="h-3.5 w-3.5" /></button>
              <button type="button" onClick={() => onDelete(activity.id)} className="rounded-md p-1 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/25" aria-label="Delete event"><X className="h-3.5 w-3.5" /></button>
            </div>
          </div>
          <h4 className="mt-1 truncate text-sm font-extrabold text-slate-850 dark:text-slate-100">{activity.title}</h4>
          {activity.location && <button type="button" onClick={() => onViewOnMap(activity.location, activity.title)} className="mt-1 flex max-w-full items-center gap-1 text-[10px] font-semibold text-slate-500 hover:text-teal-600 dark:text-slate-400"><MapPin className="h-3 w-3 shrink-0" /><span className="truncate">{activity.location}</span></button>}
          <p className="mt-1 line-clamp-2 text-[10.5px] font-medium leading-relaxed text-slate-500 dark:text-slate-400">{getRoadmapSubtitle(activity)}</p>
        </div>
        {!isTransport && <div className="flex w-16 shrink-0 items-center justify-center border-l border-slate-100 pl-2 dark:border-slate-800"><CrowdDensityWidget destination={activity.title} cityName={cityName} timeStr={activity.time || "10:00"} category={activity.category} variant="meter" /></div>}
      </div>
    );
  }

  return (
    <div className="group rounded-xl border border-slate-200/80 bg-white p-3 shadow-sm transition hover:border-violet-200 hover:shadow-md dark:border-slate-800 dark:bg-[#111827] dark:hover:border-violet-900/60">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-md px-2 py-0.5 text-[10px] font-extrabold ${meta.tone}`}>
              {meta.label}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-500 dark:text-slate-400">
              <Clock className="h-3.5 w-3.5" />
              {activity.duration || activity.time}
            </span>
            {activity.travel?.duration && !isTransport && (
              <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-extrabold text-blue-600 dark:bg-blue-950/25 dark:text-blue-300">
                {activity.travel.duration}
              </span>
            )}
            <div className="ml-auto flex items-center gap-1 text-slate-350">
              <GripVertical className="h-4 w-4" />
              <button type="button" onClick={() => onReplace(activity.id)} className="rounded-lg p-1.5 hover:bg-slate-100 hover:text-blue-600 dark:hover:bg-slate-800" aria-label="Replace event">
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
              <button type="button" onClick={() => onDelete(activity.id)} className="rounded-lg p-1.5 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/25" aria-label="Delete event">
                <X className="h-3.5 w-3.5" />
              </button>
              <MoreVertical className="h-4 w-4" />
            </div>
          </div>

          <div className="mt-1.5 grid gap-3 sm:grid-cols-[1fr_9rem]">
            <div className="min-w-0">
              <h4 className="line-clamp-1 text-sm font-extrabold text-slate-850 dark:text-slate-100">
                {activity.title}
              </h4>
              {activity.location && (
                <button
                  type="button"
                  onClick={() => onViewOnMap(activity.location, activity.title)}
                  className="mt-1 flex max-w-full items-center gap-1 text-left text-[11px] font-semibold text-slate-500 hover:text-violet-600 dark:text-slate-400"
                >
                  <MapPin className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{activity.location}</span>
                </button>
              )}
              <p className="mt-1.5 line-clamp-2 text-[11.5px] font-medium leading-relaxed text-slate-500 dark:text-slate-400">
                {getRoadmapSubtitle(activity)}
              </p>
              {activity.travel?.distance && !isTransport && (
                <div className="mt-2 flex flex-wrap gap-3 text-[10.5px] font-bold text-slate-500 dark:text-slate-400">
                  <span>Distance {activity.travel.distance}</span>
                  {activity.travel.mode && <span>{activity.travel.mode}</span>}
                </div>
              )}
            </div>

            {!isTransport && (
              <div className="overflow-hidden rounded-lg border border-slate-100 bg-slate-100 dark:border-slate-800 dark:bg-slate-900">
                <img
                  src={image}
                  alt={activity.title}
                  loading="lazy"
                  decoding="async"
                  referrerPolicy="no-referrer"
                  onError={() => setImageFailed(true)}
                  className="aspect-[4/3] h-auto w-full object-contain"
                />
              </div>
            )}
          </div>

          {!isTransport && (
            <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800/70">
              <CrowdDensityWidget
                destination={activity.title}
                cityName={cityName}
                timeStr={activity.time || "10:00"}
                category={activity.category}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const normalizeMapName = (value: unknown): string =>
  String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

const readCoordinates = (item: any): CoordinatePair | null => {
  const lat = toFiniteNumber(item?.latitude ?? item?.lat ?? item?.location?.latitude ?? item?.geometry?.location?.lat);
  const lng = toFiniteNumber(item?.longitude ?? item?.lng ?? item?.location?.longitude ?? item?.geometry?.location?.lng);
  return lat !== null && lng !== null ? { lat, lng } : null;
};

const getDistanceKm = (from: CoordinatePair, to: CoordinatePair) => {
  const earthRadiusKm = 6371;
  const toRad = (value: number) => (value * Math.PI) / 180;
  const dLat = toRad(to.lat - from.lat);
  const dLng = toRad(to.lng - from.lng);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(from.lat)) * Math.cos(toRad(to.lat)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const getStableOffset = (seed: string, index: number, spread = 0.018) => {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  }
  const angle = Math.abs(hash % 360) * (Math.PI / 180);
  const radius = spread * (0.45 + ((Math.abs(hash) + index) % 100) / 180);
  return {
    lat: Math.sin(angle) * radius,
    lng: Math.cos(angle) * radius,
  };
};

const escapeHtml = (value: string | number | undefined | null) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

interface TripPlannerProps {
  itineraryOnly?: boolean;
}

export const TripPlanner: React.FC<TripPlannerProps> = ({ itineraryOnly = false }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { activeTrip, updateActiveTrip, generateNewMockTrip, saveTrip, syncCalendar } = useTravelPlanner();

  // Page load and active workspace tab
  const [activeTab, setActiveTab] = useState<PlannerTab>(itineraryOnly ? "Itinerary" : "Overview");
  const [activeItineraryDay, setActiveItineraryDay] = useState<number>(1);

  // Modals / Drawers states
  const [isModifyOpen, setIsModifyOpen] = useState(false);
  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [isRegenOpen, setIsRegenOpen] = useState(false);
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isAddItineraryOpen, setIsAddItineraryOpen] = useState(false);
  const [isReplaceDialogOpen, setIsReplaceDialogOpen] = useState(false);
  const [itemToAdd, setItemToAdd] = useState<{ type: 'hotel' | 'restaurant' | 'attraction', id: string, name: string, location: string, rating: number, image: string, googlePhotoName?: string | null } | null>(null);
  const [mapSearchQuery, setMapSearchQuery] = useState<string | null>(null);
  const shouldRenderInteractiveMap = activeTab === "Map" || itineraryOnly;
  
  // Replacement state
  const [replacementTarget, setReplacementTarget] = useState<{ dayNum: number; activityId: string; activity: any } | null>(null);

  const [leafletLoaded, setLeafletLoaded] = useState(false);
  const [osrmRouteData, setOsrmRouteData] = useState<any>(null);
  const [isLoadingRoute, setIsLoadingRoute] = useState(false);
  const [isApplyingOptimizedRoute, setIsApplyingOptimizedRoute] = useState(false);
  const [currentPosition, setCurrentPosition] = useState<CoordinatePair | null>(null);
  const [hotelBudgetFilter, setHotelBudgetFilter] = useState<HotelBudgetFilter>("all");
  const [hotelRatingFilter, setHotelRatingFilter] = useState<HotelRatingFilter>("all");
  const [hotelTypeFilter, setHotelTypeFilter] = useState<string>("all");
  const [hotelSortMode, setHotelSortMode] = useState<HotelSortMode>("recommended");
  const [hotelAmenityFilters, setHotelAmenityFilters] = useState<string[]>([]);
  const [hotelGuestFilters, setHotelGuestFilters] = useState<string[]>([]);
  const [visibleHotelCount, setVisibleHotelCount] = useState(6);
  const [pendingHotelImpact, setPendingHotelImpact] = useState<HotelImpact | null>(null);
  const [restaurantCuisineFilter, setRestaurantCuisineFilter] = useState<string>("all");
  const [restaurantPriceFilter, setRestaurantPriceFilter] = useState<RestaurantPriceFilter>("all");
  const [restaurantRatingFilter, setRestaurantRatingFilter] = useState<RestaurantRatingFilter>("all");
  const [restaurantSortMode, setRestaurantSortMode] = useState<RestaurantSortMode>("recommended");
  const [restaurantFoodFilters, setRestaurantFoodFilters] = useState<string[]>([]);
  const [restaurantDiningFilters, setRestaurantDiningFilters] = useState<string[]>([]);
  const [restaurantAmenityFilters, setRestaurantAmenityFilters] = useState<string[]>([]);
  const [visibleRestaurantCount, setVisibleRestaurantCount] = useState(6);
  const [attractionCategoryFilter, setAttractionCategoryFilter] = useState<string>("all");
  const [attractionRatingFilter, setAttractionRatingFilter] = useState<AttractionRatingFilter>("all");
  const [attractionSortMode, setAttractionSortMode] = useState<AttractionSortMode>("recommended");
  const [visibleAttractionCount, setVisibleAttractionCount] = useState(6);


  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);

  const effectiveHotels = useMemo(() => {
    if (!activeTrip) return [];
    if (activeTrip.hotels && activeTrip.hotels.length > 0) {
      return activeTrip.hotels;
    }
    const allActs = Object.values(activeTrip.itinerary || {}).flat();
    const itineraryHotels = allActs.filter((a) => a.category === "Hotel" || a.hotel);
    if (itineraryHotels.length > 0) {
      return itineraryHotels.map((act, i) => ({
        id: act.id || `hotel-eff-${i}`,
        name: act.hotel || act.title,
        image: resolvePlaceImageUrl(act.image, act.googlePhotoName, activeTrip.cityName, "hotel", act.hotel || act.title),
        googlePhotoName: act.googlePhotoName,
        rating: act.rating || 4.7,
        reviews: 0,
        pricePerNight: 2800,
        amenities: ["Free Wi-Fi", "AC", "Room Service", "Breakfast"],
        hotelType: "Hotel",
        roomTypes: ["Standard Room"],
        parking: null,
        distanceFromCenter: `0.5 km from ${activeTrip.cityName} Center`,
        bookingUrl: `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(activeTrip.cityName)}`,
        latitude: act.latitude,
        longitude: act.longitude
      }));
    }
    return [
      {
        id: `h-1-${activeTrip.cityName}`,
        name: `Grand ${activeTrip.cityName} Heritage Resort & Spa`,
        image: resolveImageUrl(null, activeTrip.cityName, "hotel"),
        rating: 4.8,
        reviews: 0,
        pricePerNight: 3500,
        amenities: ["Free Wi-Fi", "Pool", "Spa & Wellness", "Breakfast Included"],
        hotelType: "Resort",
        roomTypes: ["Deluxe Room"],
        parking: "Available",
        distanceFromCenter: `0.8 km from ${activeTrip.cityName} Center`,
        bookingUrl: `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(activeTrip.cityName)}`
      },
      {
        id: `h-2-${activeTrip.cityName}`,
        name: `${activeTrip.cityName} Comfort Stay & Suites`,
        image: resolveImageUrl(null, activeTrip.cityName, "hotel"),
        rating: 4.5,
        reviews: 0,
        pricePerNight: 2200,
        amenities: ["Free Wi-Fi", "AC", "Room Service", "Parking"],
        hotelType: "Hotel",
        roomTypes: ["Standard Room"],
        parking: "Available",
        distanceFromCenter: `1.5 km from ${activeTrip.cityName} Center`,
        bookingUrl: `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(activeTrip.cityName)}`
      }
    ];
  }, [activeTrip]);

  useEffect(() => {
    setVisibleHotelCount(6);
  }, [hotelBudgetFilter, hotelRatingFilter, hotelTypeFilter, hotelSortMode, hotelAmenityFilters, hotelGuestFilters]);

  const filteredHotels = useMemo(() => {
    const amenityRules = HOTEL_AMENITY_FILTERS.filter((rule) => hotelAmenityFilters.includes(rule.key));
    const guestRules = HOTEL_GUEST_FILTERS.filter((rule) => hotelGuestFilters.includes(rule.key));

    const matches = effectiveHotels.filter((hotel: any) => {
      const price = Number(hotel.pricePerNight) || 0;
      if (hotelBudgetFilter === "budget" && price > 3000) return false;
      if (hotelBudgetFilter === "moderate" && (price < 1500 || price > 5000)) return false;
      if (hotelBudgetFilter === "luxury" && price < 5000) return false;

      const rating = Number(hotel.rating) || 0;
      if (hotelRatingFilter === "4" && rating < 4) return false;
      if (hotelRatingFilter === "3" && rating < 3) return false;

      if (hotelTypeFilter !== "all" && inferHotelType(hotel).toLowerCase() !== hotelTypeFilter.toLowerCase()) {
        return false;
      }

      if (!amenityRules.every((rule) => hotelMatchesTerms(hotel, rule.terms))) return false;
      if (!guestRules.every((rule) => hotelMatchesTerms(hotel, rule.terms))) return false;

      return true;
    });

    return [...matches].sort((a: any, b: any) => {
      if (hotelSortMode === "lowest") return (Number(a.pricePerNight) || 0) - (Number(b.pricePerNight) || 0);
      if (hotelSortMode === "highest") return (Number(b.pricePerNight) || 0) - (Number(a.pricePerNight) || 0);
      if (hotelSortMode === "rating") return (Number(b.rating) || 0) - (Number(a.rating) || 0);
      if (hotelSortMode === "bestValue") {
        const aValue = (Number(a.rating) || 0) / Math.max(Number(a.pricePerNight) || 1, 1);
        const bValue = (Number(b.rating) || 0) / Math.max(Number(b.pricePerNight) || 1, 1);
        return bValue - aValue;
      }
      return getHotelRecommendationScore(b) - getHotelRecommendationScore(a);
    });
  }, [effectiveHotels, hotelAmenityFilters, hotelBudgetFilter, hotelGuestFilters, hotelRatingFilter, hotelSortMode, hotelTypeFilter]);

  const visibleHotels = filteredHotels.slice(0, visibleHotelCount);
  const toggleHotelAmenityFilter = (key: string) => {
    setHotelAmenityFilters((prev) => prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]);
  };
  const toggleHotelGuestFilter = (key: string) => {
    setHotelGuestFilters((prev) => prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]);
  };
  const clearHotelFilters = () => {
    setHotelBudgetFilter("all");
    setHotelRatingFilter("all");
    setHotelTypeFilter("all");
    setHotelSortMode("recommended");
    setHotelAmenityFilters([]);
    setHotelGuestFilters([]);
  };

  const effectiveRestaurants = useMemo(() => {
    if (!activeTrip) return [];
    if (activeTrip.restaurants && activeTrip.restaurants.length > 0) {
      return activeTrip.restaurants;
    }
    const allActs = Object.values(activeTrip.itinerary || {}).flat();
    const itineraryRestos = allActs.filter((a) => a.category === "Food" || a.restaurant);
    if (itineraryRestos.length > 0) {
      return itineraryRestos.map((act, i) => ({
        id: act.id || `resto-eff-${i}`,
        name: act.restaurant || act.title,
        image: resolvePlaceImageUrl(act.image, act.googlePhotoName, activeTrip.cityName, "restaurant", act.restaurant || act.title),
        googlePhotoName: act.googlePhotoName,
        rating: act.rating || 4.6,
        reviews: 0,
        cuisine: "Authentic Local Cuisine",
        priceTier: "$$" as const,
        distanceFromHotel: "0.5 km",
        reservationAvailable: true,
        diningOptions: ["Lunch", "Dinner"],
        servesLunch: true,
        servesDinner: true,
        goodForChildren: false,
        goodForGroups: false,
        parking: {},
        mapsUrl: null,
        website: null,
        latitude: act.latitude,
        longitude: act.longitude
      }));
    }
    return [
      {
        id: `r-1-${activeTrip.cityName}`,
        name: `${activeTrip.cityName} Traditional Kitchen & Spices`,
        image: resolveImageUrl(null, activeTrip.cityName, "restaurant"),
        rating: 4.7,
        cuisine: "Authentic Local Cuisine",
        priceTier: "$$" as const,
        distanceFromHotel: "0.5 km from hotel",
        reservationAvailable: true,
        reviews: 0,
        diningOptions: ["Lunch", "Dinner"],
        servesLunch: true,
        servesDinner: true,
        goodForChildren: true,
        goodForGroups: true,
        parking: {},
        mapsUrl: null,
        website: null
      },
      {
        id: `r-2-${activeTrip.cityName}`,
        name: `The Spice Garden (${activeTrip.cityName})`,
        image: resolveImageUrl(null, activeTrip.cityName, "restaurant"),
        rating: 4.6,
        cuisine: "Multi-Cuisine & Bar",
        priceTier: "$$$" as const,
        distanceFromHotel: "1.2 km from hotel",
        reservationAvailable: true,
        reviews: 0,
        diningOptions: ["Lunch", "Dinner"],
        servesLunch: true,
        servesDinner: true,
        goodForChildren: true,
        goodForGroups: true,
        parking: {},
        mapsUrl: null,
        website: null
      }
    ];
  }, [activeTrip]);

  useEffect(() => {
    setVisibleRestaurantCount(6);
  }, [restaurantAmenityFilters, restaurantCuisineFilter, restaurantDiningFilters, restaurantFoodFilters, restaurantPriceFilter, restaurantRatingFilter, restaurantSortMode]);

  const filteredRestaurants = useMemo(() => {
    const foodRules = RESTAURANT_FOOD_FILTERS.filter((rule) => restaurantFoodFilters.includes(rule.key));
    const diningRules = RESTAURANT_DINING_FILTERS.filter((rule) => restaurantDiningFilters.includes(rule.key));
    const amenityRules = RESTAURANT_AMENITY_FILTERS.filter((rule) => restaurantAmenityFilters.includes(rule.key));

    const matches = effectiveRestaurants.filter((restaurant: any) => {
      if (restaurantCuisineFilter !== "all" && !getRestaurantSearchText(restaurant).includes(restaurantCuisineFilter.toLowerCase())) {
        return false;
      }
      if (restaurantPriceFilter !== "all" && restaurant.priceTier !== restaurantPriceFilter) return false;

      const rating = Number(restaurant.rating) || 0;
      if (restaurantRatingFilter === "4" && rating < 4) return false;
      if (restaurantRatingFilter === "3" && rating < 3) return false;

      if (!foodRules.every((rule) => restaurantMatchesTerms(restaurant, rule.terms))) return false;
      if (!diningRules.every((rule) => restaurantMatchesTerms(restaurant, rule.terms))) return false;
      if (!amenityRules.every((rule) => restaurantMatchesTerms(restaurant, rule.terms))) return false;
      return true;
    });

    return [...matches].sort((a: any, b: any) => {
      if (restaurantSortMode === "rating") return (Number(b.rating) || 0) - (Number(a.rating) || 0);
      if (restaurantSortMode === "reviews") return (Number(b.reviews) || 0) - (Number(a.reviews) || 0);
      if (restaurantSortMode === "lowest") return String(a.priceTier || "$$").length - String(b.priceTier || "$$").length;
      if (restaurantSortMode === "highest") return String(b.priceTier || "$$").length - String(a.priceTier || "$$").length;
      return getRestaurantRecommendationScore(b) - getRestaurantRecommendationScore(a);
    });
  }, [effectiveRestaurants, restaurantAmenityFilters, restaurantCuisineFilter, restaurantDiningFilters, restaurantFoodFilters, restaurantPriceFilter, restaurantRatingFilter, restaurantSortMode]);

  const visibleRestaurants = filteredRestaurants.slice(0, visibleRestaurantCount);
  const toggleRestaurantFilter = (kind: "food" | "dining" | "amenity", key: string) => {
    const setter = kind === "food" ? setRestaurantFoodFilters : kind === "dining" ? setRestaurantDiningFilters : setRestaurantAmenityFilters;
    setter((prev) => prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]);
  };
  const clearRestaurantFilters = () => {
    setRestaurantCuisineFilter("all");
    setRestaurantPriceFilter("all");
    setRestaurantRatingFilter("all");
    setRestaurantSortMode("recommended");
    setRestaurantFoodFilters([]);
    setRestaurantDiningFilters([]);
    setRestaurantAmenityFilters([]);
  };

  const effectiveAttractions = useMemo(() => {
    if (!activeTrip) return [];
    
    const discoveredPlaces = (activeTrip as any).discoveredPlaces || (activeTrip as any).attractions || [];
    
    const allActs = Object.values(activeTrip.itinerary || {}).flat();
    const itineraryAttractions = allActs.filter(
      (a) => a.category === "Sightseeing" || a.category === "Culture" || a.category === "Adventure" || (!a.restaurant && !a.hotel && a.category !== "Food" && a.category !== "Hotel" && a.category !== "Transport")
    ).map((act, i) => ({
      id: act.id || `att-eff-${i}`,
      name: act.title,
      address: act.location || `${activeTrip.cityName} Sightseeing`,
      rating: act.rating || 4.6,
      ratingCount: 500,
      description: act.description || `Famous tourist attraction and activity spot in ${activeTrip.cityName}.`,
      image: resolvePlaceImageUrl(act.image, (act as any).googlePhotoName, activeTrip.cityName, "attraction", act.title),
      googlePhotoName: (act as any).googlePhotoName || null,
      wikiUrl: null
    }));

    const combined: any[] = [...discoveredPlaces];
    const seenNames = new Set(discoveredPlaces.map((p: any) => p.name ? String(p.name).toLowerCase().trim() : ""));

    for (const item of itineraryAttractions) {
      const cleanName = item.name ? String(item.name).toLowerCase().trim() : "";
      if (cleanName && !seenNames.has(cleanName)) {
        seenNames.add(cleanName);
        combined.push(item);
      }
    }

    if (combined.length > 0) return combined;

    return [
      {
        id: `att-1-${activeTrip.cityName}`,
        name: `${activeTrip.cityName} Main Heritage Site`,
        address: `Historic Quarter, ${activeTrip.cityName}`,
        rating: 4.8,
        ratingCount: 1250,
        description: `Iconic tourist attraction in ${activeTrip.cityName} featuring historic architecture and cultural tours.`,
        image: resolveImageUrl(null, activeTrip.cityName, "attraction"),
        wikiUrl: null
      },
      {
        id: `att-2-${activeTrip.cityName}`,
        name: `${activeTrip.cityName} Botanical Gardens & Lake`,
        address: `Green Belt Drive, ${activeTrip.cityName}`,
        rating: 4.6,
        ratingCount: 890,
        description: `Beautiful botanical gardens and scenic park in ${activeTrip.cityName}.`,
        image: resolveImageUrl(null, activeTrip.cityName, "attraction"),
        wikiUrl: null
      }
    ];
  }, [activeTrip]);

  useEffect(() => {
    setVisibleAttractionCount(6);
  }, [attractionCategoryFilter, attractionRatingFilter, attractionSortMode]);

  const filteredAttractions = useMemo(() => {
    const matches = effectiveAttractions.filter((place: any) => {
      if (attractionCategoryFilter !== "all") {
        const rule = ATTRACTION_CATEGORY_FILTERS.find((item) => item.key === attractionCategoryFilter);
        const text = getAttractionSearchText(place);
        if (rule && !rule.terms.some((term) => text.includes(term)) && String(place.categoryKey || "").toLowerCase() !== rule.key) {
          return false;
        }
      }

      const rating = Number(place.rating) || 0;
      if (attractionRatingFilter === "4" && rating < 4) return false;
      if (attractionRatingFilter === "3" && rating < 3) return false;
      return true;
    });

    return [...matches].sort((a: any, b: any) => {
      if (attractionSortMode === "rating") return (Number(b.rating) || 0) - (Number(a.rating) || 0);
      if (attractionSortMode === "reviews") return (Number(b.ratingCount || b.reviews) || 0) - (Number(a.ratingCount || a.reviews) || 0);
      if (attractionSortMode === "nearby") {
        const hotel = effectiveHotels[0];
        const hotelCoords = readCoordinates(hotel);
        const aCoords = readCoordinates(a);
        const bCoords = readCoordinates(b);
        if (!hotelCoords || !aCoords || !bCoords) return 0;
        return getDistanceKm(hotelCoords, aCoords) - getDistanceKm(hotelCoords, bCoords);
      }
      return getAttractionScore(b) - getAttractionScore(a);
    });
  }, [attractionCategoryFilter, attractionRatingFilter, attractionSortMode, effectiveAttractions, effectiveHotels]);

  const visibleAttractions = filteredAttractions.slice(0, visibleAttractionCount);
  const clearAttractionFilters = () => {
    setAttractionCategoryFilter("all");
    setAttractionRatingFilter("all");
    setAttractionSortMode("recommended");
  };

  // Dynamic Statistics Calculations
  const itineraryDayEntries = activeTrip 
    ? Object.entries(activeTrip.itinerary)
        .map(([dayStr, list]) => [Number(dayStr), list] as const)
        .sort(([dayA], [dayB]) => dayA - dayB)
    : [];
  const activeDayEntry = itineraryDayEntries.find(([dayNum]) => dayNum === activeItineraryDay) || itineraryDayEntries[0];
  const activeDayNum = activeDayEntry?.[0] || 1;
  const activeDayActivities = activeDayEntry?.[1] || [];
  const allActivities = activeTrip ? Object.values(activeTrip.itinerary).flat() : [];
  const getItineraryDayDate = (dayNum: number, format: "short" | "full" = "short") => {
    const baseDate = new Date(activeTrip?.startDate || Date.now());
    if (Number.isNaN(baseDate.getTime())) return `Day ${dayNum}`;
    baseDate.setDate(baseDate.getDate() + dayNum - 1);
    return baseDate.toLocaleDateString("en-IN", format === "full"
      ? { weekday: "short", day: "numeric", month: "short" }
      : { day: "numeric", month: "short" }
    );
  };

  // Average Rating
  const ratings = activeTrip ? [
    ...allActivities.map(a => a.rating).filter(Boolean),
    ...(activeTrip.hotels || []).map(h => h.rating).filter(Boolean),
    ...(activeTrip.restaurants || []).map(r => r.rating).filter(Boolean)
  ] : [];
  const avgRating = ratings.length > 0 
    ? (ratings.reduce((sum, val) => sum + val, 0) / ratings.length).toFixed(1)
    : "4.8";

  const attractionsCount = effectiveAttractions.length;
  const restaurantsCount = effectiveRestaurants.length;
  const hotelsCount = effectiveHotels.length;

  const mapPoints = useMemo(() => {
    if (!activeTrip) return [];

    const fallbackHotel = effectiveHotels[0];
    const cityCenter = getCityCenter(activeTrip.cityName);
    const hotelCoords = readCoordinates(fallbackHotel);
    const baseLat = hotelCoords?.lat ?? cityCenter.lat;
    const baseLng = hotelCoords?.lng ?? cityCenter.lng;
    const points: MapPoint[] = [];
    const seen = new Set<string>();
    const itineraryNames = new Set<string>();

    const addPoint = (
      id: string,
      name: string,
      kind: MapPointKind,
      latValue: unknown,
      lngValue: unknown,
      subtitle?: string,
      index = points.length,
      day?: number,
    ) => {
      const offset = getStableOffset(`${kind}-${name}-${id}`, index);
      const lat = toFiniteNumber(latValue) ?? baseLat + offset.lat;
      const lng = toFiniteNumber(lngValue) ?? baseLng + offset.lng;
      const key = `${kind}-${name.toLowerCase()}-${lat.toFixed(5)}-${lng.toFixed(5)}`;
      if (seen.has(key)) return;
      seen.add(key);
      points.push({ id, name, kind, lat, lng, subtitle, day });
    };

    Object.entries(activeTrip.itinerary || {}).forEach(([day, activities]) => {
      activities.forEach((activity: Activity, index) => {
        if (activity.category === "Transport") return;
        const itineraryName = getItineraryMapName(activity);
        itineraryNames.add(normalizeMapName(itineraryName));
        itineraryNames.add(normalizeMapName(activity.title));
        if (activity.hotel) itineraryNames.add(normalizeMapName(activity.hotel));
        if (activity.restaurant) itineraryNames.add(normalizeMapName(activity.restaurant));

        const coords = readCoordinates(activity);
        addPoint(
          activity.id || `day-${day}-${index}`,
          itineraryName,
          "itinerary",
          coords?.lat,
          coords?.lng,
          `${getItineraryMapTypeLabel(activity)} · Day ${day} · ${activity.time || "Scheduled"} · ${activity.location || activeTrip.cityName}`,
          index + Number(day) * 20,
          Number(day),
        );
      });
    });

    effectiveHotels.forEach((hotel, index) => {
      if (itineraryNames.has(normalizeMapName(hotel.name))) return;
      const coords = readCoordinates(hotel);
      addPoint(
        hotel.id || `hotel-${index}`,
        hotel.name || "Hotel Stay",
        "hotel",
        coords?.lat,
        coords?.lng,
        hotel.distanceFromCenter,
        index,
      );
    });

    effectiveRestaurants.forEach((restaurant, index) => {
      if (itineraryNames.has(normalizeMapName(restaurant.name))) return;
      const coords = readCoordinates(restaurant);
      addPoint(
        restaurant.id || `restaurant-${index}`,
        restaurant.name || "Restaurant",
        "restaurant",
        coords?.lat,
        coords?.lng,
        `${restaurant.cuisine || "Dining"} · ${restaurant.distanceFromHotel || "nearby"}`,
        index + 10,
      );
    });

    effectiveAttractions.forEach((place: any, index) => {
      if (itineraryNames.has(normalizeMapName(place.name))) return;
      const coords = readCoordinates(place);
      addPoint(
        place.id || `attraction-${index}`,
        place.name || "Attraction",
        "attraction",
        coords?.lat,
        coords?.lng,
        place.address || place.description,
        index + 20,
      );
    });

    return points;
  }, [activeTrip, effectiveHotels, effectiveRestaurants, effectiveAttractions]);

  const visibleMapPoints = useMemo(() => {
    if (!activeTrip) return [];
    const scopedPoints = itineraryOnly
      ? mapPoints.filter((point) => point.kind === "itinerary" && point.day === activeItineraryDay)
      : mapPoints;
    if (!mapSearchQuery) return scopedPoints;
    const query = mapSearchQuery.toLowerCase();

    if (itineraryOnly) {
      if (query.includes("hotels in")) return mapPoints.filter((point) => point.kind === "hotel");
      if (query.includes("restaurants in")) return mapPoints.filter((point) => point.kind === "restaurant");
      if (query.includes("itinerary") || query.includes("route")) return scopedPoints;
      if (query === activeTrip.cityName.toLowerCase()) return mapPoints;
      const selectedDayStop = scopedPoints.some((point) =>
        `${point.name} ${point.subtitle || ""}`.toLowerCase().includes(query.replace(`, ${activeTrip.cityName.toLowerCase()}`, ""))
      );
      if (selectedDayStop) return scopedPoints;
    }

    if (query === activeTrip.cityName.toLowerCase()) return scopedPoints;
    if (query.includes("hotels in")) return scopedPoints.filter((point) => point.kind === "hotel");
    if (query.includes("restaurants in")) return scopedPoints.filter((point) => point.kind === "restaurant");
    if (query.includes("itinerary")) return scopedPoints.filter((point) => point.kind === "itinerary");

    const matched = scopedPoints.filter((point) =>
      `${point.name} ${point.subtitle || ""}`.toLowerCase().includes(query.replace(`, ${activeTrip.cityName.toLowerCase()}`, ""))
    );
    return matched.length > 0 ? matched : scopedPoints;
  }, [activeItineraryDay, activeTrip, itineraryOnly, mapPoints, mapSearchQuery]);

  // Dynamically load Leaflet CDN CSS and JS
  useEffect(() => {
    if ((window as any).L) {
      setLeafletLoaded(true);
      return;
    }

    if (shouldRenderInteractiveMap && !leafletLoaded) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      link.id = "leaflet-css-cdn";
      document.head.appendChild(link);

      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.id = "leaflet-js-cdn";
      script.onload = () => {
        setLeafletLoaded(true);
      };
      document.body.appendChild(script);
    }
  }, [leafletLoaded, shouldRenderInteractiveMap]);

  useEffect(() => {
    if (!shouldRenderInteractiveMap || currentPosition || !navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCurrentPosition({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      (error) => {
        console.warn("Current location unavailable for route start:", error);
      },
      { enableHighAccuracy: true, timeout: 6000, maximumAge: 60000 },
    );
  }, [currentPosition, shouldRenderInteractiveMap]);

  // Fetch OSRM route data with fast fallback
  useEffect(() => {
    if (shouldRenderInteractiveMap && activeTrip) {
      const getRoute = async () => {
        setIsLoadingRoute(true);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1500);

        try {
          const attractions: { name: string; lat?: number; lng?: number }[] = [];
          Object.values(activeTrip.itinerary).forEach((dayActivities) => {
            dayActivities.forEach((act) => {
              if (act.category !== "Hotel" && act.category !== "Transport" && act.title) {
                if (!attractions.some((a) => a.name === act.title)) {
                  attractions.push({ name: act.title, lat: act.latitude, lng: act.longitude });
                }
              }
            });
          });

          const hotel = (activeTrip.hotels && activeTrip.hotels.length > 0) ? activeTrip.hotels[0] : null;
          const cityCenter = getCityCenter(activeTrip.cityName);
          const hotelCoords = readCoordinates(hotel);
          const hotelLat = hotelCoords?.lat ?? cityCenter.lat;
          const hotelLng = hotelCoords?.lng ?? cityCenter.lng;

          const response = await fetch(`${getApiBaseUrl()}/optimize-route`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            signal: controller.signal,
            body: JSON.stringify({
              cityName: activeTrip.cityName,
              hotelName: hotel?.name || "Hotel Stay",
              hotelLat: hotelLat,
              hotelLng: hotelLng,
              places: attractions,
              startLocation: currentPosition ? "Current Location" : activeTrip.currentLocation,
              startLat: currentPosition?.lat,
              startLng: currentPosition?.lng,
            }),
          });
          clearTimeout(timeoutId);
          const data = await response.json();
          if (data && data.places) {
            setOsrmRouteData(data);
          }
        } catch (err) {
          console.warn("OSRM route fetch timed out or backend offline, rendering client route:", err);
        } finally {
          clearTimeout(timeoutId);
          setIsLoadingRoute(false);
        }
      };

      getRoute();
    }
  }, [activeTrip, currentPosition, shouldRenderInteractiveMap]);

  // Initialize and update Leaflet Map
  useEffect(() => {
    let map: any = null;
    if (shouldRenderInteractiveMap && leafletLoaded && mapContainerRef.current && activeTrip) {
      const L = (window as any).L;
      if (L) {
        if (mapInstanceRef.current) {
          try {
            mapInstanceRef.current.remove();
          } catch (e) {
            console.error(e);
          }
          mapInstanceRef.current = null;
        }

        if (mapContainerRef.current) {
          try {
            (mapContainerRef.current as any)._leaflet_id = null;
            mapContainerRef.current.innerHTML = "";
          } catch (e) {}
        }

        const firstPoint = visibleMapPoints[0];
        const hotel = activeTrip.hotels?.[0] || null;
        const cityCenter = getCityCenter(activeTrip.cityName);
        const hotelCoords = readCoordinates(hotel);
        const hotelLat = hotelCoords?.lat ?? firstPoint?.lat ?? cityCenter.lat;
        const hotelLng = hotelCoords?.lng ?? firstPoint?.lng ?? cityCenter.lng;

        try {
          map = L.map(mapContainerRef.current, { scrollWheelZoom: true }).setView([hotelLat, hotelLng], 13);
          mapInstanceRef.current = map;

          L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: "abcd",
            maxZoom: 20,
          }).addTo(map);

          const markerStyles: Record<string, { bg: string; label: string }> = {
            hotel: { bg: "#dc2626", label: "H" },
            restaurant: { bg: "#f97316", label: "R" },
            attraction: { bg: "#2563eb", label: "A" },
            itinerary: { bg: "#7c3aed", label: "I" },
            start: { bg: "#16a34a", label: "S" },
          };

          const makeIcon = (kind: MapPointKind | "start", customLabel?: string) => {
            const style = markerStyles[kind] || markerStyles.attraction;
            return L.divIcon({
              className: "",
              html: `<div style="width:30px;height:30px;border-radius:999px;background:${style.bg};color:white;border:3px solid white;box-shadow:0 8px 18px rgba(15,23,42,.28);display:flex;align-items:center;justify-content:center;font:800 12px/1 Inter,system-ui,sans-serif;">${customLabel || style.label}</div>`,
              iconSize: [30, 30],
              iconAnchor: [15, 15],
              popupAnchor: [0, -16],
            });
          };

          const markers: any[] = [];

          if (!itineraryOnly && osrmRouteData?.start?.lat && osrmRouteData?.start?.lng && (!mapSearchQuery || mapSearchQuery === activeTrip.cityName)) {
            markers.push(
              L.marker([osrmRouteData.start.lat, osrmRouteData.start.lng], { icon: makeIcon("start") })
                .addTo(map)
                .bindPopup(`<b>Trip Origin: ${escapeHtml(osrmRouteData.start.name)}</b><br/>Starting point`),
            );
          }

          visibleMapPoints.forEach((point, index) => {
            const dayText = point.day ? `<br/>Day ${escapeHtml(point.day)}` : "";
            const marker = L.marker([point.lat, point.lng], { icon: makeIcon(point.kind, itineraryOnly && point.kind === "itinerary" ? String(index + 1) : undefined) })
              .addTo(map)
              .bindPopup(`<b>${escapeHtml(point.name)}</b><br/>${escapeHtml(point.subtitle || point.kind)}${dayText}`);
            markers.push(marker);
          });

          if (itineraryOnly && visibleMapPoints.length > 1 && visibleMapPoints.every((point) => point.kind === "itinerary")) {
            L.polyline(visibleMapPoints.map((point) => [point.lat, point.lng]), {
              color: "#0d9488",
              weight: 5,
              opacity: 0.85,
              dashArray: "10 7",
            }).addTo(map);
          }

          if (!itineraryOnly && (!mapSearchQuery || mapSearchQuery === activeTrip.cityName) && osrmRouteData?.polyline?.length > 1) {
            L.polyline(osrmRouteData.polyline, {
              color: "#0d9488",
              weight: 5,
              opacity: 0.85,
            }).addTo(map);
          }

          if (markers.length > 0) {
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds(), { padding: [42, 42], maxZoom: 15 });
            if (visibleMapPoints.length === 1) markers[0].openPopup();
            if (itineraryOnly && mapSearchQuery) {
              const selectedIndex = visibleMapPoints.findIndex((point) =>
                `${point.name} ${point.subtitle || ""}`.toLowerCase().includes(mapSearchQuery.toLowerCase().split(",")[0])
              );
              if (selectedIndex >= 0 && markers[selectedIndex]) {
                map.setView([visibleMapPoints[selectedIndex].lat, visibleMapPoints[selectedIndex].lng], 15);
                markers[selectedIndex].openPopup();
              }
            }
          }

          [100, 300, 600].forEach((delay) => {
            setTimeout(() => {
              if (mapInstanceRef.current) {
                try {
                  mapInstanceRef.current.invalidateSize();
                } catch (e) {}
              }
            }, delay);
          });
        } catch (err) {
          console.error("Leaflet map initialization error:", err);
        }
      }
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.error(e);
        }
        mapInstanceRef.current = null;
      }
    };
  }, [activeTrip, itineraryOnly, leafletLoaded, mapSearchQuery, osrmRouteData, shouldRenderInteractiveMap, visibleMapPoints]);

  // Voice alerts state and sync handlers
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const plannerBannerImages = useMemo(() => {
    if (!activeTrip) return [resolveImageUrl(null, "India", "banner")];
    const fetchedImages: string[] = [];
    const addFetchedImage = (item: any) => {
      if (!item) return;
      const photoName = item.googlePhotoName || item.google_photo_name;
      if (photoName) {
        const googleImage = googlePlacePhotoUrl(photoName, 1400, 800);
        if (googleImage) fetchedImages.push(googleImage);
      }
      const source = item.image || item.imageUrl || item.image_url;
      if (source) fetchedImages.push(source.startsWith("/place-photo") ? `${API_BASE_URL}${source}` : source);
    };

    (activeTrip.discoveredPlaces || []).forEach(addFetchedImage);
    Object.values(activeTrip.itinerary || {}).flat().forEach(addFetchedImage);
    (activeTrip.hotels || []).forEach(addFetchedImage);
    (activeTrip.restaurants || []).forEach(addFetchedImage);

    const uniqueFetched = Array.from(new Set(fetchedImages.filter(Boolean))).slice(0, 6);
    return uniqueFetched.length > 0
      ? uniqueFetched
      : [resolveImageUrl(activeTrip.bannerImage, activeTrip.cityName, "banner")];
  }, [activeTrip]);
  const plannerBannerImage = plannerBannerImages[0];

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
  const [exchangeRate, setExchangeRate] = useState<number>(83.5);
  const [rateLoading, setRateLoading] = useState(true);
  const [lastRateUpdate, setLastRateUpdate] = useState<string>("");

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

  // Fetch real-time exchange rate from Frankfurter API
  useEffect(() => {
    const fetchExchangeRate = async () => {
      try {
        setRateLoading(true);
        const response = await fetch('https://api.frankfurter.app/latest?from=USD&to=INR');
        const data = await response.json();
        
        if (data && data.rates && data.rates.INR) {
          setExchangeRate(data.rates.INR);
          setLastRateUpdate(new Date().toLocaleTimeString());
          
          // Update INR amount when rate changes
          const usdValue = parseFloat(usdAmount);
          if (!isNaN(usdValue)) {
            setInrAmount((usdValue * data.rates.INR).toFixed(2));
          }
        }
      } catch (error) {
        console.error('Failed to fetch exchange rate:', error);
        // Fallback to default rate if API fails
        setExchangeRate(83.5);
      } finally {
        setRateLoading(false);
      }
    };

    fetchExchangeRate();
    
    // Refresh rate every 30 minutes
    const interval = setInterval(fetchExchangeRate, 30 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

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

  const handleApplyOptimizedRoute = () => {
    if (!activeTrip || !osrmRouteData?.places?.length) {
      triggerToast("The optimized map route is still loading. Please try again in a moment.", "info");
      return;
    }

    setIsApplyingOptimizedRoute(true);
    const routeOrder = new Map<string, number>(
      osrmRouteData.places.map((place: any, index: number) => [String(place.name || "").trim().toLowerCase(), index])
    );

    updateActiveTrip((trip) => {
      if (!trip) return null;
      const dayActivities = [...(trip.itinerary[activeDayNum] || [])];
      const movable = dayActivities
        .filter((activity) => activity.category !== "Hotel" && activity.category !== "Transport")
        .sort((left, right) => {
          const leftOrder = routeOrder.get(String(left.title || "").trim().toLowerCase()) ?? Number.MAX_SAFE_INTEGER;
          const rightOrder = routeOrder.get(String(right.title || "").trim().toLowerCase()) ?? Number.MAX_SAFE_INTEGER;
          return leftOrder - rightOrder;
        });
      let movableIndex = 0;
      const reordered = dayActivities.map((activity) =>
        activity.category === "Hotel" || activity.category === "Transport"
          ? activity
          : movable[movableIndex++] || activity
      );
      return {
        ...trip,
        itinerary: { ...trip.itinerary, [activeDayNum]: reordered },
        historyTimeline: [{
          id: `hist-route-${Date.now()}`,
          action: `Optimized Day ${activeDayNum} route from the itinerary map`,
          timestamp: "Just now",
          iconName: "route",
        }, ...trip.historyTimeline],
      };
    });
    setIsApplyingOptimizedRoute(false);
    triggerToast(`Day ${activeDayNum} route optimized`, "success");
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

  /*
  const itineraryDayEntries = Object.entries(activeTrip.itinerary)
    .map(([dayStr, list]) => [Number(dayStr), list] as const)
    .sort(([dayA], [dayB]) => dayA - dayB);
  const activeDayEntry = itineraryDayEntries.find(([dayNum]) => dayNum === activeItineraryDay) || itineraryDayEntries[0];
  const activeDayNum = activeDayEntry?.[0] || 1;
  const activeDayActivities = activeDayEntry?.[1] || [];
  const allActivities = Object.values(activeTrip.itinerary).flat();
  /*
          /* bookingUrl: `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(activeTrip.cityName)}`
        },
        {
          id: `h-2-${activeTrip.cityName}`,
          name: `${activeTrip.cityName} Comfort Stay & Suites`,
          image: resolveImageUrl(null, activeTrip.cityName, "hotel"),
          rating: 4.5,
          pricePerNight: 2200,
          amenities: ["Free Wi-Fi", "AC", "Room Service", "Parking"],
          distanceFromCenter: `1.5 km from ${activeTrip.cityName} Center`,
          bookingUrl: `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(activeTrip.cityName)}`
        }
      ]; */

  /*
    ? activeTrip.restaurants
    : [
        {
          id: `r-1-${activeTrip.cityName}`,
          name: `${activeTrip.cityName} Traditional Kitchen & Spices`,
          image: resolveImageUrl(null, activeTrip.cityName, "restaurant"),
          rating: 4.7,
          cuisine: "Authentic Local Cuisine",
          priceTier: "$$" as const,
          distanceFromHotel: "0.5 km from hotel",
          reservationAvailable: true
        },
        {
          id: `r-2-${activeTrip.cityName}`,
          name: `The Spice Garden (${activeTrip.cityName})`,
          image: resolveImageUrl(null, activeTrip.cityName, "restaurant"),
          rating: 4.6,
          cuisine: "Multi-Cuisine & Bar",
          priceTier: "$$$" as const,
          distanceFromHotel: "1.2 km from hotel",
          reservationAvailable: true
        }
      ]; */

  // const discoveredPlaces = activeTrip.discoveredPlaces ?? [];
  // const itineraryAttractions = allActivities.filter(
  //   (a) => a.category === "Sightseeing" || a.category === "Culture" || a.category === "Adventure" || (!a.restaurant && !a.hotel && a.category !== "Food" && a.category !== "Hotel" && a.category !== "Transport")
  // );

  /*
    ? discoveredPlaces
    : (itineraryAttractions.length > 0
        ? itineraryAttractions.map((act, i) => ({
            id: act.id || `att-eff-${i}`,
            name: act.title,
            address: act.location || `${activeTrip.cityName} Sightseeing`,
            rating: act.rating || 4.6,
            ratingCount: 500,
            description: act.description || `Famous tourist attraction and activity spot in ${activeTrip.cityName}.`,
            image: act.image || resolveImageUrl(null, activeTrip.cityName, "attraction", act.title),
            wikiUrl: null
          }))
        : [
            {
              id: `att-1-${activeTrip.cityName}`,
              name: `${activeTrip.cityName} Main Heritage Site`,
              address: `Historic Quarter, ${activeTrip.cityName}`,
              rating: 4.8,
              ratingCount: 1250,
              description: `Iconic tourist attraction in ${activeTrip.cityName} featuring historic architecture and cultural tours.`,
              image: resolveImageUrl(null, activeTrip.cityName, "attraction"),
              wikiUrl: null
            },
            {
              id: `att-2-${activeTrip.cityName}`,
              name: `${activeTrip.cityName} Botanical Gardens & Lake`,
              address: `Green Belt Drive, ${activeTrip.cityName}`,
              rating: 4.6,
              ratingCount: 890,
              description: `Beautiful botanical gardens and scenic park in ${activeTrip.cityName}.`,
              image: resolveImageUrl(null, activeTrip.cityName, "attraction"),
              wikiUrl: null
            }
          ]); */

  const totalDistance = osrmRouteData?.distance_km && osrmRouteData.distance_km > 0
    ? Math.round(osrmRouteData.distance_km)
    : (effectiveAttractions.length > 0 ? effectiveAttractions.length * 6 + 5 : (allActivities.length > 0 ? allActivities.length * 4 : 20));
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

  const getHotelCircuitImpact = (hotel: any): HotelImpact | null => {
    if (!activeTrip) return null;
    const hotelCoords = readCoordinates(hotel);
    if (!hotelCoords) return null;

    const attractionCoords = Object.values(activeTrip.itinerary || {})
      .flat()
      .filter((activity) => activity.category !== "Hotel" && activity.category !== "Transport")
      .map((activity) => readCoordinates(activity))
      .filter(Boolean) as CoordinatePair[];

    if (attractionCoords.length === 0) return null;

    const averageDistanceKm = attractionCoords.reduce((sum, coords) => sum + getDistanceKm(hotelCoords, coords), 0) / attractionCoords.length;

    const candidates = effectiveHotels
      .map((candidate) => {
        const coords = readCoordinates(candidate);
        if (!coords) return null;
        const avg = attractionCoords.reduce((sum, point) => sum + getDistanceKm(coords, point), 0) / attractionCoords.length;
        return { hotel: candidate, averageDistanceKm: avg };
      })
      .filter(Boolean) as { hotel: any; averageDistanceKm: number }[];

    const bestCandidate = candidates.sort((a, b) => a.averageDistanceKm - b.averageDistanceKm)[0];
    const baselineDistance = bestCandidate?.averageDistanceKm ?? averageDistanceKm;
    const extraDistanceKm = Math.max(0, averageDistanceKm - baselineDistance);
    const extraTravelMin = Math.round(extraDistanceKm * 7 * 2);
    const taxiCostPerDay = Math.round(extraDistanceKm * 2 * 28);
    const walkability = averageDistanceKm <= 2 ? "High" : averageDistanceKm <= 5 ? "Medium" : "Low";

    const reasons = [
      `${averageDistanceKm.toFixed(1)} km average distance from planned places`,
      walkability === "High" ? "Good walkability for the itinerary" : walkability === "Medium" ? "May need short cab rides between stops" : "Likely needs cab rides for most sightseeing",
      extraDistanceKm > 0.5 ? `Adds about ${extraTravelMin} min/day versus the closest stay` : "Close to the current route cluster",
      taxiCostPerDay > 0 ? `Estimated extra taxi cost: ₹${taxiCostPerDay}/day` : "No meaningful extra taxi cost",
    ];

    return {
      hotel,
      averageDistanceKm,
      extraDistanceKm,
      extraTravelMin,
      taxiCostPerDay,
      walkability,
      reasons,
      betterHotelName: bestCandidate?.hotel?.id !== hotel.id ? bestCandidate?.hotel?.name : undefined,
      betterHotelDistanceKm: bestCandidate?.hotel?.id !== hotel.id ? bestCandidate?.averageDistanceKm : undefined,
    };
  };

  const shouldWarnForHotelImpact = (impact: HotelImpact | null) => {
    if (!impact) return false;
    return impact.averageDistanceKm > 5 || impact.extraDistanceKm > 2.5 || impact.extraTravelMin >= 25;
  };


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

  const handleReplaceActivity = (dayNum: number, activityId: string) => {
    // Find the activity to be replaced
    const activity = activeTrip.itinerary[dayNum]?.find(act => act.id === activityId);
    if (activity) {
      setReplacementTarget({ dayNum, activityId, activity });
      setIsReplaceDialogOpen(true);
    }
  };

  const handleReplaceChoice = (choice: 'hotel' | 'restaurant' | 'attraction') => {
    setIsReplaceDialogOpen(false);
    
    // Redirect to the appropriate tab
    setActiveTab(choice.charAt(0).toUpperCase() + choice.slice(1) as any);
    
    triggerToast(`Select a ${choice} to replace the activity`, "info");
  };

  const handleReplaceWithItem = (item: any, type: 'hotel' | 'restaurant' | 'attraction') => {
    if (!replacementTarget) return;
    
    const { dayNum, activityId } = replacementTarget;
    
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const updatedItinerary = { ...prev.itinerary };
      updatedItinerary[dayNum] = updatedItinerary[dayNum].map(act => {
        if (act.id === activityId) {
          const nextName = item.name || item.title;
          return {
            ...act,
            title: type === 'hotel' ? `Stay at ${nextName}` : type === 'restaurant' ? `Dine at ${nextName}` : nextName,
            description: item.description || (type === 'hotel' ? `Stay at ${nextName}.` : type === 'restaurant' ? `Dine at ${nextName}.` : `Visit ${nextName}.`),
            location: item.location || item.distanceFromCenter || item.distanceFromHotel || item.address || act.location,
            entryFee: type === 'hotel' ? "Included" : type === 'restaurant' ? "Standard pricing" : item.entryFee || "Free / varies",
            rating: item.rating || 4.5,
            image: item.image || act.image,
            latitude: item.latitude ?? item.lat ?? act.latitude,
            longitude: item.longitude ?? item.lng ?? act.longitude,
            hotel: type === 'hotel' ? nextName : null,
            restaurant: type === 'restaurant' ? nextName : null,
            category: type === 'hotel' ? "Hotel" : type === 'restaurant' ? "Food" : "Sightseeing"
          };
        }
        return act;
      });

      const newHistory = [
        { id: `hist-rep-${Date.now()}`, action: `🔄 Replaced with ${type}: ${item.name || item.title}`, timestamp: "Just now", iconName: "refresh-cw" },
        ...prev.historyTimeline
      ];

      triggerToast("Activity Replaced Successfully", "success");
      setReplacementTarget(null);
      return { ...prev, itinerary: updatedItinerary, historyTimeline: newHistory };
    });
  };

  const applyHotelSelection = (hotelId: string, mode: "normal" | "rebuild" = "normal") => {
    updateActiveTrip((prev) => {
      if (!prev) return null;
      const matched = prev.hotels.find((h) => h.id === hotelId);
      const reordered = matched ? [matched, ...prev.hotels.filter((h) => h.id !== hotelId)] : prev.hotels;
      return {
        ...prev,
        hotels: reordered,
        historyTimeline: [
          { id: `hist-hot-${Date.now()}`, action: mode === "rebuild" ? `🏨 Hotel changed and route review opened: ${matched?.name}` : `🏨 Hotel changed: ${matched?.name}`, timestamp: "Just now", iconName: "home" },
          ...prev.historyTimeline
        ]
      };
    });
    setPendingHotelImpact(null);
    if (mode === "rebuild") {
      setActiveTab("Map");
      setMapSearchQuery(`Itinerary in ${activeTrip.cityName}`);
      triggerToast("Hotel selected. Map route will refresh around this stay.", "info");
    } else {
      triggerToast("Accommodation Updated Successfully!", "success");
    }
  };

  // Switch/Change Hotel from tab view directly
  const handleSwapHotel = (hotelId: string) => {
    const matched = effectiveHotels.find((h) => h.id === hotelId);
    if (!matched) return;
    const impact = getHotelCircuitImpact(matched);
    if (shouldWarnForHotelImpact(impact)) {
      setPendingHotelImpact(impact);
      return;
    }
    applyHotelSelection(hotelId);
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
    resolvePlaceImageUrl(
      itemToAdd.image,
      itemToAdd.googlePhotoName,
      activeTrip?.cityName || "India",
      itemToAdd.type === "hotel" ? "hotel" : itemToAdd.type === "restaurant" ? "restaurant" : "attraction",
      itemToAdd.name
    ),

  googlePhotoName: itemToAdd.googlePhotoName || null,

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
  const interestsLabel = activeTrip.specialInterests && activeTrip.specialInterests.length > 0
    ? activeTrip.specialInterests.join(", ")
    : "Any";
  const isInterestsSet = interestsLabel !== "Any";
  const isGenerated = Object.keys(activeTrip.itinerary).length > 0;
  const isSaved = activeTrip.status === "Upcoming" || activeTrip.status === "Completed";
  const isSynced = activeTrip.calendarSynced;

  // Currency Converter calculation
  const handleUsdChange = (val: string) => {
    setUsdAmount(val);
    const numeric = parseFloat(val);
    if (!isNaN(numeric)) {
      setInrAmount((numeric * exchangeRate).toFixed(2));
    } else {
      setInrAmount("");
    }
  };

  const handleInrChange = (val: string) => {
    setInrAmount(val);
    const numeric = parseFloat(val);
    if (!isNaN(numeric)) {
      setUsdAmount((numeric / exchangeRate).toFixed(2));
    } else {
      setUsdAmount("");
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
      <div className={`flex-1 overflow-y-auto pb-28 space-y-4 ${itineraryOnly ? "p-2 sm:p-3" : "p-4 sm:p-6"}`}>

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

        {/* ──────── REPLACEMENT MODE BANNER ──────── */}
        {replacementTarget && (
          <div className="p-3 bg-blue-500 text-white rounded-2xl flex items-center justify-between text-xs font-bold shadow-md">
            <span className="flex items-center gap-1.5">
              <RefreshCw className="w-4.5 h-4.5" />
              Replace Mode: Select a {activeTab} to replace "{replacementTarget.activity.title}"
            </span>
            <button
              onClick={() => {
                setReplacementTarget(null);
                setActiveTab("Itinerary");
              }}
              className="px-3 py-1 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {!itineraryOnly && <>
        {/* ──────── 2. TOP HERO STATS BLOCK ──────── */}
        <div className="relative rounded-3xl overflow-hidden border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#111827] shadow-sm text-left">
          {/* Banner Image */}
          <div className="relative h-44 bg-gradient-to-br from-teal-50 via-sky-50 to-amber-50 sm:h-52 dark:from-teal-950/40 dark:via-sky-950/30 dark:to-amber-950/20">
            <div className="absolute inset-0 z-0">
              <ImageSlider images={plannerBannerImages} variant="banner" />
            </div>
            <div className="pointer-events-none absolute inset-0 z-10 bg-gradient-to-t from-teal-950/85 via-sky-900/25 to-transparent" />

            <div className="absolute bottom-4 left-5 z-20 text-white">
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
                <TripCountdown startDateStr={activeTrip.startDate} compact />
              </p>
            </div>

            <div className="absolute right-4 top-4 z-20 flex gap-2">
              <span className="flex items-center gap-1 rounded-full border border-white/70 bg-white/85 px-3 py-1 text-[10px] font-bold text-slate-700 shadow-sm backdrop-blur-md">
                <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                {tempStr} Weather
                {activeTrip.weatherIntelligence?.outdoor_score ? ` · ${activeTrip.weatherIntelligence.outdoor_score}/100` : ""}
              </span>
              <span className="px-3 py-1 bg-teal-500 text-slate-950 text-[10px] font-extrabold rounded-full shadow-sm">
                ₹{activeTrip.estimatedCost} Cost
              </span>
            </div>

            <div className="absolute bottom-4 right-4 z-20 hidden w-72 lg:block">
              <CrowdDensityWidget
                destination={activeTrip.cityName}
                cityName={activeTrip.cityName}
                dateStr={activeTrip.startDate}
                timeStr="10:00"
                category="destination"
                variant="floating"
              />
            </div>
          </div>

          <div className="border-b border-slate-100 bg-white p-4 dark:border-slate-850 dark:bg-[#111827] lg:hidden">
            <CrowdDensityWidget
              destination={activeTrip.cityName}
              cityName={activeTrip.cityName}
              dateStr={activeTrip.startDate}
              timeStr="10:00"
              category="destination"
            />
          </div>

          {/* Stepper Progress bar */}
          <div className="p-4 bg-slate-50/50 dark:bg-slate-900/10 border-b border-slate-100 dark:border-slate-850">
            <div className="flex flex-wrap items-center justify-around gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              <div className="flex items-center gap-1 text-teal-600 dark:text-teal-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Destination: {activeTrip.cityName}</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isBudgetSet ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isBudgetSet ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Budget: {activeTrip.budget || "Not set"}</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isTravelersSet ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isTravelersSet ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Travelers: {activeTrip.travelersCount || 0}</span>
              </div>
              <span className="text-slate-300 dark:text-slate-800 font-normal">➔</span>

              <div className={`flex items-center gap-1 ${isInterestsSet ? "text-teal-600 dark:text-teal-400" : ""}`}>
                {isInterestsSet ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />}
                <span>Interests: {interestsLabel}</span>
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
              { label: "Est Budget", val: `💰 ₹${((activeTrip.estimatedCost && activeTrip.estimatedCost > 500) ? activeTrip.estimatedCost : (hotelsCount * 2500 + attractionsCount * 250 + restaurantsCount * 400)).toLocaleString('en-IN')}`, color: "text-emerald-600" },
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
          {(["Overview", "Tickets", "Hotels", "Restaurants", "Attractions", "Budget", "Notes"] as const).map((tab) => {
            const active = activeTab === tab;
            const iconsMap: Record<string, React.ReactNode> = {
              Overview: <LayoutDashboard className="w-3.5 h-3.5" />,
              Itinerary: <Calendar className="w-3.5 h-3.5" />,
              Tickets: <ActivityIcon className="w-3.5 h-3.5" />,
              Hotels: <Hotel className="w-3.5 h-3.5" />,
              Restaurants: <Utensils className="w-3.5 h-3.5" />,
              Attractions: <Landmark className="w-3.5 h-3.5" />,
              Map: <MapPin className="w-3.5 h-3.5" />,
              Budget: <Wallet className="w-3.5 h-3.5" />,
              Notes: <FileText className="w-3.5 h-3.5" />,
              "Smart Assistant": <Sparkles className="w-3.5 h-3.5" />
            };
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative px-4 py-2.5 text-xs font-bold transition-colors select-none flex-shrink-0 flex items-center gap-1.5 ${
                  active ? "text-teal-600 dark:text-teal-400" : "text-slate-400 hover:text-slate-700 dark:hover:text-slate-350"
                }`}
              >
                {iconsMap[tab]}
                <span>{tab}</span>
                {active && (
                  <motion.div
                    layoutId="plannerTabGlow"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-600 dark:bg-teal-400"
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                  />
                )}
              </button>
            );
          })}
        </div>
        </>}

        {itineraryOnly && (
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200/70 bg-white px-4 py-3 text-left shadow-sm dark:border-slate-800 dark:bg-[#111827]">
            <div className="flex min-w-0 items-center gap-3">
              <img
                src={plannerBannerImage}
                alt=""
                onError={(event) => {
                  event.currentTarget.onerror = null;
                  event.currentTarget.src = resolveImageUrl(activeTrip.bannerImage, activeTrip.cityName, "banner");
                }}
                className="h-11 w-11 shrink-0 rounded-xl object-cover"
              />
              <div className="min-w-0">
                <h1 className="truncate font-heading text-base font-extrabold text-slate-900 dark:text-white">{activeTrip.durationDays} Days in {activeTrip.cityName}</h1>
                <p className="mt-1 flex flex-wrap items-center gap-2 text-[10px] font-semibold text-slate-400"><Calendar className="h-3.5 w-3.5" /> {activeTrip.startDate} – {activeTrip.endDate}<span>·</span><Users className="h-3.5 w-3.5" /> {activeTrip.travelersCount} Travelers</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setIsModifyOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-extrabold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900"><Edit3 className="h-3.5 w-3.5 text-teal-600" /><span className="hidden xl:inline">Modify</span></button>
              <button type="button" onClick={() => setIsRegenOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-extrabold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900"><RefreshCw className="h-3.5 w-3.5 text-teal-600" /><span className="hidden xl:inline">Regenerate</span></button>
              <button
                type="button"
                onClick={() => activeTrip.calendarSynced ? void handleRemoveCalendarEvents() : setIsSyncOpen(true)}
                className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-[10px] font-extrabold ${activeTrip.calendarSynced ? "border-rose-200 text-rose-600 hover:bg-rose-50 dark:border-rose-900/40" : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900"}`}
              >
                <Calendar className="h-3.5 w-3.5" /><span className="hidden xl:inline">{activeTrip.calendarSynced ? "Unsync" : "Calendar"}</span>
              </button>
              <button type="button" onClick={() => setIsShareOpen(true)} className="rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-extrabold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900">Share</button>
              <button type="button" onClick={() => setIsSaveOpen(true)} className="rounded-xl bg-teal-600 px-3.5 py-2 text-[10px] font-extrabold text-white hover:bg-teal-700">Save trip</button>
            </div>
          </div>
        )}

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

                  {activeTrip.weatherIntelligence && (
                    <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <h3 className="font-heading text-sm font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                            <Thermometer className="w-4.5 h-4.5 text-amber-500" />
                            Trip Weather Intelligence
                          </h3>
                          <p className="mt-1 text-[10.5px] font-semibold text-slate-500 dark:text-slate-400">
                            Outdoor score {activeTrip.weatherIntelligence.outdoor_score ?? "--"}/100 · {activeTrip.weatherIntelligence.current?.description || activeTrip.weatherSummary}
                          </p>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-[10px] font-extrabold ${
                          (activeTrip.weatherIntelligence.outdoor_score || 0) >= 75
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300"
                            : (activeTrip.weatherIntelligence.outdoor_score || 0) >= 50
                              ? "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300"
                              : "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300"
                        }`}>
                          {(activeTrip.weatherIntelligence.outdoor_score || 0) >= 75 ? "Good for sightseeing" : (activeTrip.weatherIntelligence.outdoor_score || 0) >= 50 ? "Plan carefully" : "Prefer indoor plans"}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                        {(activeTrip.weatherIntelligence.forecast || []).slice(0, 5).map((day: any) => (
                          <div key={`${day.day}-${day.date}`} className="rounded-xl border border-slate-100 bg-slate-50 p-2.5 dark:border-slate-800 dark:bg-slate-900/40">
                            <span className="block text-[9px] font-extrabold uppercase text-slate-400">Day {day.day}</span>
                            <span className="mt-1 block text-xs font-extrabold text-slate-800 dark:text-slate-100">{Math.round(day.max_temp ?? day.temp)}°C</span>
                            <span className="mt-0.5 block text-[9.5px] font-semibold text-slate-500 dark:text-slate-400 line-clamp-1">{day.description}</span>
                            <span className="mt-1 block text-[9px] font-bold text-teal-600 dark:text-teal-400">Score {day.outdoor_score}/100</span>
                          </div>
                        ))}
                      </div>

                      {(activeTrip.weatherIntelligence.alerts || []).length > 0 && (
                        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-900/40 dark:bg-amber-950/20">
                          <p className="text-[10px] font-extrabold uppercase text-amber-700 dark:text-amber-300">Weather alerts</p>
                          <div className="mt-1 space-y-1">
                            {(activeTrip.weatherIntelligence.alerts || []).slice(0, 2).map((alert: any) => (
                              <p key={`${alert.type}-${alert.day}-${alert.title}`} className="text-[10.5px] font-semibold text-slate-700 dark:text-slate-300">
                                Day {alert.day}: {alert.title}. {alert.message}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}

                      {(activeTrip.weatherIntelligence.itinerary_suggestions || []).length > 0 && (
                        <div className="rounded-xl border border-sky-200 bg-sky-50 p-3 dark:border-sky-900/40 dark:bg-sky-950/20">
                          <p className="text-[10px] font-extrabold uppercase text-sky-700 dark:text-sky-300">Itinerary suggestions</p>
                          <div className="mt-1 space-y-1">
                            {(activeTrip.weatherIntelligence.itinerary_suggestions || []).slice(0, 2).map((item: any) => (
                              <p key={`${item.day}-${item.issue}`} className="text-[10.5px] font-semibold text-slate-700 dark:text-slate-300">
                                Day {item.day}: {item.suggestion}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

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

                </div>

                {/* Right Side: Widgets (Countdown, emergency list, weather converter) */}
                <div className="md:col-span-1 space-y-6">

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
                      {rateLoading ? (
                        <p className="text-[9px] text-slate-400 italic flex items-center gap-1">
                          <span className="animate-pulse">Loading exchange rate...</span>
                        </p>
                      ) : (
                        <p className="text-[9px] text-slate-400 italic">
                          Conversion rate: 1 USD ≈ {exchangeRate.toFixed(2)} INR
                          {lastRateUpdate && (
                            <span className="ml-1 text-slate-500">
                              (Updated: {lastRateUpdate})
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Interactive Nearby Explorer Widget (Radar & Map Compass for Hospitals, Shops, & Key Places) */}
                  <NearbyExplorerWidget
                    cityName={activeTrip.cityName}
                    emergencyContacts={activeTrip.emergencyContacts}
                  />

                </div>
              </motion.div>
            )}

            {/* TAB: TICKETS */}
            {activeTab === "Tickets" && (
              <motion.div
                key="tab-tickets"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-4xl mx-auto space-y-6 text-left"
              >
                <div className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm p-6 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                        <ActivityIcon className="w-5 h-5 text-teal-605" />
                        Live Transport Tickets
                      </h3>
                      <p className="text-xs text-slate-400 dark:text-slate-400 mt-1">
                        Scraped, ranked, and scored by our Transport Agent based on price, duration, and convenience.
                      </p>
                    </div>
                    {activeTrip?.transport_status?.last_updated && (
                      <span className="text-[10px] bg-slate-105 dark:bg-slate-800 px-2.5 py-1 rounded-full text-slate-500 font-medium">
                        Last updated: {new Date(activeTrip.transport_status.last_updated).toLocaleTimeString()}
                      </span>
                    )}
                  </div>

                  {activeTrip?.transport_status?.status === 'failed' && (
                    <div className="p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded-xl text-rose-600 dark:text-rose-450 text-xs flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                      <div>
                        <span className="font-bold">Scraping failed:</span> {activeTrip.transport_status.reason || 'Service temporarily unavailable'}
                      </div>
                    </div>
                  )}

                  {!activeTrip?.tickets || activeTrip.tickets.length === 0 ? (
                    <div className="py-10 text-center space-y-2">
                      <ActivityIcon className="w-12 h-12 text-slate-350 dark:text-slate-700 mx-auto animate-pulse" />
                      <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300">No Tickets Scraped</h4>
                      <p className="text-xs text-slate-400 dark:text-slate-500 max-w-sm mx-auto">
                        Ask the Smart Assistant to search for tickets (e.g. "Find flights and trains from Chennai to Bangalore for this trip") to trigger a live ticket search.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {activeTrip.tickets.map((ticket: any) => {
                        return (
                          <div key={ticket.id} className="p-4 bg-slate-50/50 dark:bg-slate-900/40 border border-slate-200/50 dark:border-slate-800/80 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:border-slate-350 dark:hover:border-slate-700">
                            <div className="flex items-start gap-3">
                              <div className="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/40 flex items-center justify-center shrink-0 border border-teal-150/35 dark:border-teal-900/20">
                                <span className="text-lg font-bold">
                                  {ticket.mode === 'Flight' ? '✈️' : ticket.mode === 'Train' ? '🚂' : ticket.mode === 'Car' ? '🚗' : '🚌'}
                                </span>
                              </div>
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                                    {ticket.carrier}
                                  </h4>
                                  <span className="text-[10px] bg-teal-100/60 dark:bg-teal-950/80 px-2 py-0.5 rounded-full text-teal-700 dark:text-teal-400 font-bold uppercase tracking-wide">
                                    {ticket.mode}
                                  </span>
                                  {ticket.score && (
                                    <span className="text-[10px] bg-amber-100/65 dark:bg-amber-950/80 px-2 py-0.5 rounded-full text-amber-700 dark:text-amber-400 font-bold">
                                      ⭐ Score: {ticket.score}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-450 dark:text-slate-400 mt-0.5 font-medium">
                                  {ticket.vehicle_type}
                                </p>
                                <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 font-medium">
                                  <span>⏰ Departs: <b className="text-slate-700 dark:text-slate-300">{ticket.departure}</b></span>
                                  <span>Arrives: <b className="text-slate-700 dark:text-slate-300">{ticket.arrival}</b></span>
                                  <span>Duration: <b className="text-slate-700 dark:text-slate-300">{ticket.duration}</b></span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center md:flex-col md:items-end justify-between border-t border-slate-100 dark:border-slate-800 md:border-none pt-3 md:pt-0 gap-2 shrink-0">
                              <div className="text-left md:text-right">
                                <p className="text-lg font-black text-emerald-600 dark:text-emerald-400 leading-none">
                                  ₹{parseFloat(ticket.price).toLocaleString('en-IN')}
                                </p>
                                <p className="text-[10px] text-slate-400 mt-1 font-semibold">
                                  via {ticket.booking_source}
                                </p>
                              </div>
                              <a
                                href={ticket.booking_url}
                                target="_blank"
                                rel="noreferrer"
                                className="px-4 py-2 bg-teal-650 hover:bg-teal-750 text-white text-xs font-bold rounded-xl flex items-center gap-1 transition-all shadow-sm hover-scale"
                              >
                                Book Ticket
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
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
                className={itineraryOnly ? "w-full" : "mx-auto max-w-6xl"}
              >
                <div className={`grid gap-3 ${itineraryOnly ? "lg:grid-cols-[minmax(0,1.25fr)_minmax(24rem,.75fr)]" : "lg:grid-cols-[7.5rem_minmax(0,1fr)_19rem]"}`}>
                  <aside className={itineraryOnly ? "lg:col-span-2" : "lg:sticky lg:top-4 lg:self-start"}>
                    {itineraryOnly && <p className="mb-2 text-left text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Choose a day</p>}
                    <div className={`flex gap-2 overflow-x-auto pb-1 ${itineraryOnly ? "rounded-2xl border border-slate-200/70 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-[#111827]" : "lg:flex-col lg:overflow-visible"}`}>
                    {itineraryDayEntries.map(([dayNum, list]) => {
                      const active = activeDayNum === dayNum;
                      return (
                        <button
                          key={dayNum}
                          onClick={() => setActiveItineraryDay(dayNum)}
                            className={`${itineraryOnly ? "min-w-[4.75rem] px-3 py-2 text-center" : "min-w-24 px-3 py-3 text-left shadow-sm"} shrink-0 rounded-xl border transition-all ${
                            active
                                ? "border-teal-600 bg-teal-600 text-white shadow-sm dark:border-teal-500 dark:bg-teal-500 dark:text-slate-950"
                                : "border-slate-200 bg-white text-slate-600 hover:border-teal-300 hover:bg-teal-50 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-teal-950/20"
                          }`}
                        >
                            <span className="block text-xs font-extrabold">Day {dayNum}</span>
                            {!itineraryOnly && <><span className="mt-1 block text-[10px] font-bold text-slate-400">{getItineraryDayDate(dayNum)}</span><span className="mt-2 inline-flex rounded-md bg-slate-50 px-2 py-0.5 text-[9px] font-extrabold text-slate-500 dark:bg-slate-900 dark:text-slate-400">{list.length} stops</span></>}
                        </button>
                      );
                    })}
                      <button
                        type="button"
                        onClick={() => triggerToast("Add stops from Hotels, Restaurants, or Attractions.", "info")}
                        className={`${itineraryOnly ? "min-w-[3rem] px-3 py-2 text-center" : "min-w-24 px-3 py-3 text-left"} shrink-0 rounded-xl border border-dashed border-slate-250 bg-white text-xs font-extrabold text-slate-500 transition hover:border-teal-300 hover:text-teal-700 dark:border-slate-800 dark:bg-[#111827] dark:text-slate-400`}
                      >
                        <Plus className={`${itineraryOnly ? "mx-auto" : "mb-1"} h-4 w-4`} />
                        {!itineraryOnly && "Add Day"}
                      </button>
                  </div>
                  </aside>

                  <section className={`${itineraryOnly ? "overflow-visible" : "overflow-hidden"} rounded-2xl border border-slate-200/70 bg-white shadow-sm dark:border-slate-800 dark:bg-[#111827]`}>
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/70 px-4 py-3 text-left dark:border-slate-850 dark:bg-slate-900/30">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-heading text-base font-extrabold text-slate-850 dark:text-slate-100">
                            Day {activeDayNum}
                          </h3>
                          <span className="text-xs font-bold text-slate-400">•</span>
                          <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
                            {getItineraryDayDate(activeDayNum, "full")}
                          </span>
                          <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-extrabold text-amber-600 dark:bg-amber-950/25 dark:text-amber-300">
                            {tempStr}
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] font-semibold text-slate-400">
                          Roadmap view for this day's schedule
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => triggerToast("Add stops from Hotels, Restaurants, or Attractions.", "info")}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-violet-200 bg-white px-3 py-2 text-[11px] font-extrabold text-violet-700 shadow-sm transition hover:bg-violet-50 dark:border-violet-900/60 dark:bg-slate-950 dark:text-violet-300"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Event
                      </button>
                    </div>

                    <AnimatePresence mode="wait">
                      <motion.div
                        key={`day-${activeDayNum}`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        className="relative px-4 py-4"
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDropOnDay(e, activeDayNum)}
                      >
                        <div className="absolute bottom-6 left-[5.85rem] top-6 hidden w-0.5 bg-slate-200 dark:bg-slate-800 sm:block" />
                        <div className="space-y-3">
                          {activeDayActivities.map((act) => {
                            const meta = getRoadmapMeta(act);
                            const DotIcon = meta.icon;
                            return (
                              <div
                                key={act.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, activeDayNum, act.id)}
                                onDragEnd={handleDragEnd}
                                onDragOver={handleDragOver}
                                onDrop={(e) => handleDrop(e, activeDayNum, act.id)}
                                className={`grid gap-3 transition-all duration-200 sm:grid-cols-[4.5rem_2.25rem_1fr] ${
                                  draggedActivity?.id === act.id ? "scale-[0.98] opacity-40" : ""
                                }`}
                              >
                                <div className="hidden pt-3 text-right text-[11px] font-bold text-slate-500 dark:text-slate-400 sm:block">
                                  {act.duration || act.time}
                                </div>
                                <div className="relative hidden justify-center pt-2 sm:flex">
                                  <span className={`z-10 flex h-9 w-9 items-center justify-center rounded-full text-white shadow-md ${meta.dot}`}>
                                    <DotIcon className="h-4.5 w-4.5" />
                                  </span>
                                </div>
                                <div className="min-w-0 space-y-2">
                                  {act.travel && act.category !== "Transport" && (
                                    <LocalTransportBookingCard
                                      mode={act.travel.mode}
                                      duration={act.travel.duration}
                                      distance={act.travel.distance}
                                      destination={`${act.title} ${act.location}`.trim()}
                                      compact
                                      inline={itineraryOnly}
                                    />
                                  )}
                                  <RoadmapEventCard
                                    activity={act}
                                    cityName={activeTrip.cityName}
                                    onDelete={(id: string) => handleDeleteActivity(activeDayNum, id)}
                                    onReplace={(id: string) => handleReplaceActivity(activeDayNum, id)}
                                    onViewOnMap={handleViewOnMap}
                                    compactTimeline={itineraryOnly}
                                  />
                                </div>
                              </div>
                            );
                          })}
                          <button
                            type="button"
                            onClick={() => triggerToast("Drag an item here after adding it from another tab.", "info")}
                            className="ml-0 w-full rounded-xl border border-dashed border-violet-300 bg-violet-50/40 px-4 py-3 text-[11px] font-extrabold text-violet-700 transition hover:bg-violet-50 dark:border-violet-900/60 dark:bg-violet-950/10 dark:text-violet-300 sm:ml-[6.75rem] sm:w-[calc(100%-6.75rem)]"
                          >
                            <Plus className="mr-1 inline h-3.5 w-3.5" />
                            Drag event here to add
                          </button>
                        </div>
                      </motion.div>
                    </AnimatePresence>
                  </section>

                  <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
                    <div className="overflow-hidden rounded-2xl border border-slate-200/70 bg-white shadow-sm dark:border-slate-800 dark:bg-[#111827]">
                      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                        <div>
                          <h3 className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800 dark:text-slate-100">
                            <MapPin className="h-4 w-4 text-teal-600" /> Day {activeDayNum} map
                          </h3>
                          <p className="mt-0.5 text-[9px] font-semibold text-slate-400">Select a stop to locate it</p>
                        </div>
                        <button type="button" onClick={() => setActiveTab("Map")} className="rounded-lg bg-teal-50 px-2.5 py-1.5 text-[9px] font-extrabold text-teal-700 hover:bg-teal-100 dark:bg-teal-950/30 dark:text-teal-300">
                          Open full map
                        </button>
                      </div>
                      {itineraryOnly && (
                        <div className="flex flex-wrap gap-1.5 border-b border-slate-100 bg-slate-50/70 p-2.5 dark:border-slate-800 dark:bg-slate-900/40">
                          <button type="button" onClick={() => setMapSearchQuery(activeTrip.cityName)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[9px] font-extrabold text-slate-600 hover:border-teal-400 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Center City</button>
                          <button type="button" onClick={() => setMapSearchQuery(`Hotels in ${activeTrip.cityName}`)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[9px] font-extrabold text-slate-600 hover:border-teal-400 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Show Stays</button>
                          <button type="button" onClick={() => setMapSearchQuery(`Restaurants in ${activeTrip.cityName}`)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[9px] font-extrabold text-slate-600 hover:border-teal-400 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Show Restaurants</button>
                          <button type="button" onClick={() => setMapSearchQuery(`Itinerary Day ${activeDayNum} in ${activeTrip.cityName}`)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[9px] font-extrabold text-slate-600 hover:border-teal-400 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">Show Itinerary</button>
                          <button type="button" onClick={() => setMapSearchQuery(`Route Day ${activeDayNum} in ${activeTrip.cityName}`)} className="inline-flex items-center gap-1 rounded-lg bg-teal-600 px-2.5 py-1.5 text-[9px] font-extrabold text-white hover:bg-teal-700"><Route className="h-3 w-3" /> Route 1–{activeDayActivities.length}</button>
                          <button
                            type="button"
                            onClick={handleApplyOptimizedRoute}
                            disabled={isApplyingOptimizedRoute || isLoadingRoute}
                            className="inline-flex items-center gap-1 rounded-lg border border-violet-200 bg-violet-50 px-2.5 py-1.5 text-[9px] font-extrabold text-violet-700 hover:bg-violet-100 disabled:cursor-wait disabled:opacity-60 dark:border-violet-900/60 dark:bg-violet-950/25 dark:text-violet-300"
                          >
                            <Zap className={`h-3 w-3 ${isApplyingOptimizedRoute || isLoadingRoute ? "animate-pulse" : ""}`} />
                            {isApplyingOptimizedRoute || isLoadingRoute ? "Optimizing…" : "Optimize Route"}
                          </button>
                        </div>
                      )}
                      <div className="relative h-[28rem] bg-slate-100 dark:bg-slate-900 lg:h-[calc(100vh-15rem)] lg:min-h-[32rem]">
                        {itineraryOnly ? <div ref={mapContainerRef} className="absolute inset-0 z-20 h-full w-full" /> : <iframe
                          title={`Map for itinerary day ${activeDayNum}`}
                          className="absolute inset-0 h-full w-full border-0"
                          src={`https://maps.google.com/maps?q=${encodeURIComponent(mapSearchQuery || activeDayActivities[0]?.location || activeDayActivities[0]?.title || activeTrip.cityName)}&t=&z=13&ie=UTF8&iwloc=&output=embed`}
                          loading="lazy"
                        />}
                        {itineraryOnly && !leafletLoaded && <div className="absolute inset-0 z-30 grid place-items-center bg-slate-100/90 text-xs font-bold text-slate-500 dark:bg-slate-900/90 dark:text-slate-400"><RefreshCw className="mr-2 inline h-4 w-4 animate-spin" />Loading interactive route map…</div>}
                      </div>
                      <div className="max-h-44 space-y-1 overflow-y-auto p-2">
                        {activeDayActivities.map((activity, index) => (
                          <button
                            key={`map-stop-${activity.id}`}
                            type="button"
                            onClick={() => setMapSearchQuery(`${activity.title} ${activity.location || activeTrip.cityName}`)}
                            className="flex w-full items-start gap-2 rounded-xl px-2.5 py-2 text-left transition hover:bg-teal-50 dark:hover:bg-teal-950/20"
                          >
                            <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-teal-600 text-[9px] font-extrabold text-white">{index + 1}</span>
                            <span className="min-w-0"><strong className="block truncate text-[10px] text-slate-700 dark:text-slate-200">{activity.title}</strong><small className="block truncate text-[9px] text-slate-400">{activity.location || activeTrip.cityName}</small></span>
                          </button>
                        ))}
                      </div>
                    </div>
                    {itineraryOnly && (
                      <div className="rounded-2xl border border-slate-200/70 bg-white p-4 text-left shadow-sm dark:border-slate-800 dark:bg-[#111827]">
                        <div className="mb-4 flex items-center justify-between gap-3">
                          <div>
                            <h3 className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800 dark:text-slate-100"><ActivityIcon className="h-4 w-4 text-teal-600" /> Trip History</h3>
                            <p className="mt-0.5 text-[9px] font-bold uppercase tracking-wider text-slate-400">Event logs · Audit trail</p>
                          </div>
                          <span className="rounded-full bg-slate-100 px-2 py-1 text-[9px] font-extrabold text-slate-500 dark:bg-slate-900 dark:text-slate-400">{activeTrip.historyTimeline.length} events</span>
                        </div>
                        <div className="relative max-h-72 space-y-4 overflow-y-auto border-l border-slate-200 pl-5 dark:border-slate-800">
                          {activeTrip.historyTimeline.map((event) => (
                            <div key={event.id} className="relative">
                              <span className="absolute -left-[1.47rem] top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-teal-500 dark:border-[#111827]" />
                              <p className="text-[10.5px] font-bold leading-relaxed text-slate-700 dark:text-slate-200">{event.action}</p>
                              <time className="mt-0.5 block text-[9px] font-semibold text-slate-400">{event.timestamp}</time>
                            </div>
                          ))}
                          {activeTrip.historyTimeline.length === 0 && <p className="text-[10px] font-semibold text-slate-400">No itinerary changes recorded yet.</p>}
                        </div>
                      </div>
                    )}
                  </aside>
                </div>
              </motion.div>
            )}

            {/* TAB: HOTELS ACCOMMODATION */}
            {activeTab === "Hotels" && (
              <motion.div
                key="tab-hotels"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-5 text-left"
              >
                <div className="rounded-2xl border border-slate-200/70 dark:border-slate-800/70 bg-white dark:bg-[#111827] p-4 shadow-sm">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-extrabold text-slate-800 dark:text-slate-100">
                        <Hotel className="h-4 w-4 text-teal-600" />
                        Hotels in {activeTrip?.cityName || "your destination"}
                      </div>
                      <p className="mt-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                        Found {effectiveHotels.length} hotels. Showing {filteredHotels.length} best match{filteredHotels.length !== 1 ? "es" : ""}.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <SlidersHorizontal className="h-3.5 w-3.5" />
                        <select
                          value={hotelBudgetFilter}
                          onChange={(event) => setHotelBudgetFilter(event.target.value as HotelBudgetFilter)}
                          className="bg-transparent outline-none"
                        >
                          <option value="all">All budgets</option>
                          <option value="budget">₹0-3000</option>
                          <option value="moderate">₹1500-5000</option>
                          <option value="luxury">₹5000+</option>
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <Star className="h-3.5 w-3.5 text-amber-500" />
                        <select
                          value={hotelRatingFilter}
                          onChange={(event) => setHotelRatingFilter(event.target.value as HotelRatingFilter)}
                          className="bg-transparent outline-none"
                        >
                          <option value="all">All ratings</option>
                          <option value="4">★★★★+</option>
                          <option value="3">★★★+</option>
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <BedDouble className="h-3.5 w-3.5 text-indigo-500" />
                        <select
                          value={hotelTypeFilter}
                          onChange={(event) => setHotelTypeFilter(event.target.value)}
                          className="bg-transparent outline-none"
                        >
                          <option value="all">All stays</option>
                          {HOTEL_TYPE_FILTERS.map((type) => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <ArrowUpDown className="h-3.5 w-3.5" />
                        <select
                          value={hotelSortMode}
                          onChange={(event) => setHotelSortMode(event.target.value as HotelSortMode)}
                          className="bg-transparent outline-none"
                        >
                          <option value="recommended">Recommended</option>
                          <option value="lowest">Lowest price</option>
                          <option value="highest">Highest price</option>
                          <option value="rating">Highest rating</option>
                          <option value="bestValue">Best value</option>
                        </select>
                      </label>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {HOTEL_AMENITY_FILTERS.map(({ key, label, icon: Icon }) => {
                      const active = hotelAmenityFilters.includes(key);
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => toggleHotelAmenityFilter(key)}
                          className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-[10.5px] font-bold transition ${
                            active
                              ? "border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300"
                              : "border-slate-200 bg-white text-slate-500 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400"
                          }`}
                        >
                          <Icon className="h-3.5 w-3.5" />
                          {label}
                        </button>
                      );
                    })}
                    {HOTEL_GUEST_FILTERS.map(({ key, label, icon: Icon }) => {
                      const active = hotelGuestFilters.includes(key);
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => toggleHotelGuestFilter(key)}
                          className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-[10.5px] font-bold transition ${
                            active
                              ? "border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300"
                              : "border-slate-200 bg-white text-slate-500 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400"
                          }`}
                        >
                          <Icon className="h-3.5 w-3.5" />
                          {label}
                        </button>
                      );
                    })}
                    {(hotelBudgetFilter !== "all" || hotelRatingFilter !== "all" || hotelTypeFilter !== "all" || hotelAmenityFilters.length > 0 || hotelGuestFilters.length > 0 || hotelSortMode !== "recommended") && (
                      <button
                        type="button"
                        onClick={clearHotelFilters}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[10.5px] font-bold text-slate-600 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
                      >
                        <X className="h-3.5 w-3.5" />
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                {filteredHotels.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/40 p-8 text-center">
                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200">No hotels match these filters.</p>
                    <button
                      type="button"
                      onClick={clearHotelFilters}
                      className="mt-3 rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-700"
                    >
                      Reset filters
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {visibleHotels.map((h, idx) => {
                  const isCurrent = idx === 0;
                  return (
                    <div key={h.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                      {/* Cover Photo */}
                      <div className="h-44 relative bg-slate-100 dark:bg-slate-800">
                      <img
                        src={resolvePlaceImageUrl(h.image, h.googlePhotoName, activeTrip?.cityName || "India", "hotel", h.name)}
                        loading="lazy"
                        decoding="async"
                        className="h-full w-full bg-slate-100 object-cover dark:bg-slate-900"
                        alt={h.name}
                        onError={(event) => {
                          const fallback = getFallbackImage(activeTrip?.cityName || "India", "hotel", h.name);
                          if (event.currentTarget.src !== fallback) event.currentTarget.src = fallback;
                        }}
                      />
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
                          <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-slate-50 px-2 py-0.5 text-[9.5px] font-bold text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                            {inferHotelType(h)}
                            {h.reviews ? ` · ${h.reviews} reviews` : ""}
                          </span>
                        </div>

                        {/* Amenities lists */}
                        <div className="flex flex-wrap gap-1">
                          {h.amenities.slice(0, 8).map((item) => (
                            <span key={item} className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">
                              {item}
                            </span>
                          ))}
                          {h.parking && (
                            <span className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">
                              Parking: {h.parking}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-850 text-xs">
                          <div className="font-bold text-teal-700 dark:text-teal-400">
                            <span>₹{h.pricePerNight} </span>
                            <span className="text-[10px] text-slate-400 font-semibold">/ night</span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {replacementTarget ? (
                              <button
                                onClick={() => handleReplaceWithItem(h, 'hotel')}
                                className="px-3 py-1.5 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 hover:bg-blue-100 rounded-xl text-[10.5px] font-bold hover-scale border border-blue-100 dark:border-blue-900/50"
                              >
                                Replace Activity
                              </button>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setItemToAdd({
                                      type: "hotel",
                                      id: h.id,
                                      name: h.name,
                                      image: h.image,
                                      googlePhotoName: h.googlePhotoName,
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
                              </>
                            )}
                            <a
                              href={h.bookingUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-750 text-white rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                            >
                              Book
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                  </div>
                )}

                {filteredHotels.length > visibleHotelCount && (
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={() => setVisibleHotelCount((count) => count + 6)}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-extrabold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-[#111827] dark:text-slate-200"
                    >
                      Load more hotels
                    </button>
                  </div>
                )}
              </motion.div>
            )}

            {/* TAB: RESTAURANTS */}
            {activeTab === "Restaurants" && (
              <motion.div
                key="tab-restaurants"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-5 text-left"
              >
                <div className="rounded-2xl border border-slate-200/70 dark:border-slate-800/70 bg-white dark:bg-[#111827] p-4 shadow-sm">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-extrabold text-slate-800 dark:text-slate-100">
                        <Utensils className="h-4 w-4 text-rose-600" />
                        Restaurants in {activeTrip?.cityName || "your destination"}
                      </div>
                      <p className="mt-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                        Found {effectiveRestaurants.length} restaurants. Showing {filteredRestaurants.length} match{filteredRestaurants.length !== 1 ? "es" : ""}.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <Utensils className="h-3.5 w-3.5 text-rose-500" />
                        <select value={restaurantCuisineFilter} onChange={(event) => setRestaurantCuisineFilter(event.target.value)} className="bg-transparent outline-none">
                          <option value="all">All cuisines</option>
                          {RESTAURANT_CUISINE_FILTERS.map((cuisine) => (
                            <option key={cuisine} value={cuisine}>{cuisine}</option>
                          ))}
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <DollarSign className="h-3.5 w-3.5 text-emerald-500" />
                        <select value={restaurantPriceFilter} onChange={(event) => setRestaurantPriceFilter(event.target.value as RestaurantPriceFilter)} className="bg-transparent outline-none">
                          <option value="all">All prices</option>
                          <option value="$">₹</option>
                          <option value="$$">₹₹</option>
                          <option value="$$$">₹₹₹</option>
                          <option value="$$$$">₹₹₹₹</option>
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <Star className="h-3.5 w-3.5 text-amber-500" />
                        <select value={restaurantRatingFilter} onChange={(event) => setRestaurantRatingFilter(event.target.value as RestaurantRatingFilter)} className="bg-transparent outline-none">
                          <option value="all">All ratings</option>
                          <option value="4">★★★★+</option>
                          <option value="3">★★★+</option>
                        </select>
                      </label>
                      <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                        <ArrowUpDown className="h-3.5 w-3.5" />
                        <select value={restaurantSortMode} onChange={(event) => setRestaurantSortMode(event.target.value as RestaurantSortMode)} className="bg-transparent outline-none">
                          <option value="recommended">Recommended</option>
                          <option value="rating">Highest rating</option>
                          <option value="reviews">Most reviewed</option>
                          <option value="lowest">Lowest price</option>
                          <option value="highest">Highest price</option>
                        </select>
                      </label>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {[...RESTAURANT_FOOD_FILTERS, ...RESTAURANT_DINING_FILTERS, ...RESTAURANT_AMENITY_FILTERS].map(({ key, label, icon: Icon }: any) => {
                      const kind = RESTAURANT_FOOD_FILTERS.some((rule) => rule.key === key) ? "food" : RESTAURANT_DINING_FILTERS.some((rule) => rule.key === key) ? "dining" : "amenity";
                      const active = kind === "food" ? restaurantFoodFilters.includes(key) : kind === "dining" ? restaurantDiningFilters.includes(key) : restaurantAmenityFilters.includes(key);
                      return (
                        <button
                          key={`${kind}-${key}`}
                          type="button"
                          onClick={() => toggleRestaurantFilter(kind as "food" | "dining" | "amenity", key)}
                          className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-[10.5px] font-bold transition ${
                            active
                              ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300"
                              : "border-slate-200 bg-white text-slate-500 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400"
                          }`}
                        >
                          <Icon className="h-3.5 w-3.5" />
                          {label}
                        </button>
                      );
                    })}
                    {(restaurantCuisineFilter !== "all" || restaurantPriceFilter !== "all" || restaurantRatingFilter !== "all" || restaurantSortMode !== "recommended" || restaurantFoodFilters.length > 0 || restaurantDiningFilters.length > 0 || restaurantAmenityFilters.length > 0) && (
                      <button type="button" onClick={clearRestaurantFilters} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[10.5px] font-bold text-slate-600 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
                        <X className="h-3.5 w-3.5" />
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                {filteredRestaurants.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/40 p-8 text-center">
                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200">No restaurants match these filters.</p>
                    <button type="button" onClick={clearRestaurantFilters} className="mt-3 rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-700">
                      Reset filters
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {visibleRestaurants.map((r) => (
                  <div key={r.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                    <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
                      <img
                        src={resolvePlaceImageUrl(r.image, r.googlePhotoName, activeTrip?.cityName || "India", "restaurant", r.name)}
                        loading="lazy"
                        decoding="async"
                        className="h-full w-full bg-slate-100 object-cover dark:bg-slate-900"
                        alt={r.name}
                        onError={(event) => {
                          const fallback = getFallbackImage(activeTrip?.cityName || "India", "restaurant", r.name);
                          if (event.currentTarget.src !== fallback) event.currentTarget.src = fallback;
                        }}
                      />
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
                        <p className="text-[10px] text-slate-400 mt-0.5">Price range: {r.priceTier} · {r.distanceFromHotel}</p>
                        {r.reviews ? <p className="text-[9.5px] font-bold text-slate-400 mt-0.5">{r.reviews} reviews</p> : null}
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {(r.diningOptions || []).slice(0, 4).map((option) => (
                          <span key={option} className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">
                            {option}
                          </span>
                        ))}
                        {r.goodForChildren && <span className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">Family</span>}
                        {Object.values(r.parking || {}).some(Boolean) && <span className="px-2 py-0.5 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded text-[9.5px] text-slate-500 dark:text-slate-400">Parking</span>}
                      </div>

                      {getRestaurantReasons(r).length > 0 && (
                        <div className="rounded-xl bg-rose-50/50 dark:bg-rose-950/15 border border-rose-100/70 dark:border-rose-900/30 p-2">
                          <p className="text-[9px] font-extrabold uppercase text-rose-500">Recommended because</p>
                          <div className="mt-1 space-y-0.5">
                            {getRestaurantReasons(r).slice(0, 3).map((reason) => (
                              <p key={reason} className="flex items-start gap-1.5 text-[9.5px] font-semibold text-slate-600 dark:text-slate-300">
                                <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-rose-500" />
                                {reason}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-850">
                        <span className="text-[9px] font-bold text-slate-450 dark:text-slate-500 uppercase">
                          {r.reservationAvailable ? "Tables Available" : "Walk-in Only"}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {replacementTarget ? (
                            <button
                              onClick={() => handleReplaceWithItem(r, 'restaurant')}
                              className="px-3 py-1.5 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 hover:bg-blue-100 rounded-xl text-[10px] font-bold hover-scale border border-blue-100 dark:border-blue-900/50"
                            >
                              Replace Activity
                            </button>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setItemToAdd({
                                    type: "restaurant",
                                    id: r.id,
                                    name: r.name,
                                    image: r.image,
                                    googlePhotoName: r.googlePhotoName,
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
                              {r.mapsUrl && (
                                <a href={r.mapsUrl} target="_blank" rel="noreferrer" className="px-3 py-1.5 border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10px] font-bold hover-scale">
                                  Navigate
                                </a>
                              )}
                              {r.website && (
                                <a href={r.website} target="_blank" rel="noreferrer" className="px-3 py-1.5 border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10px] font-bold hover-scale">
                                  Menu
                                </a>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                  </div>
                )}

                {filteredRestaurants.length > visibleRestaurantCount && (
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={() => setVisibleRestaurantCount((count) => count + 6)}
                      className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-extrabold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-[#111827] dark:text-slate-200"
                    >
                      Load more restaurants
                    </button>
                  </div>
                )}
              </motion.div>
            )}


{activeTab === "Attractions" && (
  <motion.div
    key="tab-attractions"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="space-y-5 text-left"
  >
    <div className="rounded-2xl border border-slate-200/70 dark:border-slate-800/70 bg-white dark:bg-[#111827] p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-extrabold text-slate-800 dark:text-slate-100">
            <Landmark className="h-4 w-4 text-sky-600" />
            Discover places in {activeTrip?.cityName || "your destination"}
          </div>
          <p className="mt-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            Found {effectiveAttractions.length} places. Showing {filteredAttractions.length} match{filteredAttractions.length !== 1 ? "es" : ""}.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
            <Camera className="h-3.5 w-3.5 text-sky-500" />
            <select value={attractionCategoryFilter} onChange={(event) => setAttractionCategoryFilter(event.target.value)} className="bg-transparent outline-none">
              <option value="all">All types</option>
              {ATTRACTION_CATEGORY_FILTERS.map((category) => (
                <option key={category.key} value={category.key}>{category.label}</option>
              ))}
            </select>
          </label>
          <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
            <Star className="h-3.5 w-3.5 text-amber-500" />
            <select value={attractionRatingFilter} onChange={(event) => setAttractionRatingFilter(event.target.value as AttractionRatingFilter)} className="bg-transparent outline-none">
              <option value="all">All ratings</option>
              <option value="4">★★★★+</option>
              <option value="3">★★★+</option>
            </select>
          </label>
          <label className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-[11px] font-bold text-slate-600 dark:text-slate-300">
            <ArrowUpDown className="h-3.5 w-3.5" />
            <select value={attractionSortMode} onChange={(event) => setAttractionSortMode(event.target.value as AttractionSortMode)} className="bg-transparent outline-none">
              <option value="recommended">Recommended</option>
              <option value="rating">Highest rating</option>
              <option value="reviews">Most reviewed</option>
              <option value="nearby">Nearest to hotel</option>
            </select>
          </label>
          {(attractionCategoryFilter !== "all" || attractionRatingFilter !== "all" || attractionSortMode !== "recommended") && (
            <button type="button" onClick={clearAttractionFilters} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[10.5px] font-bold text-slate-600 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
              <X className="h-3.5 w-3.5" />
              Clear
            </button>
          )}
        </div>
      </div>
    </div>

    {filteredAttractions.length === 0 ? (
      <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/40 p-8 text-center">
        <p className="text-sm font-bold text-slate-700 dark:text-slate-200">No attractions match these filters.</p>
        <button type="button" onClick={clearAttractionFilters} className="mt-3 rounded-xl bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-700">
          Reset filters
        </button>
      </div>
    ) : (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    {visibleAttractions.map((p) => {
      const img = resolvePlaceImageUrl(p.image, (p as any).googlePhotoName, activeTrip?.cityName || "India", "attraction", p.name, 800, 800);
      return (
        <div key={p.id} className="bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
          <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
            {img ? (
              <img
                src={img}
                loading="lazy"
                decoding="async"
                className="h-full w-full bg-slate-100 object-cover dark:bg-slate-900"
                alt={p.name}
                onError={(event) => {
                  const fallback = getFallbackImage(activeTrip?.cityName || "India", "attraction", p.name);
                  if (event.currentTarget.src !== fallback) event.currentTarget.src = fallback;
                }}
              />
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
              <span className="mt-1 inline-flex rounded-full bg-sky-50 px-2 py-0.5 text-[9.5px] font-bold text-sky-700 dark:bg-sky-950/25 dark:text-sky-300">
                {inferAttractionCategory(p)}
                {(p.ratingCount || p.reviews) ? ` · ${p.ratingCount || p.reviews} reviews` : ""}
              </span>
            </div>
            {p.description && (
              <p className="text-[10.5px] text-slate-500 dark:text-slate-400 line-clamp-2">{p.description}</p>
            )}
            {getAttractionReasons(p).length > 0 && (
              <div className="rounded-xl bg-sky-50/50 dark:bg-sky-950/15 border border-sky-100/70 dark:border-sky-900/30 p-2">
                <p className="text-[9px] font-extrabold uppercase text-sky-500">Recommended because</p>
                <div className="mt-1 space-y-0.5">
                  {getAttractionReasons(p).slice(0, 3).map((reason) => (
                    <p key={reason} className="flex items-start gap-1.5 text-[9.5px] font-semibold text-slate-600 dark:text-slate-300">
                      <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-sky-500" />
                      {reason}
                    </p>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-end pt-1 border-t border-slate-100 dark:border-slate-850">
              {/* NOTE: no "Tables Available" / "Reserve Table" here (attractions) */}
              {replacementTarget ? (
                <button
                  onClick={() => handleReplaceWithItem(p, 'attraction')}
                  className="px-3 py-1.5 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 hover:bg-blue-100 rounded-xl text-[10px] font-bold border border-blue-100 dark:border-blue-900/50"
                >
                  Replace Activity
                </button>
              ) : (
                <div className="flex flex-wrap justify-end gap-1.5">
                  <button
                    onClick={() => {
                      setItemToAdd({
                        type: "attraction",
                        id: p.id,
                        name: p.name,
                        image: img || "",
                        googlePhotoName: (p as any).googlePhotoName || null,
                        rating: p.rating ?? 4.5,
                        location: p.address || "",
                      });
                      setIsAddItineraryOpen(true);
                    }}
                    className="px-3 py-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded-xl text-[10px] font-bold border border-teal-100 dark:border-teal-900/50"
                  >
                    Add
                  </button>
                  {(p.mapsUrl || p.address) && (
                    <a href={p.mapsUrl || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${p.name} ${p.address || activeTrip.cityName}`)}`} target="_blank" rel="noreferrer" className="px-3 py-1.5 border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10px] font-bold">
                      Navigate
                    </a>
                  )}
                  {p.wikiUrl && (
                    <a href={p.wikiUrl} target="_blank" rel="noreferrer" className="px-3 py-1.5 border border-slate-205 dark:border-slate-805 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10px] font-bold">
                      Wiki
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    })}
      </div>
    )}

    {filteredAttractions.length > visibleAttractionCount && (
      <div className="flex justify-center">
        <button type="button" onClick={() => setVisibleAttractionCount((count) => count + 6)} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-extrabold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-800 dark:bg-[#111827] dark:text-slate-200">
          Load more places
        </button>
      </div>
    )}
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
                    <button
                      onClick={() => setMapSearchQuery(`Itinerary in ${activeTrip.cityName}`)}
                      className="px-3 py-1 rounded-lg border border-slate-150 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-[10px] font-bold text-slate-500 dark:text-slate-400 cursor-pointer hover:border-teal-500 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-all"
                    >
                      Show Itinerary
                    </button>
                  </div>
                  <div className="w-full flex flex-wrap gap-2 pt-1 text-[9.5px] font-bold text-slate-400">
                    <span className="inline-flex items-center gap-1"><span className="w-4 h-4 rounded-full bg-purple-600 text-white grid place-items-center text-[9px]">I</span> Itinerary hotels, restaurants & places</span>
                    <span className="inline-flex items-center gap-1"><span className="w-4 h-4 rounded-full bg-red-600 text-white grid place-items-center text-[9px]">H</span> Other stays</span>
                    <span className="inline-flex items-center gap-1"><span className="w-4 h-4 rounded-full bg-orange-500 text-white grid place-items-center text-[9px]">R</span> Other restaurants</span>
                    <span className="inline-flex items-center gap-1"><span className="w-4 h-4 rounded-full bg-blue-600 text-white grid place-items-center text-[9px]">A</span> Other attractions</span>
                  </div>
                </div>

                <div className="h-[450px] w-full relative rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 flex flex-col shadow-inner z-10">
                  {isLoadingRoute && (
                    <div className="absolute inset-0 bg-white/60 dark:bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-30">
                      <div className="flex flex-col items-center gap-2">
                        <svg className="animate-spin h-8 w-8 text-teal-600" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span className="text-xs font-bold text-slate-600 dark:text-slate-400">Loading map route...</span>
                      </div>
                    </div>
                  )}
                  <div
                    ref={mapContainerRef}
                    className="w-full h-full rounded-3xl absolute inset-0 z-20"
                    style={{ minHeight: "450px", height: "450px" }}
                  />
                  <iframe
                    title="Interactive Destination Map"
                    className="w-full h-full rounded-3xl absolute inset-0 z-10 border-0"
                    src={`https://maps.google.com/maps?q=${encodeURIComponent(mapSearchQuery || activeTrip?.cityName || "India")}&t=&z=13&ie=UTF8&iwloc=&output=embed`}
                    loading="lazy"
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
                  <p className="text-xs text-slate-400 mt-0.5">
                    Progress status based on {activeTrip.budget || "Moderate"} Tier calculations for {activeTrip.durationDays || 1} day{(activeTrip.durationDays || 1) > 1 ? "s" : ""}.
                  </p>
                </div>

                {/* Progress bars categories */}
                <div className="space-y-4 pt-1">
                  {(() => {
                    const expenseConfig: Record<string, { label: string; color: string; capMultiplier: number }> = {
                      Hotel:     { label: "Hotel Accommodations", color: "bg-teal-500",   capMultiplier: 2 },
                      Food:      { label: "Dining & Food",        color: "bg-rose-500",   capMultiplier: 1.67 },
                      Transport: { label: "Transport",            color: "bg-blue-500",   capMultiplier: 1.67 },
                      Tickets:   { label: "Tickets & Entry",      color: "bg-purple-500", capMultiplier: 3.2 },
                      Shopping:  { label: "Shopping",             color: "bg-amber-500",  capMultiplier: 2.5 },
                      Misc:      { label: "Miscellaneous",        color: "bg-slate-400",  capMultiplier: 2 },
                    };

                    const expenses = activeTrip.expenses && activeTrip.expenses.length > 0
                      ? activeTrip.expenses
                      : [
                          { id: "e1", category: "Hotel" as const,     amount: 0, label: "No data" },
                          { id: "e2", category: "Food" as const,      amount: 0, label: "No data" },
                          { id: "e3", category: "Transport" as const, amount: 0, label: "No data" },
                          { id: "e4", category: "Tickets" as const,   amount: 0, label: "No data" },
                          { id: "e5", category: "Shopping" as const,  amount: 0, label: "No data" },
                        ];

                    return expenses.map((item) => {
                      const cfg = expenseConfig[item.category] || { label: item.category, color: "bg-slate-400", capMultiplier: 2 };
                      const cap = Math.round(item.amount * cfg.capMultiplier);
                      const percentage = cap > 0 ? Math.min(100, (item.amount / cap) * 100) : 0;
                      return (
                        <div key={item.id} className="space-y-1">
                          <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                            <span>{cfg.label}</span>
                            <span>₹{item.amount.toLocaleString("en-IN")} / ₹{cap.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-105 bg-slate-100 dark:bg-slate-850 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${percentage}%` }}
                              className={`h-full ${cfg.color} rounded-full`}
                            />
                          </div>
                          <p className="text-[10px] text-slate-400 dark:text-slate-500">{item.label}</p>
                        </div>
                      );
                    });
                  })()}

                  <hr className="border-slate-100 dark:border-slate-850" />

                  <div className="flex justify-between items-center text-xs font-extrabold pt-1">
                    <span className="text-slate-500 dark:text-slate-400">Total Estimated Expenses</span>
                    <span className="text-lg text-emerald-600 dark:text-emerald-450">
                      ₹{(activeTrip.estimatedCost || 0).toLocaleString("en-IN")} INR
                    </span>
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
      {activeTab === "Itinerary" && !itineraryOnly && (
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

            {/* Save Trip */}
            <button
              onClick={() => setIsSaveOpen(true)}
              className="flex-1 sm:flex-initial px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 text-xs font-bold flex items-center justify-center gap-1.5 hover-scale"
            >
              <Save className="w-4 h-4 text-teal-605" />
              <span>Save</span>
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
      <div className={`fixed right-5 z-45 sm:right-6 ${itineraryOnly ? "bottom-24" : "bottom-24 sm:bottom-20"}`}>
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

      {/* Replacement Choice Dialog */}
      {isReplaceDialogOpen && replacementTarget && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                Replace Activity
              </h3>
              <button
                onClick={() => setIsReplaceDialogOpen(false)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <div className="mb-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Current activity:</p>
              <p className="font-bold text-slate-800 dark:text-slate-100">{replacementTarget.activity.title}</p>
            </div>

            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Choose what type of replacement you'd like:
            </p>

            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={() => handleReplaceChoice('hotel')}
                className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-teal-500 dark:hover:border-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-all"
              >
                <div className="w-12 h-12 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center">
                  <span className="text-2xl">🏨</span>
                </div>
                <div className="text-left">
                  <p className="font-bold text-slate-800 dark:text-slate-100">Hotels</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Choose accommodation</p>
                </div>
              </button>

              <button
                onClick={() => handleReplaceChoice('restaurant')}
                className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-rose-500 dark:hover:border-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all"
              >
                <div className="w-12 h-12 rounded-lg bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center">
                  <span className="text-2xl">🍽️</span>
                </div>
                <div className="text-left">
                  <p className="font-bold text-slate-800 dark:text-slate-100">Restaurants</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Choose dining options</p>
                </div>
              </button>

              <button
                onClick={() => handleReplaceChoice('attraction')}
                className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-sky-500 dark:hover:border-sky-400 hover:bg-sky-50 dark:hover:bg-sky-950/20 transition-all"
              >
                <div className="w-12 h-12 rounded-lg bg-sky-100 dark:bg-sky-900/30 flex items-center justify-center">
                  <span className="text-2xl">📍</span>
                </div>
                <div className="text-left">
                  <p className="font-bold text-slate-800 dark:text-slate-100">Attractions</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Choose places to visit</p>
                </div>
              </button>
            </div>

            <button
              onClick={() => setIsReplaceDialogOpen(false)}
              className="mt-6 w-full py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 font-bold transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {pendingHotelImpact && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl dark:bg-[#111827]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-extrabold text-amber-700 dark:bg-amber-950/30 dark:text-amber-300">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Route impact detected
                </div>
                <h3 className="mt-3 text-base font-extrabold text-slate-850 dark:text-slate-100">
                  {pendingHotelImpact.hotel.name} may slow down your itinerary
                </h3>
                <p className="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">
                  This hotel is farther from your planned attraction circuit than the best route-friendly stay.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPendingHotelImpact(null)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                <span className="block text-[9px] font-extrabold uppercase text-slate-400">Avg distance</span>
                <span className="mt-1 block text-sm font-extrabold text-slate-800 dark:text-slate-100">
                  {pendingHotelImpact.averageDistanceKm.toFixed(1)} km
                </span>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                <span className="block text-[9px] font-extrabold uppercase text-slate-400">Extra travel</span>
                <span className="mt-1 block text-sm font-extrabold text-slate-800 dark:text-slate-100">
                  +{pendingHotelImpact.extraTravelMin} min/day
                </span>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                <span className="block text-[9px] font-extrabold uppercase text-slate-400">Taxi impact</span>
                <span className="mt-1 block text-sm font-extrabold text-slate-800 dark:text-slate-100">
                  +₹{pendingHotelImpact.taxiCostPerDay}/day
                </span>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                <span className="block text-[9px] font-extrabold uppercase text-slate-400">Walkability</span>
                <span className="mt-1 block text-sm font-extrabold text-slate-800 dark:text-slate-100">
                  {pendingHotelImpact.walkability}
                </span>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
              <p className="text-[10px] font-extrabold uppercase text-slate-400">Why this warning?</p>
              <ul className="mt-2 space-y-1.5">
                {pendingHotelImpact.reasons.map((reason) => (
                  <li key={reason} className="flex items-start gap-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-500" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
              {pendingHotelImpact.betterHotelName && (
                <p className="mt-3 rounded-lg bg-teal-50 px-3 py-2 text-[11px] font-bold text-teal-700 dark:bg-teal-950/25 dark:text-teal-300">
                  Route-friendly option: {pendingHotelImpact.betterHotelName}
                  {pendingHotelImpact.betterHotelDistanceKm ? `, about ${pendingHotelImpact.betterHotelDistanceKm.toFixed(1)} km average from stops.` : "."}
                </p>
              )}
            </div>

            <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
              <button
                type="button"
                onClick={() => applyHotelSelection(pendingHotelImpact.hotel.id)}
                className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-extrabold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
              >
                Use Anyway
              </button>
              {pendingHotelImpact.betterHotelName ? (
                <button
                  type="button"
                  onClick={() => {
                    const better = effectiveHotels.find((hotel) => hotel.name === pendingHotelImpact.betterHotelName);
                    if (better) applyHotelSelection(better.id);
                  }}
                  className="rounded-xl bg-teal-600 px-3 py-2 text-xs font-extrabold text-white hover:bg-teal-700"
                >
                  Choose Recommended
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setPendingHotelImpact(null)}
                  className="rounded-xl bg-teal-600 px-3 py-2 text-xs font-extrabold text-white hover:bg-teal-700"
                >
                  Review Hotels
                </button>
              )}
              <button
                type="button"
                onClick={() => applyHotelSelection(pendingHotelImpact.hotel.id, "rebuild")}
                className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-extrabold text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-950"
              >
                Rebuild Route
              </button>
            </div>
          </div>
        </div>
      )}

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
