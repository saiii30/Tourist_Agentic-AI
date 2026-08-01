import React, { useState, useEffect } from "react";
import { RefreshCw, X, Loader } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface RegenerateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onRegenerate: (keeps: { budget: boolean; style: boolean; interests: boolean; duration: boolean }) => void;
}

export const RegenerateDialog: React.FC<RegenerateDialogProps> = ({ isOpen, onClose, onRegenerate }) => {
  const [budget, setBudget] = useState(true);
  const [style, setStyle] = useState(true);
  const [interests, setInterests] = useState(false);
  const [duration, setDuration] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsGenerating(false);
    }
  }, [isOpen]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    // Simulate AI Generation delay
    await new Promise((resolve) => setTimeout(resolve, 3000));
    onRegenerate({ budget, style, interests, duration });
    setIsGenerating(false);
    onClose();
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal Container */}
          <div className="fixed inset-0 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", duration: 0.3 }}
              className="bg-white dark:bg-[#111827] w-full max-w-md rounded-2xl shadow-2xl border border-slate-200/50 dark:border-slate-800/80 overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
                <span className="font-heading text-sm font-bold text-slate-850 dark:text-slate-150 flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
                  <RefreshCw className="w-4 h-4 text-teal-650" />
                  Regenerate Itinerary
                </span>
                {!isGenerating && (
                  <button
                    onClick={onClose}
                    className="p-1 rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-650 dark:hover:text-slate-350 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Body */}
              <div className="p-6">
                <AnimatePresence mode="wait">
                  {!isGenerating ? (
                    <motion.div
                      key="options"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-4"
                    >
                      <div>
                        <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100">
                          Configure New Plan Parameters
                        </h3>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                          Select which aspects of the current plan you would like the AI core to keep or lock when creating the alternate itinerary.
                        </p>
                      </div>

                      {/* Checkbox settings */}
                      <div className="space-y-2 pt-2">
                        {/* Budget */}
                        <label className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/40 cursor-pointer select-none">
                          <div className="text-left">
                            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                              Keep Budget Tier
                            </p>
                            <p className="text-[10px] text-slate-400">
                              Maintains same expenses calculations
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={budget}
                            onChange={(e) => setBudget(e.target.checked)}
                            className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                          />
                        </label>

                        {/* Travel Style */}
                        <label className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/40 cursor-pointer select-none">
                          <div className="text-left">
                            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                              Keep Travel Style
                            </p>
                            <p className="text-[10px] text-slate-400">
                              Locks adventure / relaxation balances
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={style}
                            onChange={(e) => setStyle(e.target.checked)}
                            className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                          />
                        </label>

                        {/* Interests */}
                        <label className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/40 cursor-pointer select-none">
                          <div className="text-left">
                            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                              Keep Specific Interests
                            </p>
                            <p className="text-[10px] text-slate-400">
                              Retains food tours, hikes, and sights
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={interests}
                            onChange={(e) => setInterests(e.target.checked)}
                            className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                          />
                        </label>

                        {/* Duration */}
                        <label className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/40 cursor-pointer select-none">
                          <div className="text-left">
                            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                              Keep Itinerary Duration
                            </p>
                            <p className="text-[10px] text-slate-400">
                              Keeps number of travel days same
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={duration}
                            onChange={(e) => setDuration(e.target.checked)}
                            className="w-4.5 h-4.5 accent-teal-600 rounded cursor-pointer"
                          />
                        </label>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="generating"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-center py-10 space-y-4"
                    >
                      <div className="relative w-12 h-12 mx-auto flex items-center justify-center">
                        <Loader className="w-10 h-10 text-teal-600 dark:text-teal-400 animate-spin" />
                        <RefreshCw className="w-4.5 h-4.5 text-teal-650 dark:text-teal-400 absolute animate-pulse" />
                      </div>
                      <div>
                        <h3 className="font-heading text-sm font-semibold text-slate-800 dark:text-slate-200">
                          AI is generating another itinerary...
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-1 max-w-[220px] mx-auto leading-relaxed">
                          Re-indexing sights, dining joints, and mapping optimized routes.
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Actions Footer */}
              {!isGenerating && (
                <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 justify-end">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 border border-slate-200 dark:border-slate-850 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleGenerate}
                    className="px-4 py-2 bg-teal-650 bg-teal-655 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 hover-scale shadow-md"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Generate Itinerary
                  </button>
                </div>
              )}

            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
export default RegenerateDialog;
