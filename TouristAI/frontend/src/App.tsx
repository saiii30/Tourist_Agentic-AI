import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { TravelPlannerProvider } from "./context/TravelPlannerContext";
import Navigation from "./components/layout/Navigation";
import TopBar from "./components/layout/TopBar";
import UnifiedHome from "./pages/UnifiedHome";
import TripPlanner from "./pages/TripPlanner";
import SavedTrips from "./pages/SavedTrips";
import Profile from "./pages/Profile";
import TrainSearchHome from "./pages/TrainSearchHome";
import TrainSearchResults from "./pages/TrainSearchResults";
import FlightSearchHome from "./pages/FlightSearchHome";
import FlightSearchResults from "./pages/FlightSearchResults";
import BusSearchHome from "./pages/BusSearchHome";
import BusSearchResults from "./pages/BusSearchResults";
import LocalAssist from "./pages/LocalAssist";
import Auth from "./pages/Auth";
import ProtectedRoute from "./components/auth/ProtectedRoute";

function AppContent() {
  const location = useLocation();
  const isAuthPage = location.pathname === "/auth";

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-slate-50 dark:bg-[#0b0f19] text-slate-850 dark:text-slate-200">

      {/* 1. Responsive Navigation System (Left Sidebar, Tablet Rail, Mobile Bottom Nav) */}
      {!isAuthPage && <Navigation />}

      {/* 2. Main Page content area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">

        {/* Top Header bar */}
        {!isAuthPage && <TopBar onMenuClick={() => { }} />}

        {/* Scrollable interior page body */}
        <main className={`flex-1 overflow-y-auto ${isAuthPage ? "" : "pb-16 sm:pb-0"}`}>
          <Routes>
            <Route path="/" element={<UnifiedHome />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/chat" element={<Navigate to="/" replace />} />
            <Route path="/planner" element={<TripPlanner key="trip-planner" />} />
            <Route path="/itinerary" element={<TripPlanner key="itinerary-list" itineraryOnly />} />
            <Route path="/saved" element={<ProtectedRoute><SavedTrips /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/local-assist" element={<LocalAssist />} />
            <Route path="/trains" element={<TrainSearchHome />} />
            <Route path="/trains/between/:from/:to" element={<TrainSearchResults />} />
            <Route path="/flights" element={<FlightSearchHome />} />
            <Route path="/flights/between/:from/:to" element={<FlightSearchResults />} />
            <Route path="/buses" element={<BusSearchHome />} />
            <Route path="/buses/between/:from/:to" element={<BusSearchResults />} />
            <Route path="*" element={<Navigate to="/" replace />} />
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
