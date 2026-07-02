import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Send, Mic, Image, Sparkles, Bot, User, Cloud, Hotel, Utensils, Compass, ArrowRight, Loader, Info, Calendar, DollarSign, Users, Sun } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTravelPlanner } from "../context/TravelPlannerContext";
import type { TripDetails } from "../context/TravelPlannerContext";

// Import all dialogs to support buttons inside chat attachment card
import { ModifyDrawer } from "../components/dialogs/ModifyDrawer";
import { SaveDialog } from "../components/dialogs/SaveDialog";
import { CalendarSyncDialog } from "../components/dialogs/CalendarSyncDialog";
import { RegenerateDialog } from "../components/dialogs/RegenerateDialog";

export const AIChat: React.FC = () => {
  const navigate = useNavigate();
  const { chatMessages, askAIChat, isLoadingChat, setActiveTrip, saveTrip } = useTravelPlanner();
  
  const [question, setQuestion] = useState("");
  const [isListening, setIsListening] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // States to handle overlays inside chat card actions
  const [targetTripCard, setTargetTripCard] = useState<TripDetails | null>(null);
  const [isModifyOpen, setIsModifyOpen] = useState(false);
  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [isRegenOpen, setIsRegenOpen] = useState(false);

  // Toast alert status state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Auto-scroll on messages addition
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isLoadingChat]);

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleSend = async (text?: string) => {
    const queryText = text || question;
    if (!queryText.trim()) return;
    
    setQuestion("");
    await askAIChat(queryText);
  };

  const getAgentBadge = (route: string) => {
    switch (route) {
      case "weather":
        return { label: "Weather Agent", icon: Cloud, color: "text-sky-505 text-sky-600 bg-sky-50 dark:bg-sky-950/20 border-sky-100 dark:border-sky-900/30" };
      case "hotel":
        return { label: "Hotel Agent", icon: Hotel, color: "text-amber-605 text-amber-600 bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30" };
      case "restaurant":
        return { label: "Restaurant Agent", icon: Utensils, color: "text-rose-605 text-rose-600 bg-rose-50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30" };
      case "nearby":
        return { label: "Attractions Agent", icon: Compass, color: "text-purple-605 text-purple-600 bg-purple-50 dark:bg-purple-950/20 border-purple-100 dark:border-purple-900/30" };
      case "budget":
        return { label: "Budget Agent", icon: DollarSign, color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/30" };
      default:
        return { label: "General Chat", icon: Bot, color: "text-slate-500 bg-slate-50 dark:bg-slate-900 border-slate-100 dark:border-slate-800" };
    }
  };

  // Card button trigger actions
  const handleLoadTrip = (trip: TripDetails) => {
    setActiveTrip(trip);
    navigate("/planner");
  };

  const handleCardModify = (trip: TripDetails) => {
    setActiveTrip(trip);
    setTargetTripCard(trip);
    setIsModifyOpen(true);
  };

  const handleCardRegen = (trip: TripDetails) => {
    setActiveTrip(trip);
    setTargetTripCard(trip);
    setIsRegenOpen(true);
  };

  const handleCardSave = (trip: TripDetails) => {
    setActiveTrip(trip);
    setTargetTripCard(trip);
    setIsSaveOpen(true);
  };

  const handleSaveOnly = () => {
    if (targetTripCard) {
      saveTrip(targetTripCard);
      setIsSaveOpen(false);
      triggerToast("Trip Saved Successfully!");
    }
  };

  const handleSaveAndSync = () => {
    if (targetTripCard) {
      saveTrip(targetTripCard);
      setIsSaveOpen(false);
      setTimeout(() => {
        setIsSyncOpen(true);
      }, 300);
    }
  };

  const handleRegenerateItinerary = (_keeps: { budget: boolean; style: boolean; interests: boolean; duration: boolean }) => {
    if (!targetTripCard) return;
    triggerToast("Itinerary Successfully Regenerated!");
  };

  // Web Speech API Microphone listener
  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice Speech Recognition is not supported by this browser version.");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    setIsListening(true);

    recognition.onresult = (event: any) => {
      const speechToText = event.results[0][0].transcript;
      setQuestion(speechToText);
      setIsListening(false);
      setTimeout(() => handleSend(speechToText), 800);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const suggestedPrompts = [
    "Plan a 3-day cultural trip to Madurai",
    "Find romantic restaurants in Chennai Marina",
    "4 days adventure itinerary for Goa beach",
    "Weather report for Paris this week"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50/50 dark:bg-[#0b0f19] relative">
      
      {/* 1. Chat Dialog Log */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 no-scrollbar">
        
        {chatMessages.length === 0 ? (
          /* Landing Empty State */
          <div className="h-full flex flex-col items-center justify-center max-w-md mx-auto text-center space-y-5 py-12">
            <div className="w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-950/20 border border-teal-100/50 dark:border-teal-900/30 flex items-center justify-center text-teal-605">
              <Bot className="w-8 h-8 text-teal-600 dark:text-teal-405 animate-pulse" />
            </div>
            <div>
              <h2 className="font-heading text-lg sm:text-xl font-extrabold text-slate-800 dark:text-slate-100">
                Explore with AI Travel Core
              </h2>
              <p className="text-xs text-slate-455 dark:text-slate-400 mt-1 leading-relaxed">
                Describe your dream location, custom budgets, and durations. Our multi-agent travel core will assemble your itineraries instantly.
              </p>
            </div>

            {/* Suggested prompts list */}
            <div className="w-full space-y-2 pt-2 text-left">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">
                Suggested Prompts
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestedPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="p-3 text-xs text-slate-650 dark:text-slate-355 font-semibold text-left border border-slate-200/60 dark:border-slate-850 bg-white dark:bg-[#111827] rounded-xl hover:border-teal-500 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-all hover-scale"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Active Chat Conversation Log */
          <div className="space-y-6 max-w-3xl mx-auto pb-4">
            {chatMessages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div key={idx} className={`flex gap-3 text-left ${isUser ? "justify-end" : "justify-start"}`}>
                  
                  {/* Assistant Avatar */}
                  {!isUser && (
                    <div className="w-8.5 h-8.5 rounded-xl bg-teal-600 text-white flex items-center justify-center flex-shrink-0 mt-1 shadow-sm shadow-teal-500/10">
                      <Sparkles className="w-4.5 h-4.5" />
                    </div>
                  )}

                  {/* Message bubble wrapper */}
                  <div className="space-y-3.5 max-w-[85%] sm:max-w-[78%]">
                    
                    {/* ChatGPT-style bubbles */}
                    <div
                      className={`relative p-4 rounded-2xl shadow-sm border leading-relaxed ${
                        isUser
                          ? "bg-teal-600 border-teal-650 text-white rounded-br-none"
                          : "bg-white dark:bg-[#111827] border-slate-200/60 dark:border-slate-800 text-slate-700 dark:text-slate-200 rounded-bl-none"
                      }`}
                    >
                      {/* Message Content */}
                      <p
                        className="text-xs sm:text-sm whitespace-pre-line font-medium leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: msg.text
                            .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-900 dark:text-white">$1</strong>')
                            .replace(/^# (.*)/gm, '<h3 class="font-heading text-sm sm:text-base font-bold text-slate-800 dark:text-slate-100 mt-2 mb-1">$1</h3>')
                            .replace(/^## (.*)/gm, '<h4 class="font-heading text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-100 mt-2 mb-1">$1</h4>')
                            .replace(/^- (.*)/gm, '<li class="ml-4 list-disc text-xs">$1</li>')
                        }}
                      />

                      {/* Timestamps */}
                      <span className={`block text-[9px] mt-2 text-right ${isUser ? "text-slate-200/80" : "text-slate-400"}`}>
                        {msg.timestamp || "10:15 AM"}
                      </span>

                      {/* Enabled Agent Chips */}
                      {msg.routes && msg.routes.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                          {msg.routes.map((rt) => {
                            const badge = getAgentBadge(rt);
                            const Icon = badge.icon;
                            return (
                              <span
                                key={rt}
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${badge.color}`}
                              >
                                <Icon className="w-3 h-3" />
                                {badge.label}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Premium Inline Trip Summary Card Attachment */}
                    {msg.tripCard && (
                      <motion.div
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="rounded-2xl overflow-hidden border border-slate-200/60 dark:border-slate-800/85 bg-white dark:bg-[#111827] shadow-md text-left"
                      >
                        {/* City Cover Image */}
                        <div className="h-32 relative bg-slate-100 dark:bg-slate-800">
                          <img
                            src={msg.tripCard.bannerImage}
                            alt={msg.tripCard.cityName}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/85 to-transparent" />
                          <div className="absolute bottom-3 left-4 text-white text-left">
                            <span className="text-[9px] font-bold text-teal-400 bg-teal-950/60 backdrop-blur-sm px-2.5 py-0.5 rounded border border-teal-500/20 uppercase tracking-wider mb-1 inline-block">
                              Itinerary Deck
                            </span>
                            <h4 className="font-heading font-extrabold text-sm sm:text-base tracking-tight leading-none">
                              {msg.tripCard.cityName}
                            </h4>
                          </div>
                        </div>

                        {/* Itinerary specifications Grid */}
                        <div className="p-4 grid grid-cols-2 gap-3 text-xs border-b border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/10">
                          <div className="flex items-center gap-1.5 font-semibold text-slate-600 dark:text-slate-350">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.durationDays} Days Plan</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-600 dark:text-slate-350">
                            <Users className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.travelersCount} Travelers</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-650 dark:text-slate-350">
                            <DollarSign className="w-4 h-4 text-slate-400" />
                            <span>{msg.tripCard.budget} Budget</span>
                          </div>
                          <div className="flex items-center gap-1.5 font-semibold text-slate-650 dark:text-slate-350">
                            <Sun className="w-4 h-4 text-amber-500" />
                            <span>Sunny Forecast</span>
                          </div>
                          <div className="col-span-2 flex items-center gap-1 font-bold text-teal-700 dark:text-teal-405 text-xs pt-1 border-t border-slate-200/40 dark:border-slate-800/40">
                            <span>Estimated cost: </span>
                            <span>₹{typeof msg.tripCard.estimatedCost === 'number' ? msg.tripCard.estimatedCost.toLocaleString('en-IN') : msg.tripCard.estimatedCost} INR</span>
                          </div>
                        </div>

                        {/* Summary Deck Actions */}
                        <div className="p-3 flex flex-wrap items-center gap-1.5 justify-end bg-white dark:bg-[#111827]">
                          <button
                            onClick={() => handleCardModify(msg.tripCard!)}
                            className="px-3 py-1.5 border border-slate-205 dark:border-slate-800 text-slate-600 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                          >
                            Modify
                          </button>
                          
                          <button
                            onClick={() => handleCardRegen(msg.tripCard!)}
                            className="px-3 py-1.5 border border-slate-205 dark:border-slate-800 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                          >
                            Regenerate
                          </button>

                          <button
                            onClick={() => handleCardSave(msg.tripCard!)}
                            className="px-3 py-1.5 border border-slate-205 dark:border-slate-800 text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-900 rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale"
                          >
                            Save
                          </button>

                          <button
                            onClick={() => handleLoadTrip(msg.tripCard!)}
                            className="px-3.5 py-1.5 bg-teal-650 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-[10.5px] font-bold flex items-center gap-1 hover-scale shadow-sm"
                          >
                            View Itinerary
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* User Avatar */}
                  {isUser && (
                    <div className="w-8.5 h-8.5 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                      <User className="w-4.5 h-4.5" />
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}

        {/* AI Typing / Agent Core Thinking Loader */}
        {isLoadingChat && (
          <div className="flex gap-3 text-left max-w-3xl mx-auto">
            <div className="w-8 h-8 rounded-xl bg-teal-650 bg-teal-600 text-white shadow-sm flex items-center justify-center flex-shrink-0 mt-1">
              <Sparkles className="w-4 h-4 animate-spin-slow" />
            </div>
            
            <div className="bg-white dark:bg-[#111827] border border-slate-200/50 dark:border-slate-800/80 p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-3">
              <Loader className="w-4.5 h-4.5 text-teal-650 text-teal-600 animate-spin" />
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  AI Travel Agent is planning...
                </span>
                
                {/* Typing Streaming Indicators */}
                <div className="flex items-center gap-1">
                  {[0, 1, 2].map((dot) => (
                    <span
                      key={dot}
                      className="w-1.5 h-1.5 rounded-full bg-teal-600 dark:bg-teal-405 animate-bounce"
                      style={{ animationDelay: `${dot * 0.15}s` }}
                    />
                  ))}
                  <span className="text-[10px] text-slate-400 ml-1 font-bold animate-pulse">Streaming reply</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* 2. Bottom Chat Input Panel */}
      <div className="bg-white dark:bg-[#111827] border-t border-slate-200/60 dark:border-slate-800/60 p-4 flex-shrink-0">
        <div className="max-w-3xl mx-auto space-y-3">
          
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-3 py-2 rounded-xl focus-within:border-teal-500 focus-within:ring-1 focus-within:ring-teal-500/20 transition-all duration-150 shadow-inner">
            
            {/* Attachment mock */}
            <button
              className="p-2 rounded-lg text-slate-400 hover:text-slate-655 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Upload Image File"
            >
              <Image className="w-4.5 h-4.5" />
            </button>

            {/* Input field */}
            <input
              type="text"
              placeholder={isListening ? "Listening... Speak your request" : "Describe where to go, budget, sights..."}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              className="flex-1 bg-transparent border-none outline-none text-xs sm:text-sm text-slate-700 dark:text-slate-305 placeholder-slate-405 font-medium"
            />

            {/* Web Speech voice */}
            <button
              onClick={toggleListening}
              className={`p-2 rounded-lg transition-colors ${
                isListening
                  ? "bg-red-50 text-red-500 dark:bg-red-950/20 animate-pulse"
                  : "text-slate-400 hover:text-slate-655 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
              aria-label="Speech to Text"
            >
              <Mic className="w-4.5 h-4.5" />
            </button>

            {/* Send */}
            <button
              onClick={() => handleSend()}
              className="p-2 rounded-lg bg-teal-650 bg-teal-600 text-white hover:bg-teal-700 transition-colors shadow-sm"
              aria-label="Send query"
            >
              <Send className="w-4 h-4" />
            </button>

          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-400 px-1 font-semibold">
            <span>{isListening ? "🎤 Web Speech Listening Active" : "Google Cloud powered travel agents"}</span>
            <span className="flex items-center gap-1">
              <Info className="w-3.5 h-3.5" />
              Markdown details supported
            </span>
          </div>

        </div>
      </div>

      {/* ── MODAL WORKFLOW DRAWERS ── */}
      {targetTripCard && (
        <>
          <ModifyDrawer
            isOpen={isModifyOpen}
            onClose={() => setIsModifyOpen(false)}
            onSaveSuccess={() => triggerToast("Itinerary modifications saved!")}
          />

          <SaveDialog
            isOpen={isSaveOpen}
            onClose={() => setIsSaveOpen(false)}
            onSaveOnly={handleSaveOnly}
            onSaveAndSync={handleSaveAndSync}
          />

          <CalendarSyncDialog
            isOpen={isSyncOpen}
            onClose={() => setIsSyncOpen(false)}
            tripName={targetTripCard.cityName}
          />

          <RegenerateDialog
            isOpen={isRegenOpen}
            onClose={() => setIsRegenOpen(false)}
            onRegenerate={handleRegenerateItinerary}
          />
        </>
      )}

      {/* ── TOAST NOTIFICATION ALERTS ── */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-55 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-xs font-bold text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 border-slate-850 dark:border-slate-200/50"
          >
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
export default AIChat;
