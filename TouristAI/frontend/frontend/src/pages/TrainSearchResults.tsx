import React from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Train, ExternalLink, ShieldAlert } from "lucide-react";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export const TrainSearchResults: React.FC = () => {
  const { from, to } = useParams<{ from: string; to: string }>();
  const [searchParams] = useSearchParams();
  const date = searchParams.get("date") || todayISO();
  const navigate = useNavigate();

  const fromName = searchParams.get("fromName") || from || "";
  const toName = searchParams.get("toName") || to || "";

  const formatConfirmTktDate = (dateStr: string) => {
    if (!dateStr) return "";
    const parts = dateStr.split("-");
    if (parts.length !== 3) return "";
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  };

  const handleBookRedirect = () => {
    if (!from || !to) return;
    const formattedDate = formatConfirmTktDate(date);
    const queryUrl = `https://www.confirmtkt.com/rbooking/trains/from/${from.toUpperCase()}/to/${to.toUpperCase()}/${formattedDate}`;
    window.open(queryUrl, "_blank");
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200 text-left pb-16">
      {/* Route Breadcrumb Header */}
      <div className="flex items-center justify-between bg-emerald-600 px-6 py-3 shadow-md">
        <div className="flex items-center gap-3 text-sm font-semibold text-white">
          <button onClick={() => navigate("/trains")} aria-label="Go back" className="hover:opacity-85">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <span className="flex items-center gap-1.5 font-heading capitalize">
            <Train className="h-4 w-4" />
            Trains: {fromName} ⇄ {toName}
          </span>
          <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-mono">
            {date}
          </span>
        </div>
      </div>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {/* Prominent ConfirmTkt search card */}
        <div className="mb-6 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Train className="h-4 w-4 text-emerald-400" />
            Search Directly on ConfirmTkt
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed capitalize">
            Click below to open ConfirmTkt with your pre-filled search for{" "}
            <span className="font-bold text-slate-200">{fromName} ⇄ {toName}</span>.
          </p>
          <button
            onClick={handleBookRedirect}
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors"
          >
            Search on ConfirmTkt
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* RED WARNING MESSAGE BOX */}
        <div className="rounded-2xl border border-red-500/20 bg-red-950/10 p-5 text-center my-8">
          <ShieldAlert className="mx-auto h-10 w-10 text-red-500 mb-3" />
          <h4 className="text-sm font-bold text-slate-200">Unable to load live train schedules</h4>
          <p className="text-xs text-slate-450 mt-1">
            Please use the search card above to open ConfirmTkt directly and view live schedules, seat availability, and book tickets.
          </p>
        </div>
      </main>
    </div>
  );
};

export default TrainSearchResults;
