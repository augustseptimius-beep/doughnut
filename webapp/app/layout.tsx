import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Doughnut Economics — Danmark",
  description:
    "Doughnut Economics dashboard for alle 98 danske kommuner baseret på data fra Danmarks Statistik",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="da">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-3 no-underline">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-emerald-600">
                <div className="h-4 w-4 rounded-full border-2 border-amber-400" />
              </div>
              <h1 className="text-lg font-semibold text-gray-900">
                Doughnut Economics — Danmark
              </h1>
            </a>
            <nav className="flex items-center gap-5 text-sm">
              <a href="/" className="text-gray-500 hover:text-gray-900 transition-colors">
                Kommuner
              </a>
              <a href="/metode" className="text-gray-500 hover:text-gray-900 transition-colors">
                Metode & data
              </a>
              <a href="/om" className="text-gray-500 hover:text-gray-900 transition-colors">
                Om platformen
              </a>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>

        <footer className="border-t border-gray-200 bg-white mt-12">
          <div className="mx-auto max-w-6xl px-4 py-4 text-center text-xs text-gray-500">
            Data:{" "}
            <a
              href="https://www.dst.dk"
              className="underline hover:text-gray-700"
              target="_blank"
              rel="noopener"
            >
              Danmarks Statistik
            </a>{" "}
            (CC BY 4.0) &middot; Seneste datapunkt: 2022-2023 &middot; Metodik:{" "}
            <a
              href="/om"
              className="underline hover:text-gray-700"
            >
              Doughnut Economics v4.1
            </a>{" "}
            &middot;{" "}
            <a
              href="https://doughnuteconomics.org"
              className="underline hover:text-gray-700"
              target="_blank"
              rel="noopener"
            >
              doughnuteconomics.org
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
