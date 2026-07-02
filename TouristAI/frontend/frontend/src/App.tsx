import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { TravelPlannerProvider } from "./context/TravelPlannerContext";
import Navigation from "./components/layout/Navigation";
import TopBar from "./components/layout/TopBar";
import Home from "./pages/Home";
import AIChat from "./pages/AIChat";
import TripPlanner from "./pages/TripPlanner";
import SavedTrips from "./pages/SavedTrips";
import Profile from "./pages/Profile";

function AppContent() {
  return (
    <div className="h-screen w-screen overflow-hidden flex bg-slate-50 dark:bg-[#0b0f19] text-slate-800 dark:text-slate-200">
      
      {/* 1. Responsive Navigation System (Left Sidebar, Tablet Rail, Mobile Bottom Nav) */}
      <Navigation />

      {/* 2. Main Page content area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        
        {/* Top Header bar */}
        <TopBar onMenuClick={() => {}} />

        {/* Scrollable interior page body */}
        <main className="flex-1 overflow-y-auto pb-16 sm:pb-0">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<AIChat />} />
            <Route path="/planner" element={<TripPlanner />} />
            <Route path="/saved" element={<SavedTrips />} />
            <Route path="/profile" element={<Profile />} />
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
