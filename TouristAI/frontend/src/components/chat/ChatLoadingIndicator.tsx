import {
  Bot,
  BookOpen,
  CalendarDays,
  CloudSun,
  Hotel,
  Landmark,
  MapPin,
  Plane,
  Sparkles,
  Train,
  Utensils,
} from "lucide-react";

interface ChatLoadingIndicatorProps {
  stage: string;
  stageNumber: number;
  totalStages: number;
  stages?: string[];
}

const getStageDisplay = (stage: string) => {
  const lower = stage.toLowerCase();

  if (lower.includes("hotel") || lower.includes("stay")) {
    return { icon: Hotel, text: "Finding the best hotels..." };
  }
  if (lower.includes("restaurant") || lower.includes("food")) {
    return { icon: Utensils, text: "Looking for great restaurants..." };
  }
  if (lower.includes("weather")) {
    return { icon: CloudSun, text: "Checking the latest weather..." };
  }
  if (lower.includes("nearby") || lower.includes("attraction") || lower.includes("places")) {
    return { icon: MapPin, text: "Discovering nearby attractions..." };
  }
  if (lower.includes("transport") || lower.includes("train") || lower.includes("travel options")) {
    return { icon: Train, text: "Searching travel options..." };
  }
  if (lower.includes("calendar") || lower.includes("itinerary") || lower.includes("organizing")) {
    return { icon: CalendarDays, text: "Organizing your itinerary..." };
  }
  if (lower.includes("routing")) {
    return { icon: Landmark, text: "Choosing the right travel agents..." };
  }
  if (lower.includes("knowledge") || lower.includes("trusted tourism")) {
    return { icon: BookOpen, text: "Checking trusted tourism knowledge..." };
  }
  if (lower.includes("building") || lower.includes("response")) {
    return { icon: Sparkles, text: "Almost ready..." };
  }
  if (lower.includes("understanding") || lower.includes("planning")) {
    return { icon: Plane, text: "Planning your trip..." };
  }

  return { icon: Bot, text: "Thinking..." };
};

export function ChatLoadingIndicator({ stage }: ChatLoadingIndicatorProps) {
  const { icon: Icon, text } = getStageDisplay(stage);

  return (
    <div className="flex gap-3 text-left max-w-3xl mx-auto">
      <div className="w-8.5 h-8.5 rounded-xl bg-teal-600 text-white flex items-center justify-center flex-shrink-0 mt-1 shadow-sm shadow-teal-500/10">
        <Sparkles className="w-4.5 h-4.5" />
      </div>

      <div className="w-full max-w-sm rounded-2xl rounded-bl-none border border-slate-200/60 bg-white p-5 text-center shadow-sm dark:border-slate-800/80 dark:bg-[#111827]">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl border border-teal-100 bg-teal-50 text-teal-700 shadow-sm dark:border-teal-900/40 dark:bg-teal-950/25 dark:text-teal-300">
          <Icon className="h-7 w-7 animate-pulse" />
        </div>

        <div className="space-y-1">
          <p className="text-sm font-extrabold text-slate-850 dark:text-slate-100">
            {text}
          </p>
          <p className="text-[11px] font-semibold text-slate-400">
            This usually takes a few seconds.
          </p>
        </div>

        <div className="mt-4 flex items-center justify-center gap-1">
          {[0, 1, 2].map((dot) => (
            <span
              key={dot}
              className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-bounce"
              style={{ animationDelay: `${dot * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
