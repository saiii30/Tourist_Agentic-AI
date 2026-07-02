import React, { useState } from "react";
import { User, Globe, Bell, Moon, Sun, LogOut, Check, Save } from "lucide-react";
import { useTravelPlanner } from "../context/TravelPlannerContext";

export const Profile: React.FC = () => {
  const { theme, toggleTheme } = useTravelPlanner();
  
  // Local profile state inputs
  const [displayName, setDisplayName] = useState("Sarah Jenkins");
  const [email, setEmail] = useState("sarah.j@google.com");
  const [homeAirport, setHomeAirport] = useState("San Francisco International (SFO)");
  const [language, setLanguage] = useState("English (US)");
  
  // Notification switches
  const [pushNotif, setPushNotif] = useState(true);
  const [emailSync, setEmailSync] = useState(true);
  
  // Connected account sync
  const [googleConnected, setGoogleConnected] = useState(true);

  // Success indicator toast local simulation
  const [isSaved, setIsSaved] = useState(false);

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="space-y-6 pb-20 sm:pb-8 text-left max-w-3xl mx-auto">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-xl sm:text-2xl font-extrabold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <User className="w-6 h-6 text-teal-605" />
            Profile & Settings
          </h2>
          <p className="text-xs text-slate-450 dark:text-slate-400 mt-1">
            Manage your personal traveler details, notification hubs, and synced calendars.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Side: Avatar Card */}
        <div className="md:col-span-1 p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm flex flex-col items-center text-center space-y-4">
          <div className="relative">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80"
              alt="Profile Avatar"
              className="w-24 h-24 rounded-full object-cover border-4 border-slate-100 dark:border-slate-800 shadow-md"
            />
            <span className="absolute bottom-1 right-1 w-5 h-5 bg-emerald-500 border-2 border-white dark:border-[#111827] rounded-full" />
          </div>
          <div>
            <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-250">
              {displayName}
            </h3>
            <p className="text-[10px] font-semibold text-teal-605 dark:text-teal-400 uppercase tracking-widest mt-0.5">
              Premium Explorer
            </p>
          </div>

          <div className="w-full pt-4 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 font-semibold">Home Airport</span>
              <span className="font-bold text-slate-700 dark:text-slate-350 truncate max-w-[120px]">{homeAirport.split(" ").slice(-1)[0]}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 font-semibold">Tier Status</span>
              <span className="font-bold text-emerald-600">Active</span>
            </div>
          </div>

          <button className="w-full py-2 border border-slate-200 dark:border-slate-800 hover:bg-red-50 dark:hover:bg-red-950/20 text-slate-500 hover:text-red-600 dark:hover:text-red-400 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 hover-scale">
            <LogOut className="w-4 h-4" />
            Log Out Account
          </button>
        </div>

        {/* Right Side: Settings Forms */}
        <div className="md:col-span-2 space-y-6">
          
          {/* 1. Personal Information */}
          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <User className="w-4.5 h-4.5 text-teal-605" />
              Personal Information
            </h3>
            <form onSubmit={handleProfileSave} className="space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-355 outline-none focus:border-teal-500 font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Primary Home Airport
                </label>
                <input
                  type="text"
                  value={homeAirport}
                  onChange={(e) => setHomeAirport(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none focus:border-teal-500 font-medium"
                />
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[10px] text-slate-400 italic">
                  * All changes are synced securely to tourist cloud databases
                </span>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 hover-scale shadow-sm"
                >
                  {isSaved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                  <span>{isSaved ? "Saved!" : "Save Changes"}</span>
                </button>
              </div>
            </form>
          </div>

          {/* 2. Preferences & Theme */}
          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Globe className="w-4.5 h-4.5 text-teal-655 text-sky-500" />
              App Preferences
            </h3>
            
            <div className="space-y-3">
              {/* Language Selection */}
              <div className="flex items-center justify-between text-xs py-1">
                <div className="text-left">
                  <p className="font-bold text-slate-700 dark:text-slate-300">Display Language</p>
                  <p className="text-[10px] text-slate-450 dark:text-slate-500">Sets interface translated texts</p>
                </div>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-slate-700 dark:text-slate-350 outline-none"
                >
                  <option value="English (US)" className="dark:bg-[#111827]">English (US)</option>
                  <option value="Tamil" className="dark:bg-[#111827]">Tamil (தமிழ்)</option>
                  <option value="Spanish" className="dark:bg-[#111827]">Spanish (Español)</option>
                  <option value="Hindi" className="dark:bg-[#111827]">Hindi (हिन्दी)</option>
                </select>
              </div>

              <hr className="border-slate-100 dark:border-slate-850" />

              {/* Theme selection toggle */}
              <div className="flex items-center justify-between text-xs py-1">
                <div className="text-left">
                  <p className="font-bold text-slate-700 dark:text-slate-300">Interface Dark Mode</p>
                  <p className="text-[10px] text-slate-450 dark:text-slate-500">Sets color palette light / dark overrides</p>
                </div>
                <button
                  onClick={toggleTheme}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-bold flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
                >
                  {theme === "light" ? (
                    <>
                      <Moon className="w-3.5 h-3.5" />
                      <span>Dark Theme</span>
                    </>
                  ) : (
                    <>
                      <Sun className="w-3.5 h-3.5" />
                      <span>Light Theme</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 3. Notifications & Integrations */}
          <div className="p-5 bg-white dark:bg-[#111827] border border-slate-200/60 dark:border-slate-800/60 rounded-2xl shadow-sm space-y-4">
            <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <Bell className="w-4.5 h-4.5 text-teal-605" />
              Sync & Notifications
            </h3>

            <div className="space-y-3">
              {/* Push notifications */}
              <label className="flex items-center justify-between cursor-pointer select-none">
                <div className="text-left">
                  <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Push Notifications</p>
                  <p className="text-[10px] text-slate-400">Receive schedule updates or flight notifications</p>
                </div>
                <input
                  type="checkbox"
                  checked={pushNotif}
                  onChange={(e) => setPushNotif(e.target.checked)}
                  className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                />
              </label>

              <hr className="border-slate-100 dark:border-slate-850" />

              {/* Email synchronization */}
              <label className="flex items-center justify-between cursor-pointer select-none">
                <div className="text-left">
                  <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Email Itinerary Summaries</p>
                  <p className="text-[10px] text-slate-400">Receive formatted PDF details on email saves</p>
                </div>
                <input
                  type="checkbox"
                  checked={emailSync}
                  onChange={(e) => setEmailSync(e.target.checked)}
                  className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                />
              </label>

              <hr className="border-slate-100 dark:border-slate-850" />

              {/* Google Sync Connected Account Toggle */}
              <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-850 flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300">
                    <Globe className="w-4 h-4 text-teal-605" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="text-[11px] font-bold text-slate-700 dark:text-slate-300">Google Account Sync</p>
                    <p className="text-[9.5px] text-slate-400 truncate">Connected to sarah.j@google.com</p>
                  </div>
                </div>
                
                <input
                  type="checkbox"
                  checked={googleConnected}
                  onChange={(e) => setGoogleConnected(e.target.checked)}
                  className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                />
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
export default Profile;
