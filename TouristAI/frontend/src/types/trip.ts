export interface NormalizedTicket {
  id: string;
  mode: 'Flight' | 'Train' | 'Bus';
  carrier: string;
  vehicle_type: string;
  departure: string;
  arrival: string;
  duration: string;
  price: number;
  currency: string;
  rating: number;
  score: number;
  booking_source: string;
  booking_url: string;
  last_updated: string;
}

export interface TransportStatus {
  status: 'success' | 'failed';
  reason: string;
  last_updated: string;
}
