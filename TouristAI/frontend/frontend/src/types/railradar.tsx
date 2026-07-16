export interface Station {
  code: string;
  name: string;
}

export type RunDay = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export interface TrainSummary {
  number: string;
  name: string;
  type: string;
  runDays: RunDay[];
}

export interface TrainStop {
  departure?: string;
  arrival?: string;
  day: number;
  sequence: number;
}

export interface LiveInfo {
  type: "upcoming" | "running" | "departed" | "arrived" | string;
  startDate: string;
  expectedArrivalTime?: string;
  expectedDepartureTime?: string;
  platform?: string;
  delayMinutes?: number;
}

export interface TrainBetweenStations {
  train: TrainSummary;
  from: TrainStop;
  to: TrainStop;
  distance: number;
  duration: number; // minutes
  totalHaltsBetween: number;
  live?: LiveInfo;
}

export interface TrainsBetweenResponse {
  from: Station;
  to: Station;
  count: number;
  trains: TrainBetweenStations[];
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: { code: string; message: string };
}
