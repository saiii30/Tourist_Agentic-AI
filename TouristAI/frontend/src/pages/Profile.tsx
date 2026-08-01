import React, { useEffect, useState } from "react";
import {
  Accessibility,
  Bell,
  Brain,
  Check,
  Globe,
  Hotel,
  Moon,
  Save,
  Sun,
  Train,
  User
} from "lucide-react";
import {
  DEFAULT_TRAVEL_PROFILE,
  useTravelPlanner
} from "../context/TravelPlannerContext";
import type { TravelProfile } from "../context/TravelPlannerContext";

const travelStyles = [
  "Nature",
  "Adventure",
  "Culture",
  "Spiritual",
  "Wildlife",
  "Beaches",
  "Food",
  "Shopping",
  "Family",
  "Photography"
];

const accessibilityOptions = [
  "Wheelchair Accessible",
  "Senior Citizen",
  "Traveling with Kids",
  "Pregnant Traveler",
  "Medical Needs"
];

const behaviorOptions = [
  "Usually books in advance",
  "Likes spontaneous trips",
  "Prefers public transport",
  "Likes rental cars",
  "Enjoys walking",
  "Prefers guided tours"
];

const notificationOptions = [
  "Weather alerts",
  "Flight/train reminders",
  "Hotel check-in reminders",
  "Traffic alerts",
  "Budget alerts"
];

type MultiKey =
  | "favoriteTravelStyles"
  | "accessibilityNeeds"
  | "travelBehavior"
  | "notificationPreferences";

const Field: React.FC<{
  label: string;
  children: React.ReactNode;
}> = ({ label, children }) => (
  <label className="block">
    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1.5">
      {label}
    </span>
    {children}
  </label>
);

const inputClass =
  "w-full px-3 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-700 dark:text-slate-250 outline-none focus:border-teal-500 font-medium";

export const Profile: React.FC = () => {
  const { theme, toggleTheme, travelProfile, setTravelProfile } = useTravelPlanner();
  const [profileDraft, setProfileDraft] = useState<TravelProfile>({
    ...DEFAULT_TRAVEL_PROFILE,
    ...travelProfile
  });
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    setProfileDraft({ ...DEFAULT_TRAVEL_PROFILE, ...travelProfile });
  }, [travelProfile]);

  const updateProfileField = (key: keyof TravelProfile, value: any) => {
    setProfileDraft((prev) => ({ ...prev, [key]: value }));
  };

  const toggleListValue = (key: MultiKey, value: string) => {
    setProfileDraft((prev) => {
      const current = prev[key] || [];
      const next = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];
      return { ...prev, [key]: next };
    });
  };

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    setTravelProfile(profileDraft);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  const chipGroup = (key: MultiKey, options: string[]) => (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = profileDraft[key]?.includes(option);
        return (
          <button
            key={option}
            type="button"
            onClick={() => toggleListValue(key, option)}
            className={`px-3 py-1.5 rounded-full text-[11px] font-bold border transition-colors ${
              active
                ? "bg-teal-600 text-white border-teal-600"
                : "bg-white dark:bg-slate-950 text-slate-600 dark:text-slate-350 border-slate-200 dark:border-slate-800 hover:border-teal-400"
            }`}
          >
            {option}
          </button>
        );
      })}
    </div>
  );

  return (
    <form onSubmit={handleProfileSave} className="space-y-6 pb-20 sm:pb-8 text-left max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading text-xl sm:text-2xl font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <User className="w-6 h-6 text-teal-600" />
            Profile & Travel Memory
          </h2>
          <p className="text-xs text-slate-450 dark:text-slate-400 mt-1">
            Save stable preferences so TouristAI asks fewer repeated questions.
          </p>
        </div>
        <button
          type="submit"
          className="px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm"
        >
          {isSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{isSaved ? "Saved" : "Save Profile"}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <aside className="lg:col-span-1 space-y-4">
          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-teal-50 dark:bg-teal-950/30 border border-teal-100 dark:border-teal-900 flex items-center justify-center">
                <User className="w-7 h-7 text-teal-600" />
              </div>
              <div className="min-w-0">
                <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100 truncate">
                  {profileDraft.fullName || "Traveler"}
                </h3>
                <p className="text-[10px] font-bold text-teal-600 uppercase tracking-widest">
                  {profileDraft.budgetType} Explorer
                </p>
              </div>
            </div>
            <div className="mt-5 space-y-2 text-xs">
              <div className="flex justify-between gap-3">
                <span className="text-slate-400 font-semibold">Home City</span>
                <span className="font-bold text-slate-700 dark:text-slate-300 truncate">{profileDraft.homeCity || "Not set"}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-slate-400 font-semibold">Transport</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">{profileDraft.preferredTransport}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-slate-400 font-semibold">Food</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">{profileDraft.preferredFood}</span>
              </div>
            </div>
          </div>

          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Brain className="w-4.5 h-4.5 text-violet-500" />
              AI Memory
            </h3>
            <label className="flex items-start justify-between gap-4 cursor-pointer">
              <span>
                <span className="block text-xs font-bold text-slate-700 dark:text-slate-300">Use profile in chat</span>
                <span className="block text-[10px] text-slate-400 mt-1">
                  Planning uses these preferences only when details are missing.
                </span>
              </span>
              <input
                type="checkbox"
                checked={profileDraft.aiMemoryEnabled}
                onChange={(e) => updateProfileField("aiMemoryEnabled", e.target.checked)}
                className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer mt-0.5"
              />
            </label>
          </div>

          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              {theme === "light" ? <Moon className="w-4.5 h-4.5" /> : <Sun className="w-4.5 h-4.5" />}
              Interface
            </h3>
            <button
              type="button"
              onClick={toggleTheme}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-bold flex items-center justify-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
            >
              {theme === "light" ? "Switch to Dark Theme" : "Switch to Light Theme"}
            </button>
          </div>
        </aside>

        <main className="lg:col-span-2 space-y-6">
          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <User className="w-4.5 h-4.5 text-teal-600" />
              Registration Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <Field label="Full Name">
                <input className={inputClass} value={profileDraft.fullName} onChange={(e) => updateProfileField("fullName", e.target.value)} />
              </Field>
              <Field label="Email">
                <input type="email" className={inputClass} value={profileDraft.email} onChange={(e) => updateProfileField("email", e.target.value)} />
              </Field>
              <Field label="Mobile Number">
                <input className={inputClass} value={profileDraft.mobileNumber} onChange={(e) => updateProfileField("mobileNumber", e.target.value)} />
              </Field>
              <Field label="Country / Region">
                <input className={inputClass} value={profileDraft.countryRegion} onChange={(e) => updateProfileField("countryRegion", e.target.value)} />
              </Field>
            </div>
          </section>

          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Globe className="w-4.5 h-4.5 text-sky-500" />
              Personal Preferences
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <Field label="Date of Birth">
                <input type="date" className={inputClass} value={profileDraft.dateOfBirth || ""} onChange={(e) => updateProfileField("dateOfBirth", e.target.value)} />
              </Field>
              <Field label="Home City">
                <input className={inputClass} value={profileDraft.homeCity} onChange={(e) => updateProfileField("homeCity", e.target.value)} />
              </Field>
              <Field label="Preferred Language">
                <select className={inputClass} value={profileDraft.preferredLanguage} onChange={(e) => updateProfileField("preferredLanguage", e.target.value)}>
                  <option>English</option>
                  <option>Tamil</option>
                  <option>Hindi</option>
                  <option>Spanish</option>
                </select>
              </Field>
              <Field label="Currency">
                <select className={inputClass} value={profileDraft.currency} onChange={(e) => updateProfileField("currency", e.target.value)}>
                  <option>INR</option>
                  <option>USD</option>
                  <option>EUR</option>
                  <option>GBP</option>
                </select>
              </Field>
            </div>
          </section>

          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Train className="w-4.5 h-4.5 text-indigo-500" />
              Travel Preferences
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <Field label="Budget Type">
                <select className={inputClass} value={profileDraft.budgetType} onChange={(e) => updateProfileField("budgetType", e.target.value)}>
                  <option>Low</option>
                  <option>Moderate</option>
                  <option>Luxury</option>
                </select>
              </Field>
              <Field label="Preferred Transport">
                <select className={inputClass} value={profileDraft.preferredTransport} onChange={(e) => updateProfileField("preferredTransport", e.target.value)}>
                  <option>Flight</option>
                  <option>Train</option>
                  <option>Bus</option>
                  <option>Car</option>
                </select>
              </Field>
              <Field label="Preferred Hotel">
                <select className={inputClass} value={profileDraft.preferredHotel} onChange={(e) => updateProfileField("preferredHotel", e.target.value)}>
                  <option>Homestay</option>
                  <option>Hostel</option>
                  <option>3-Star</option>
                  <option>4-Star</option>
                  <option>5-Star</option>
                  <option>Resort</option>
                </select>
              </Field>
              <Field label="Preferred Food">
                <select className={inputClass} value={profileDraft.preferredFood} onChange={(e) => updateProfileField("preferredFood", e.target.value)}>
                  <option>Vegetarian</option>
                  <option>Vegan</option>
                  <option>Jain</option>
                  <option>Halal</option>
                  <option>Non-Vegetarian</option>
                </select>
              </Field>
            </div>
            <Field label="Favorite Travel Styles">
              {chipGroup("favoriteTravelStyles", travelStyles)}
            </Field>
          </section>

          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Accessibility className="w-4.5 h-4.5 text-emerald-500" />
              Accessibility & Companions
            </h3>
            <Field label="Special Needs">
              {chipGroup("accessibilityNeeds", accessibilityOptions)}
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <Field label="Usually Travels With">
                <select className={inputClass} value={profileDraft.companionType} onChange={(e) => updateProfileField("companionType", e.target.value)}>
                  <option>Solo</option>
                  <option>Couple</option>
                  <option>Family</option>
                  <option>Friends</option>
                  <option>Business</option>
                </select>
              </Field>
              <Field label="Average Group Size">
                <select className={inputClass} value={profileDraft.averageGroupSize} onChange={(e) => updateProfileField("averageGroupSize", e.target.value)}>
                  <option>1</option>
                  <option>2</option>
                  <option>4</option>
                  <option>6+</option>
                </select>
              </Field>
            </div>
            <Field label="Travel Behavior">
              {chipGroup("travelBehavior", behaviorOptions)}
            </Field>
          </section>

          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Hotel className="w-4.5 h-4.5 text-violet-500" />
              Booking Preferences
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <Field label="Favorite Airline">
                <input className={inputClass} value={profileDraft.favoriteAirline} onChange={(e) => updateProfileField("favoriteAirline", e.target.value)} />
              </Field>
              <Field label="Preferred Train Class">
                <input className={inputClass} value={profileDraft.preferredTrainClass} onChange={(e) => updateProfileField("preferredTrainClass", e.target.value)} />
              </Field>
              <Field label="Hotel Chain Preference">
                <input className={inputClass} value={profileDraft.hotelChainPreference} onChange={(e) => updateProfileField("hotelChainPreference", e.target.value)} />
              </Field>
              <Field label="Car Rental Preference">
                <input className={inputClass} value={profileDraft.carRentalPreference} onChange={(e) => updateProfileField("carRentalPreference", e.target.value)} />
              </Field>
            </div>
          </section>

          <section className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Bell className="w-4.5 h-4.5 text-amber-500" />
              Notifications
            </h3>
            <Field label="Travel Alerts">
              {chipGroup("notificationPreferences", notificationOptions)}
            </Field>
          </section>
        </main>
      </div>
    </form>
  );
};

export default Profile;
