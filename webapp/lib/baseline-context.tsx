"use client";

import { createContext, useContext, useState } from "react";

export type BaselineMode = "avg" | "top10" | "kommunegruppe";

interface BaselineContextValue {
  mode: BaselineMode;
  setMode: (mode: BaselineMode) => void;
}

const BaselineContext = createContext<BaselineContextValue>({
  mode: "kommunegruppe",
  setMode: () => {},
});

export function BaselineProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<BaselineMode>("kommunegruppe");
  return (
    <BaselineContext.Provider value={{ mode, setMode }}>
      {children}
    </BaselineContext.Provider>
  );
}

export function useBaseline() {
  return useContext(BaselineContext);
}
