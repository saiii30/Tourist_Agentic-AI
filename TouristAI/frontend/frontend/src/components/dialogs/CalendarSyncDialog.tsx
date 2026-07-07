import { useState, useEffect } from "react";
import { X, Calendar, Globe, CheckCircle, ExternalLink, ArrowRight, Loader } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface CalendarSyncDialogProps {
  isOpen: boolean;
  onClose: () => void;
  tripName: string;
}

type SyncStep = "auth" | "syncing" | "success";

export const CalendarSyncDialog: React.FC<CalendarSyncDialogProps> = ({ isOpen, onClose, tripName }) => {
  const [step, setStep] = useState<SyncStep>("auth");
  const [progress, setProgress] = useState<number>(0);

  // Reset steps when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep("auth");
      setProgress(0);
    }
  }, [isOpen]);

  // Simulate progress bar during sync step
  useEffect(() => {
    let interval: any;
    if (step === "syncing") {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((p) => {
          if (p >= 100) {
            clearInterval(interval);
            setTimeout(() => setStep("success"), 500);
            return 100;
          }
          return p + 4;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [step]);

  const handleGoogleAuth = () => {
    setStep("syncing");
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-55"
          />

          {/* Sync Dialog Modal */}
          <div className="fixed inset-0 flex items-center justify-center p-4 z-55">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", duration: 0.3 }}
              className="bg-white dark:bg-[#111827] w-full max-w-md rounded-2xl shadow-2xl border border-slate-200/50 dark:border-slate-800/85 overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
                <span className="font-heading text-xs font-bold text-slate-400 uppercase tracking-widest">
                  Google Calendar Integration
                </span>
                {step !== "syncing" && (
                  <button
                    onClick={onClose}
                    className="p-1 rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-650 dark:hover:text-slate-350 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Steps Body */}
              <div className="p-6 h-[260px] flex flex-col justify-center items-center">
                
                {/* ── STEP 1: AUTHENTICATION ── */}
                {step === "auth" && (
                  <motion.div
                    key="step-auth"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="text-center space-y-5"
                  >
                    <div className="w-12 h-12 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center mx-auto text-slate-800 dark:text-slate-200">
                      <Globe className="w-6 h-6 text-teal-650" />
                    </div>
                    <div>
                      <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100">
                        Sign in with Google
                      </h3>
                      <p className="text-xs text-slate-400 dark:text-slate-500 max-w-xs mt-1.5 mx-auto">
                        In order to insert events directly, authorize Tourist.AI to access your Google Calendar.
                      </p>
                    </div>
                    <button
                      onClick={handleGoogleAuth}
                      className="px-5 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white text-xs font-semibold flex items-center gap-2 mx-auto hover-scale shadow-md"
                    >
                      <Globe className="w-4 h-4" />
                      Sign In with Google Account
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </motion.div>
                )}

                {/* ── STEP 2: SYNCING ── */}
                {step === "syncing" && (
                  <motion.div
                    key="step-syncing"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center w-full max-w-[280px] space-y-5"
                  >
                    <div className="relative w-12 h-12 flex items-center justify-center mx-auto">
                      <Loader className="w-10 h-10 text-teal-600 dark:text-teal-400 animate-spin" />
                      <Calendar className="w-4.5 h-4.5 text-teal-600 dark:text-teal-400 absolute" />
                    </div>
                    <div>
                      <h3 className="font-heading text-sm font-semibold text-slate-800 dark:text-slate-200">
                        Creating Calendar Events...
                      </h3>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Exporting activities for "{tripName}"
                      </p>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="space-y-1.5">
                      <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-teal-600 dark:bg-teal-400 rounded-full"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-teal-600 dark:text-teal-400">
                        {progress}%
                      </span>
                    </div>
                  </motion.div>
                )}

                {/* ── STEP 3: SUCCESS ── */}
                {step === "success" && (
                  <motion.div
                    key="step-success"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center space-y-4"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", damping: 12 }}
                      className="w-14 h-14 rounded-full bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 flex items-center justify-center mx-auto text-emerald-650"
                    >
                      <CheckCircle className="w-8 h-8 text-emerald-605" />
                    </motion.div>
                    <div>
                      <h3 className="font-heading text-base font-bold text-slate-800 dark:text-slate-100">
                        Trip Successfully Added
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        All itinerary stops have been synchronized with your primary Google Calendar schedules.
                      </p>
                    </div>
                  </motion.div>
                )}

              </div>

              {/* Success Actions Footer */}
              {step === "success" && (
                <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 justify-end">
                  <button
                    onClick={onClose}
                    className="w-full sm:w-auto px-4 py-2 border border-slate-200 dark:border-slate-850 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    Done
                  </button>
                  <a
                    href="https://calendar.google.com"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full sm:w-auto px-4 py-2 bg-teal-650 text-white bg-teal-600 hover:bg-teal-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 hover-scale"
                  >
                    Open Google Calendar
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}

            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
export default CalendarSyncDialog;
