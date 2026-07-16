import axios from "axios";
import type { ApiEnvelope, Station, TrainsBetweenResponse } from "../types/railradar"

// Points at OUR backend (see /backend folder), never at railradar.in directly —
// keeps the RailRadar API key server-side only.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const http = axios.create({
    baseURL: BASE_URL,
    timeout: 15000,
});

function unwrap<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
    return promise.then((res) => {
        if (!res.data.success) {
            throw new Error(res.data.error?.message || "Request failed");
        }
        return res.data.data;
    });
}

export const railradarApi = {
    /** Full station code -> name map (use for building your own autocomplete cache). */
    getAllStations(): Promise<Record<string, string>> {
        return unwrap(http.get("/stations/lookup"));
    },

    /** Server-side filtered station autocomplete. */
    searchStations(query: string): Promise<Station[]> {
        return unwrap(http.get("/stations/search", { params: { q: query } }));
    },

    /** All trains running between two station codes. */
    getTrainsBetween(
        from: string,
        to: string,
        opts: { date?: string; live?: boolean } = {}
    ): Promise<TrainsBetweenResponse> {
        return unwrap(
            http.get("/trains/between", {
                params: { from, to, date: opts.date, live: opts.live },
            })
        );
    },

    /** Live GPS/delay status for a single train. */
    getTrainLiveStatus(trainNumber: string) {
        return unwrap(http.get(`/trains/${trainNumber}/live`));
    },

    /** Full schedule/stops for a single train. */
    getTrainDetails(trainNumber: string) {
        return unwrap(http.get(`/trains/${trainNumber}`));
    },

    /** All trains halting at a station. */
    getStationBoard(stationCode: string) {
        return unwrap(http.get(`/stations/${stationCode}/board`));
    },
};
