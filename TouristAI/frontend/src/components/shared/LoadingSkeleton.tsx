import React from "react";

export const ShimmerElement: React.FC<{ className?: string }> = ({ className = "h-4 w-full" }) => {
  return <div className={`shimmer-bg rounded-lg ${className}`} />;
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="p-4 bg-white dark:bg-[#1e293b]/60 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl flex flex-col md:flex-row gap-4">
      {/* Shimmer Image */}
      <ShimmerElement className="w-full md:w-36 h-28 rounded-xl flex-shrink-0" />
      
      {/* Shimmer details */}
      <div className="flex-1 space-y-3 py-1">
        <div className="flex gap-2">
          <ShimmerElement className="h-4 w-16" />
          <ShimmerElement className="h-4 w-12" />
        </div>
        <ShimmerElement className="h-5 w-2/3" />
        <div className="space-y-1.5">
          <ShimmerElement className="h-3 w-full" />
          <ShimmerElement className="h-3 w-5/6" />
        </div>
        <ShimmerElement className="h-3.5 w-24" />
      </div>
    </div>
  );
};

export const TimelineSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Banner hero skeleton */}
      <div className="rounded-[28px] overflow-hidden border border-slate-200/50 dark:border-slate-800/80 bg-white dark:bg-[#111827]">
        <ShimmerElement className="h-48 sm:h-56 w-full rounded-none" />
        <div className="p-5 sm:p-6 grid grid-cols-2 md:grid-cols-5 gap-3 border-b border-slate-100 dark:border-slate-800">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 space-y-2">
              <ShimmerElement className="h-3 w-12" />
              <ShimmerElement className="h-4 w-20" />
            </div>
          ))}
        </div>
        <div className="p-5 sm:p-6">
          <ShimmerElement className="h-12 w-full rounded-2xl" />
        </div>
      </div>

      {/* Timeline items skeleton */}
      <div className="space-y-6 relative pl-6 sm:pl-8">
        <div className="absolute left-[9px] sm:left-[11px] top-6 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-800" />
        
        {[...Array(2)].map((_, dayIdx) => (
          <div key={dayIdx} className="space-y-4">
            {/* Day header skeleton */}
            <div className="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 rounded-2xl flex items-center justify-between">
              <div className="space-y-1.5">
                <ShimmerElement className="h-5 w-24" />
                <ShimmerElement className="h-3 w-48" />
              </div>
              <ShimmerElement className="h-8 w-8 rounded-lg" />
            </div>

            {/* Activities skeleton */}
            <div className="space-y-4">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const MapPlaceholder: React.FC = () => {
  return (
    <div className="relative h-64 sm:h-full w-full rounded-3xl overflow-hidden border border-slate-200/60 dark:border-slate-800/60 bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-6 text-center space-y-3">
      {/* Grid line patterns simulated on background */}
      <div className="absolute inset-0 opacity-10 bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      
      {/* Glow dot overlay */}
      <div className="w-4 h-4 rounded-full bg-teal-500 animate-ping absolute top-1/3 left-1/2" />
      <div className="w-3.5 h-3.5 rounded-full bg-teal-650 bg-teal-500 absolute top-1/3 left-1/2" />
      
      <div className="relative z-10 max-w-xs space-y-1.5">
        <h4 className="font-heading text-sm font-bold text-slate-800 dark:text-slate-100">
          Interactive Map Visualizer
        </h4>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-normal">
          AI routing renders optimized routes, points-of-interest markers, and estimated travel times.
        </p>
      </div>
    </div>
  );
};
