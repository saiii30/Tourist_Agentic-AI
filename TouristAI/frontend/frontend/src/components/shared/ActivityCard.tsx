import React from "react";
import { Clock, MapPin, Tag, Star, Heart, Trash2, ExternalLink, RefreshCw } from "lucide-react";
import type { Activity } from "../../context/TravelPlannerContext";

interface ActivityCardProps {
  activity: Activity;
  onDelete: (id: string) => void;
  onFavoriteToggle: (id: string) => void;
  onReplace?: (id: string) => void;
  onViewOnMap?: (location: string, title: string) => void;
}

export const ActivityCard: React.FC<ActivityCardProps> = ({
  activity,
  onDelete,
  onFavoriteToggle,
  onReplace,
  onViewOnMap
}) => {
  
  const getCategoryColor = (cat: Activity["category"]) => {
    switch (cat) {
      case "Sightseeing":
        return "bg-sky-50 text-sky-700 border-sky-100 dark:bg-sky-950/20 dark:text-sky-400 dark:border-sky-900/30";
      case "Food":
        return "bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/30";
      case "Adventure":
        return "bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/30";
      case "Culture":
        return "bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-950/20 dark:text-purple-400 dark:border-purple-900/30";
      case "Relaxation":
        return "bg-teal-50 text-teal-700 border-teal-100 dark:bg-teal-950/20 dark:text-teal-400 dark:border-teal-900/30";
      default:
        return "bg-slate-50 text-slate-700 border-slate-100 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800";
    }
  };

  return (
    <div className="group relative flex flex-col md:flex-row items-start gap-4 p-4 bg-white dark:bg-[#1e293b]/60 dark:hover:bg-[#1e293b]/80 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl hover:shadow-md hover:border-slate-350 dark:hover:border-slate-700 transition-all duration-200">
      
      {/* Activity Image */}
      <div className="relative w-full md:w-36 h-28 rounded-xl overflow-hidden flex-shrink-0 bg-slate-100 dark:bg-slate-800 shadow-inner">
        <img
          src={activity.image}
          alt={activity.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        {/* Time overlay */}
        <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded-lg bg-black/60 backdrop-blur-md text-[10px] font-bold text-white flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          {activity.time}
        </span>
      </div>

      {/* Details info */}
      <div className="flex-1 min-w-0 space-y-1.5 text-left">
        <div className="flex flex-wrap items-center gap-2">
          {/* Specific Timeline Slot Tag */}
          {activity.slot && (
            <span className="px-2.5 py-0.5 rounded-full text-[9px] font-extrabold bg-teal-650 bg-teal-600 text-white shadow-sm uppercase tracking-wider">
              {activity.slot}
            </span>
          )}

          {/* Category Badge */}
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getCategoryColor(activity.category)}`}>
            {activity.category}
          </span>
          
          {/* Duration info */}
          <span className="text-[10px] text-slate-400 font-semibold">
            {activity.duration}
          </span>

          {/* Rating */}
          <div className="flex items-center gap-0.5 text-amber-500 text-[10px] font-bold ml-auto">
            <Star className="w-3.5 h-3.5 fill-amber-500" />
            <span>{activity.rating.toFixed(1)}</span>
          </div>
        </div>

        <div>
          <h4 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100 group-hover:text-teal-650 transition-colors">
            {activity.title}
          </h4>
          <div className="flex items-center gap-1 text-[10px] text-slate-450 dark:text-slate-400 mt-0.5">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate">{activity.location}</span>
          </div>
        </div>

        <p className="text-[11.5px] text-slate-500 dark:text-slate-400 leading-relaxed font-medium line-clamp-2">
          {activity.description}
        </p>

        {/* Pricing / Entry Info */}
        <div className="flex items-center gap-1 text-[10.5px] font-bold text-slate-600 dark:text-slate-300 pt-1">
          <Tag className="w-3.5 h-3.5 text-slate-400" />
          <span>Entry Fee: {activity.entryFee}</span>
        </div>
      </div>

      {/* Action Buttons: Navigate, Replace, Delete, Favorite */}
      <div className="flex md:flex-col items-center justify-end w-full md:w-auto gap-1.5 border-t md:border-t-0 border-slate-100 dark:border-slate-800 pt-3 md:pt-0 self-stretch md:self-auto flex-shrink-0">
        
        {/* Favorite */}
        <button
          onClick={() => onFavoriteToggle(activity.id)}
          className={`p-2 rounded-xl border transition-colors ${
            activity.isFavorite
              ? "border-rose-100 bg-rose-50/50 text-rose-600 dark:border-rose-900/30 dark:bg-rose-950/20"
              : "border-slate-200 dark:border-slate-800 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20"
          }`}
          aria-label="Add to Favorites"
        >
          <Heart className={`w-4 h-4 ${activity.isFavorite ? "fill-rose-500" : ""}`} />
        </button>

        {/* Navigate Map Link */}
        {onViewOnMap ? (
          <button
            onClick={() => onViewOnMap(activity.location, activity.title)}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-450 hover:text-teal-600 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-colors"
            title="View on Map"
            aria-label="View on Map"
          >
            <MapPin className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          </button>
        ) : (
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activity.location + " " + activity.title)}`}
            target="_blank"
            rel="noreferrer"
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-450 hover:text-teal-600 hover:bg-teal-50/50 dark:hover:bg-teal-950/20 transition-colors"
            title="Open in Google Maps"
            aria-label="Get Directions"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}

        {/* Replace Button */}
        {onReplace && (
          <button
            onClick={() => onReplace(activity.id)}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-450 hover:text-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 transition-colors"
            aria-label="Replace Activity"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* Delete */}
        <button
          onClick={() => onDelete(activity.id)}
          className="p-2 rounded-xl border border-slate-200 dark:border-slate-805 text-slate-450 hover:text-red-650 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
          aria-label="Delete Activity"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

    </div>
  );
};
export default ActivityCard;
