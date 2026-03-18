export type SubscriptionPlan = 'free' | 'pro' | 'premium';

export interface UserProfile {
  id: string;
  full_name: string | null;
  discipline_score: number;
  daily_streak: number;
  quote_of_day: string;
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  pnl: number | null;
  opened_at: string;
}
