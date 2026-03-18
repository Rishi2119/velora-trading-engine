import { create } from 'zustand';

interface TradingState {
  disciplineScore: number;
  dailyStreak: number;
  motivationalQuote: string;
  setDisciplineScore: (score: number) => void;
}

export const useTradingStore = create<TradingState>((set) => ({
  disciplineScore: 89,
  dailyStreak: 14,
  motivationalQuote: 'Discipline beats emotion.',
  setDisciplineScore: (score) => set({ disciplineScore: score }),
}));
