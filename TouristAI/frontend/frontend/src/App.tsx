import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { TravelPlannerProvider } from "./context/TravelPlannerContext";

import Navigation from "./components/layout/Navigation";
import TopBar from "./components/layout/TopBar";

import Home from "./pages/Home";
import AIChat from "./pages/AIChat";
import TripPlanner from "./pages/TripPlanner";
import SavedTrips from "./pages/SavedTrips";
import Profile from "./pages/Profile";

import TrainSearchHome from "./pages/TrainSearchHome";
import TrainSearchResults from "./pages/TrainSearchResults";

import FlightSearchHome from "./pages/FlightSearchHome";
import FlightSearchResults from "./pages/FlightSearchResults";

import BusSearchHome from "./pages/BusSearchHome";
import BusSearchResults from "./pages/BusSearchResults";

function AppContent() {
  return (
    <div className="h-screen w-screen overflow-hidden flex bg-slate-50 dark:bg-[#0b0f19] text-slate-800 dark:text-slate-200">
      
      {/* Navigation */}
      <Navigation />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        
        {/* Header */}
        <TopBar onMenuClick={() => {}} />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto pb-16 sm:pb-0">
          <Routes>
            {/* Existing Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<AIChat />} />
            <Route path="/planner" element={<TripPlanner />} />
            <Route path="/saved" element={<SavedTrips />} />
            <Route path="/profile" element={<Profile />} />

            {/* Train Routes */}
            <Route path="/trains" element={<TrainSearchHome />} />
            <Route
              path="/trains/between/:from/:to"
              element={<TrainSearchResults />}
            />

            {/* Flight Routes */}
            <Route path="/flights" element={<FlightSearchHome />} />
            <Route
              path="/flights/between/:from/:to"
              element={<FlightSearchResults />}
            />

            {/* Bus Routes */}
            <Route path="/buses" element={<BusSearchHome />} />
            <Route
              path="/buses/between/:from/:to"
              element={<BusSearchResults />}
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <TravelPlannerProvider>
      <Router>
        <AppContent />
      </Router>
    </TravelPlannerProvider>
  );
}

export default App;