import React, { useState } from "react";
import { Sparkles, X, Send, Bot, Check, AlertCircle, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTravelPlanner } from "../../context/TravelPlannerContext";
import type { Activity } from "../../context/TravelPlannerContext";

interface FloatingAICopilotProps {
  isOpen: boolean;
  onClose: () => void;
  onApplySuccess?: (message: string) => void;
}

interface PreviewChange {
  title: string;
  description: string;
  diffText: string;
  effect: () => void;
}

export const FloatingAICopilot: React.FC<FloatingAICopilotProps> = ({ isOpen, onClose, onApplySuccess }) => {
  const { activeTrip, updateActiveTrip } = useTravelPlanner();
  const [prompt, setPrompt] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [preview, setPreview] = useState<PreviewChange | null>(null);

  const suggestedPrompts = [
    "Replace today's hotel with budget resort",
    "Reduce budget to Budget",
    "Make itinerary kid-friendly",
    "Add shopping stops to Day 1",
    "Find vegetarian restaurants nearby",
    "Add museum visit to afternoon slots"
  ];

  const handleSendPrompt = async (textText?: string) => {
    const input = textText || prompt;
    if (!input.trim() || !activeTrip) return;

    setPrompt("");
    setIsThinking(true);
    setPreview(null);

    // Simulate AI Copilot thinking delay
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsThinking(false);

    const lowerInput = input.toLowerCase();

    if (lowerInput.includes("budget") || lowerInput.includes("reduce")) {
      setPreview({
        title: "Adjust Budget Category",
        description: "Change itinerary budget settings from Moderate to Budget Tier.",
        diffText: "💰 Budget Tier: Moderate ➔ Budget (Est. Cost: ₹8,450 ➔ ₹4,000)",
        effect: () => {
          updateActiveTrip((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              budget: "Budget",
              estimatedCost: 4000,
              historyTimeline: [
                {
                  id: `hist-cop-${Date.now()}`,
                  action: "📝 Budget reduced via AI Copilot",
                  timestamp: "Just now",
                  iconName: "edit"
                },
                ...prev.historyTimeline
              ]
            };
          });
        }
      });
    } else if (lowerInput.includes("kid") || lowerInput.includes("child")) {
      setPreview({
        title: "Kid-Friendly Activities Swap",
        description: "Swap sightseeing spots for theme parks and children's science museums.",
        diffText: "📍 Day 2 Afternoon: Artisan Marketplace ➔ Heritage Kids Fun Center Visit",
        effect: () => {
          updateActiveTrip((prev) => {
            if (!prev) return null;
            const updated = { ...prev.itinerary };
            updated[2] = updated[2].map(act => {
              if (act.slot === "Afternoon Activity") {
                return {
                  ...act,
                  title: "Heritage Kids Fun Center & Toy Museum",
                  description: "Features hand-crafted toy exhibits, block building areas, and clay modeling activities for children.",
                  location: "Children's Park Square",
                  image: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=400&q=80"
                };
              }
              return act;
            });
            return {
              ...prev,
              itinerary: updated,
              travelStyle: "Family",
              historyTimeline: [
                {
                  id: `hist-cop-${Date.now()}`,
                  action: "👨‍👩‍👧‍👦 Itinerary made Kid-Friendly by Copilot",
                  timestamp: "Just now",
                  iconName: "smile"
                },
                ...prev.historyTimeline
              ]
            };
          });
        }
      });
    } else if (lowerInput.includes("shopping") || lowerInput.includes("shop")) {
      setPreview({
        title: "Inject Shopping Stops",
        description: "Append traditional weaver markets to Day 1 evening slot.",
        diffText: "➕ Day 1 Afternoon: Added 'Traditional silk weaving cotton looms shopping walk'",
        effect: () => {
          updateActiveTrip((prev) => {
            if (!prev) return null;
            const updated = { ...prev.itinerary };
            const newAct: Activity = {
              id: `cop-shop-${Date.now()}`,
              title: "Silk Weaving Looms & Cotton Craft Shopping",
              time: "04:30 PM",
              duration: "2 hours",
              category: "Relaxation",
              rating: 4.8,
              entryFee: "Free Entry",
              description: "Shop directly from hand-loom weavers spinning traditional fabrics, cotton crafts, and brassware.",
              location: "Hand-Loom Weavers Colony",
              image: "https://images.unsplash.com/photo-1590073844006-33379778ae09?auto=format&fit=crop&w=400&q=80",
              slot: "Afternoon Activity"
            };
            updated[1] = [...updated[1], newAct];
            return {
              ...prev,
              itinerary: updated,
              historyTimeline: [
                {
                  id: `hist-cop-${Date.now()}`,
                  action: "🛍 Shopping activity added by Copilot",
                  timestamp: "Just now",
                  iconName: "shopping-bag"
                },
                ...prev.historyTimeline
              ]
            };
          });
        }
      });
    } else if (lowerInput.includes("hotel") || lowerInput.includes("stay")) {
      setPreview({
        title: "Swap Hotel Accommodation",
        description: "Change hotel selection to Sol de Goa Boutique Hotel.",
        diffText: "🏨 Hotel: Heritage Gateway Resort ➔ Sol de Goa Boutique Hotel",
        effect: () => {
          updateActiveTrip((prev) => {
            if (!prev) return null;
            const matched = prev.hotels.find(h => h.id === "hotel-2");
            const reorderedHotels = matched ? [matched, ...prev.hotels.filter(h => h.id !== "hotel-2")] : prev.hotels;
            return {
              ...prev,
              hotels: reorderedHotels,
              historyTimeline: [
                {
                  id: `hist-cop-${Date.now()}`,
                  action: "🏨 Hotel changed via Copilot prompt",
                  timestamp: "Just now",
                  iconName: "home"
                },
                ...prev.historyTimeline
              ]
            };
          });
        }
      });
    } else {
      // Fallback preview
      setPreview({
        title: "Refine Itinerary Schedule",
        description: `Apply general itinerary adjustments for: "${input}"`,
        diffText: "🔄 Reordering activities slots for optimized daily pathways.",
        effect: () => {
          updateActiveTrip((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              historyTimeline: [
                {
                  id: `hist-cop-${Date.now()}`,
                  action: "🔄 Timelines refined by AI Copilot",
                  timestamp: "Just now",
                  iconName: "refresh-cw"
                },
                ...prev.historyTimeline
              ]
            };
          });
        }
      });
    }
  };

  const handleApplyPreview = () => {
    if (preview) {
      preview.effect();
      if (onApplySuccess) onApplySuccess(preview.title);
      setPreview(null);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Copilot Drawer Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 220 }}
            className="fixed top-0 right-0 z-50 h-screen w-full sm:w-[420px] bg-slate-900 text-white flex flex-col shadow-2xl border-l border-slate-800"
          >
            {/* Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-500 text-slate-900 flex items-center justify-center">
                  <Sparkles className="w-4.5 h-4.5 animate-pulse" />
                </div>
                <div className="text-left">
                  <h3 className="font-heading text-sm font-bold tracking-tight">AI Itinerary Copilot</h3>
                  <span className="text-[9.5px] text-teal-400 font-bold uppercase">Active Assistant</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5.5 h-5.5" />
              </button>
            </div>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 no-scrollbar">
              
              {/* Bot Welcome Card */}
              <div className="flex gap-3 text-left">
                <div className="w-8.5 h-8.5 rounded-xl bg-teal-500/20 text-teal-400 border border-teal-505/30 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4.5 h-4.5" />
                </div>
                <div className="p-3 bg-slate-850 bg-slate-800 rounded-xl rounded-tl-none border border-slate-800 max-w-[85%]">
                  <p className="text-xs font-semibold leading-relaxed text-slate-200">
                    Welcome! I am your AI Copilot. You can tell me to modify your itinerary using natural language commands.
                  </p>
                  <p className="text-[10px] text-slate-450 dark:text-slate-400 mt-1 leading-normal italic">
                    Example: "Reduce budget", "Swap hotel", "Add shopping to Day 1", or "Vegetarian options".
                  </p>
                </div>
              </div>

              {/* Suggestions prompt chips */}
              <div className="space-y-2 pt-2 text-left">
                <span className="text-[9.5px] font-bold text-slate-500 uppercase tracking-widest block">
                  Quick Prompt Actions
                </span>
                <div className="flex flex-col gap-2">
                  {suggestedPrompts.map((p) => (
                    <button
                      key={p}
                      onClick={() => handleSendPrompt(p)}
                      className="px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-800 hover:border-teal-500 hover:bg-slate-800 text-[10.5px] font-bold text-left text-slate-300 transition-all"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Thinking loader */}
              {isThinking && (
                <div className="flex gap-3 text-left items-center pt-4">
                  <RefreshCw className="w-4 h-4 text-teal-400 animate-spin" />
                  <span className="text-xs font-bold text-slate-400">Copilot is modifying itinerary details...</span>
                </div>
              )}

              {/* Dynamic Preview Change Card */}
              <AnimatePresence>
                {preview && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 15 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 15 }}
                    className="p-4 bg-teal-950/20 border border-teal-900 rounded-2xl text-left space-y-3"
                  >
                    <div className="flex items-center gap-1.5 text-teal-400">
                      <AlertCircle className="w-4.5 h-4.5" />
                      <h4 className="text-xs font-extrabold uppercase tracking-wider">Preview Changes</h4>
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-white">{preview.title}</h5>
                      <p className="text-[10px] text-slate-350 mt-0.5 leading-relaxed">{preview.description}</p>
                    </div>
                    <div className="p-2.5 bg-slate-900 border border-slate-850 rounded-lg text-[10.5px] font-mono text-teal-400 break-words leading-relaxed">
                      {preview.diffText}
                    </div>
                    <div className="flex items-center justify-end gap-1.5 pt-1">
                      <button
                        onClick={() => setPreview(null)}
                        className="px-3 py-1.5 border border-slate-800 hover:bg-slate-850 text-slate-400 hover:text-white rounded-lg text-[10.5px] font-bold transition-colors"
                      >
                        Discard
                      </button>
                      <button
                        onClick={handleApplyPreview}
                        className="px-3.5 py-1.5 bg-teal-500 hover:bg-teal-600 text-slate-950 rounded-lg text-[10.5px] font-extrabold flex items-center gap-1 transition-colors"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Apply Changes
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

            </div>

            {/* Input Box */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/80">
              <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 focus-within:border-teal-500 transition-colors">
                <input
                  type="text"
                  placeholder="Describe details to modify itinerary..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSendPrompt();
                  }}
                  className="flex-1 bg-transparent border-none outline-none text-xs text-slate-205 text-slate-300 placeholder-slate-550 font-bold"
                />
                <button
                  onClick={() => handleSendPrompt()}
                  className="p-1.5 rounded-lg bg-teal-500 text-slate-900 hover:bg-teal-600 transition-colors"
                  aria-label="Send copilot instructions"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
export default FloatingAICopilot;
