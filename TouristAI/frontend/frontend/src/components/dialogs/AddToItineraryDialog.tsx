import React, { useState, useEffect } from "react";
import { X, Calendar, Clock, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
 
interface AddToItineraryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  item: { type: 'hotel' | 'restaurant' | 'attraction', id: string, name: string, location: string, rating: number, image: string } | null;
  durationDays: number;
  onAdd: (dayNum: number, time: string) => void;
}
 
export const AddToItineraryDialog: React.FC<AddToItineraryDialogProps> = ({
  isOpen,
  onClose,
  item,
  durationDays,
  onAdd,
}) => {
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [selectedTime, setSelectedTime] = useState<string>("09:00 AM");
 
  // Reset defaults when item changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedDay(1);
      // setSelectedTime(item?.type === "hotel" ? "09:00 PM" : "01:00 PM");commented this to add attractions code below
      setSelectedTime(
  item?.type === "hotel" ? "09:00 PM"
  : item?.type === "attraction" ? "09:00 AM"
  : "01:00 PM"
);
    }
  }, [isOpen, item]);
 
  if (!item) return null;
 
  // Generate days based on trip duration
  const dayOptions = [];
  for (let i = 1; i <= durationDays; i++) {
    dayOptions.push(i);
  }
 
  // Generate times (07:00 AM to 11:30 PM, 30m intervals)
  const timeOptions: string[] = [];
  for (let hour = 7; hour <= 23; hour++) {
    const h12 = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    const ampm = hour >= 12 ? "PM" : "AM";
    const hStr = h12 < 10 ? `0${h12}` : `${h12}`;
    timeOptions.push(`${hStr}:00 ${ampm}`);
    timeOptions.push(`${hStr}:30 ${ampm}`);
  }
 
  const handleAddClick = () => {
    onAdd(selectedDay, selectedTime);
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
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 pointer-events-auto"
          />
 
          {/* Modal Centered on Desktop, Bottom Sheet on Mobile */}
          <div className="fixed inset-0 flex items-center justify-center p-4 z-50 pointer-events-none">
            <motion.div
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
                fixed bottom-0 left-0 right-0 sm:relative sm:bottom-auto sm:left-auto sm:right-auto text-left"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-850">
                <span className="font-heading text-xs font-bold text-slate-400 uppercase tracking-widest">
                  Add to Itinerary
                </span>
                <button
                  onClick={onClose}
                  className="p-1 rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 hover:text-slate-650 dark:hover:text-slate-350 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
 
              {/* Form Content */}
              <div className="p-6 space-y-5">
                <div>
                  <h3 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-200">
                    {item.type === "hotel"
    ? "🏨 Add Stay Accommodation"
    : item.type === "attraction"
    ? "🗺️ Add on Travel Plan"
    : "🍽 Add Dining Spot"}
                  </h3>
                  <p className="text-[11px] text-slate-450 dark:text-slate-400 mt-1 font-medium truncate">
                    {item.name}
                  </p>
                  <span className="text-[10px] text-slate-400 block truncate mt-0.5">
                    {item.location}
                  </span>
                </div>
 
                <div className="space-y-4">
                  {/* Select Day */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-teal-600" />
                      Select Day
                    </label>
                    <select
                      value={selectedDay}
                      onChange={(e) => setSelectedDay(parseInt(e.target.value))}
                      className="w-full p-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-slate-50/50 dark:bg-slate-900/40 text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500 font-medium"
                    >
                      {dayOptions.map((day) => (
                        <option key={day} value={day}>
                          Day {day}
                        </option>
                      ))}
                    </select>
                  </div>
 
                  {/* Select Time */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-teal-600" />
                      Select Time
                    </label>
                    <select
                      value={selectedTime}
                      onChange={(e) => setSelectedTime(e.target.value)}
                      className="w-full p-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-805 bg-slate-50/50 dark:bg-slate-900/40 text-slate-700 dark:text-slate-300 outline-none focus:border-teal-500 font-medium"
                    >
                      {timeOptions.map((time) => (
                        <option key={time} value={time}>
                          {time}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
 
                {/* Submit Action */}
                <button
                  onClick={handleAddClick}
                  className="w-full py-2.5 mt-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 hover-scale shadow-sm"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add to Itinerary</span>
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};