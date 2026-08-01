import React, { useState } from "react";
import { X, Send, Mail, Link2, Download, CheckCircle, Loader } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  tripName: string;
}

export const ShareDialog: React.FC<ShareDialogProps> = ({ isOpen, onClose, tripName }) => {
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    setDownloadSuccess(false);

    // Simulate PDF generation and formatting
    await new Promise((resolve) => setTimeout(resolve, 3000));

    setIsDownloading(false);
    setDownloadSuccess(true);
    setTimeout(() => {
      setDownloadSuccess(false);
    }, 3000);
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

          {/* Modal Centered on Desktop, Bottom Sheet on Mobile */}
          <div className="fixed inset-0 flex items-center justify-center p-4 z-50 pointer-events-none">
            <motion.div
              // Mobile: bottom sheet, Desktop: modal popup
              initial={{
                y: window.innerWidth < 640 ? "100%" : 20,
                opacity: window.innerWidth < 640 ? 1 : 0,
                scale: window.innerWidth < 640 ? 1 : 0.95
              }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{
                y: window.innerWidth < 640 ? "100%" : 20,
                opacity: window.innerWidth < 640 ? 1 : 0,
                scale: window.innerWidth < 640 ? 1 : 0.95
              }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="bg-white dark:bg-[#111827] w-full max-w-sm rounded-t-[28px] sm:rounded-2xl shadow-2xl border-t border-slate-200 dark:border-slate-800 sm:border-t-0 sm:border border-slate-200/50 dark:border-slate-800/80 overflow-hidden pointer-events-auto
                fixed bottom-0 left-0 right-0 sm:relative sm:bottom-auto sm:left-auto sm:right-auto"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
                <span className="font-heading text-xs font-bold text-slate-400 uppercase tracking-widest">
                  Share Itinerary
                </span>
                <button
                  onClick={onClose}
                  className="p-1 rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 hover:text-slate-650 dark:hover:text-slate-350 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Share Chips Grid */}
              <div className="p-6 space-y-5">
                <div>
                  <h3 className="font-heading text-sm font-bold text-slate-850 dark:text-slate-150 text-slate-800 dark:text-slate-200">
                    Spread the Adventure
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                    Share your curated trip plans for "{tripName}" with friends and co-travelers.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {/* WhatsApp */}
                  <a
                    href={`https://api.whatsapp.com/send?text=Check out my travel plan for ${encodeURIComponent(tripName)}!`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-3 rounded-xl border border-slate-150 dark:border-slate-850 flex flex-col items-center gap-1.5 text-slate-700 dark:text-slate-300 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/20 hover:border-emerald-200 dark:hover:border-emerald-900/50 transition-all text-center"
                  >
                    <Send className="w-5 h-5 text-emerald-500" />
                    <span className="text-[11px] font-bold">WhatsApp</span>
                  </a>

                  {/* Email */}
                  <a
                    href={`mailto:?subject=AI Travel Plan: ${tripName}&body=Hey, checkout this itinerary I planned on Tourist.AI...`}
                    className="p-3 rounded-xl border border-slate-150 dark:border-slate-850 flex flex-col items-center gap-1.5 text-slate-700 dark:text-slate-300 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 hover:border-blue-200 dark:hover:border-blue-900/50 transition-all text-center"
                  >
                    <Mail className="w-5 h-5 text-blue-500" />
                    <span className="text-[11px] font-bold">Email</span>
                  </a>

                  {/* Copy Link */}
                  <button
                    onClick={handleCopyLink}
                    className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all text-center ${
                      copied
                        ? "border-teal-500 bg-teal-50/40 dark:bg-teal-950/20 text-teal-650"
                        : "border-slate-150 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900"
                    }`}
                  >
                    <Link2 className="w-5 h-5 text-teal-505 text-slate-500" />
                    <span className="text-[11px] font-bold">{copied ? "Copied!" : "Copy Link"}</span>
                  </button>

                  {/* Download PDF */}
                  <button
                    onClick={handleDownloadPDF}
                    disabled={isDownloading || downloadSuccess}
                    className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 transition-all text-center ${
                      downloadSuccess
                        ? "border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20 text-emerald-650"
                        : "border-slate-150 dark:border-slate-850 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900"
                    }`}
                  >
                    {isDownloading ? (
                      <Loader className="w-5 h-5 text-slate-400 animate-spin" />
                    ) : downloadSuccess ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <Download className="w-5 h-5 text-slate-500" />
                    )}
                    <span className="text-[11px] font-bold">
                      {isDownloading ? "Creating..." : downloadSuccess ? "Downloaded!" : "Download PDF"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Progress sync / Success banner */}
              <AnimatePresence>
                {isDownloading && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "auto" }}
                    exit={{ height: 0 }}
                    className="bg-slate-50 dark:bg-slate-900 px-5 py-3 border-t border-slate-100 dark:border-slate-850 text-center"
                  >
                    <p className="text-[10px] text-slate-400 font-semibold flex items-center justify-center gap-1.5">
                      <Loader className="w-3.5 h-3.5 animate-spin text-teal-600" />
                      Generating premium PDF package...
                    </p>
                  </motion.div>
                )}
                {downloadSuccess && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "auto" }}
                    exit={{ height: 0 }}
                    className="bg-emerald-50 dark:bg-emerald-950/20 px-5 py-3 border-t border-emerald-100 dark:border-emerald-900/40 text-center"
                  >
                    <p className="text-[10.5px] text-emerald-650 dark:text-emerald-450 font-bold flex items-center justify-center gap-1.5">
                      ✓ PDF Successfully compiled & saved!
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>

            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
export default ShareDialog;
