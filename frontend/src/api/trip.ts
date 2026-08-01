import axios from 'axios';
import type { TripCreateRequest, TripResponse } from '../types/trip';

// Base URL of the FastAPI backend (adjust if needed)
const BASE_URL = process.env.REACT_APP_BACKEND_URL ?? 'http://localhost:8000';

/**
 * Create a new trip planning request.
 * Returns the generated trip ID and initial status.
 */
export async function createTrip(data: TripCreateRequest): Promise<TripResponse> {
  const response = await axios.post<TripResponse>(`${BASE_URL}/trip`, data);
  return response.data;
}

/**
 * Retrieve the current state of an existing trip.
 */
export async function getTrip(tripId: string): Promise<TripResponse> {
  const response = await axios.get<TripResponse>(`${BASE_URL}/trip/${tripId}`);
  return response.data;
}

/**
 * Subscribe to real‑time trip events via WebSocket.
 * Calls the provided callback for each incoming message.
 */
export function subscribeToTripEvents(
  tripId: string,
  onMessage: (event: MessageEvent) => void,
  onError?: (ev: Event) => void,
  onClose?: (ev: CloseEvent) => void
): WebSocket {
  const ws = new WebSocket(`${BASE_URL.replace(/^http/, 'ws')}/ws/trip/${tripId}`);
  ws.onmessage = onMessage;
  if (onError) ws.onerror = onError;
  if (onClose) ws.onclose = onClose;
  return ws;
}
