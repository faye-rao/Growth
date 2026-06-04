import { create } from "zustand";

interface AppState {
  locale: string;
  setLocale: (l: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  locale: "en",
  setLocale: (locale) => set({ locale }),
}));
