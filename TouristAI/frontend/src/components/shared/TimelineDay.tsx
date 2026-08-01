import React, { useState } from "react";
import { ChevronDown, ChevronUp, Compass } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface TimelineDayProps {
  dayNum: number;
  activitiesCount: number;
  children: React.ReactNode;
}

export const TimelineDay: React.FC<TimelineDayProps> = ({ dayNum, activitiesCount, children }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const getDayThemeDescription = (num: number) => {
    switch (num) {
      case 1:
        return "Historic Highlights & Cultural Foundations";
      case 2:
        return "Scenic Discoveries & Local Gastronomy";
      case 3:
        return "Coastal Escapes & Scenic Sunsets";
      default:
        return "Leisure Exploration & Souvenir Shopping";
    }
  };

  return (
    <div className="relative pl-6 sm:pl-8 space-y-4">
      {/* Vertical Connecting Line */}
      <div className="absolute left-[9px] sm:left-[11px] top-6 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-800 pointer-events-none" />

      {/* Glow dot indicator */}
      <div className="absolute left-0 top-1.5 w-[20px] h-[20px] rounded-full border-[3.5px] border-teal-600 bg-white dark:bg-[#0b0f19] flex items-center justify-center timeline-dot text-teal-600" />

      {/* Day Folder Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-850/60 transition-all select-none"
      >
        <div className="space-y-0.5 text-left pr-2">
          <div className="flex items-center gap-2">
            <span className="font-heading text-sm sm:text-base font-bold text-slate-800 dark:text-slate-100">
              Day {dayNum}
            </span>
            <span className="px-2 py-0.5 rounded-md bg-teal-50 dark:bg-teal-950/20 text-[9.5px] font-bold text-teal-700 dark:text-teal-400">
              {activitiesCount} {activitiesCount === 1 ? "Activity" : "Activities"}
            </span>
          </div>
          <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 flex-shrink-0" />
            {getDayThemeDescription(dayNum)}
          </p>
        </div>

        <button
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/40 dark:hover:bg-slate-800/40 transition-colors"
          aria-label={isExpanded ? "Collapse Day" : "Expand Day"}
        >
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Activities Grid Container */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="space-y-4 pb-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
export default TimelineDay;
