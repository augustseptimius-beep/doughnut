"use client";

import { BaselineProvider } from "@/lib/baseline-context";

export default function Providers({ children }: { children: React.ReactNode }) {
  return <BaselineProvider>{children}</BaselineProvider>;
}
