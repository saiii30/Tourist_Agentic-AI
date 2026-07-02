import React, { useState } from "react";
import { Bookmark, Calendar, FileText, CheckCircle2, ChevronRight, X, FileCode } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SaveDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveOnly: (type: "Draft" | "Completed") => void;
  onSaveAndSync: () => void;
  onDownloadPDF?: () => void;
  onExportICS?: () => void;
}

type SaveOption = "draft" | "final" | "google" | "pdf" | "ics";

export const SaveDialog: React.FC<SaveDialogProps> = ({
  isOpen,
  onClose,
  onSaveOnly,
  onSaveAndSync,
  onDownloadPDF,
  onExportICS
}) => {
  const [selectedOption, setSelectedOption] = useState<SaveOption>("final");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveAction = async () => {
    setIsSaving(true);
    // Simulate minor progress
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSaving(false);
    setSaveSuccess(true);

    // Wait for success animation
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setSaveSuccess(false);

    // Trigger parent handlers
    if (selectedOption === "draft") {
      onSaveOnly("Draft");
    } else if (selectedOption === "final") {
      onSaveOnly("Completed");
    } else if (selectedOption === "google") {
      onSaveAndSync();
    } else if (selectedOption === "pdf") {
      if (onDownloadPDF) onDownloadPDF();
      onClose();
    } else if (selectedOption === "ics") {
      if (onExportICS) onExportICS();
      onClose();
    }
  };

  const optionsList = [
    { id: "draft" as SaveOption, label: "Save Draft", desc: "Saves as local editable collection draft", icon: Bookmark, color: "text-slate-500 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800" },
    { id: "final" as SaveOption, label: "Save Final", desc: "Saves as finalized trip in Upcoming collection", icon: CheckCircle2, color: "text-teal-600 bg-teal-50/50 dark:bg-teal-950/20 border-teal-100 dark:border-teal-900" },
    { id: "google" as SaveOption, label: "Save + Google Calendar", desc: "Saves and syncs all stops to Google Calendar", icon: Calendar, color: "text-blue-500 bg-blue-50/50 dark:bg-blue-950/20 border-blue-100 dark:border-blue-900" },
    { id: "pdf" as SaveOption, label: "Download PDF Itinerary", desc: "Generates formatted offline trip PDF guide", icon: FileText, color: "text-rose-500 bg-rose-50/50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900" },
    { id: "ics" as SaveOption, label: "Export ICS Calendar File", desc: "Generates standard ICS calendar download", icon: FileCode, color: "text-amber-500 bg-amber-50/50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900" }
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-55"
          />

          {/* Modal Container */}
          <div className="fixed inset-0 flex items-center justify-center p-4 z-55">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", duration: 0.3 }}
              className="bg-white dark:bg-[#111827] w-full max-w-md rounded-2xl shadow-2xl border border-slate-200/50 dark:border-slate-800/80 overflow-hidden text-left"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-850">
                <span className="font-heading text-xs font-bold text-slate-400 uppercase tracking-widest">
                  Save Trip Workflow
                </span>
                {!isSaving && !saveSuccess && (
                  <button
                    onClick={onClose}
                    className="p-1 rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 hover:text-slate-650 dark:hover:text-slate-350 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Steps views */}
              <div className="p-6 space-y-4">
                <AnimatePresence mode="wait">
                  {saveSuccess ? (
                    <motion.div
                      key="success"
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.9, opacity: 0 }}
                      className="text-center py-8 space-y-3"
                    >
                      <div className="w-14 h-14 rounded-full bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-250 dark:border-emerald-900/40 flex items-center justify-center mx-auto text-emerald-600">
                        <CheckCircle2 className="w-8 h-8 text-emerald-605 animate-pulse" />
                      </div>
                      <div>
                        <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-200">
                          Trip Saved Successfully
                        </h3>
                        <p className="text-[11px] text-slate-450 dark:text-slate-400">
                          Updating dashboard indexes and collections...
                        </p>
                      </div>
                    </motion.div>
                  ) : isSaving ? (
                    <motion.div
                      key="saving"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-center py-10 space-y-3"
                    >
                      <LoaderIcon className="w-10 h-10 text-teal-600 animate-spin mx-auto" />
                      <div>
                        <h3 className="font-heading text-sm font-semibold text-slate-800 dark:text-slate-250">
                          Writing Trip Config Data...
                        </h3>
                        <p className="text-[10px] text-slate-400">
                          Synchronizing with local SQLite databases
                        </p>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="options"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-3"
                    >
                      <div className="text-center mb-1">
                        <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100">
                          Select Save Format
                        </h3>
                        <p className="text-[11px] text-slate-450 dark:text-slate-400 mt-0.5">
                          Choose how you want to secure and sync your trip collections.
                        </p>
                      </div>

                      {/* Options Grid */}
                      <div className="space-y-2">
                        {optionsList.map((opt) => {
                          const Icon = opt.icon;
                          const active = selectedOption === opt.id;
                          return (
                            <button
                              key={opt.id}
                              onClick={() => setSelectedOption(opt.id)}
                              className={`w-full p-3 rounded-xl border text-left flex items-start gap-3 transition-all ${
                                active
                                  ? "border-teal-605 bg-teal-50/40 dark:bg-teal-950/20 text-teal-700 dark:text-teal-400 ring-2 ring-teal-500/10"
                                  : "border-slate-150 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-900/60 text-slate-700 dark:text-slate-350"
                              }`}
                            >
                              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 border ${opt.color}`}>
                                <Icon className="w-4 h-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold">{opt.label}</p>
                                <p className="text-[9.5px] text-slate-400 truncate">{opt.desc}</p>
                              </div>
                              <ChevronRight className={`w-4 h-4 mt-2 text-slate-400 transition-transform ${active ? "translate-x-1" : ""}`} />
                            </button>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Actions Footer */}
              {!isSaving && !saveSuccess && (
                <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-850 flex items-center justify-end gap-2">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 border border-slate-200 dark:border-slate-850 text-xs font-semibold text-slate-655 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveAction}
                    className="px-5 py-2 bg-teal-650 bg-teal-605 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold hover-scale shadow-md shadow-teal-600/10"
                  >
                    Confirm & Save
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

// Local spinning loader helper
const LoaderIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={props.className}
    {...props}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);

export default SaveDialog;
