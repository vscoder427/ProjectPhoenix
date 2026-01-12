import type { Metadata } from "next";
import "./globals.css";
import { WebVitals } from "@/src/components/web-vitals";

export const metadata: Metadata = {
  title: "Employa - Recovery-Focused Job Search",
  description: "Find recovery-friendly employers and take the next step in your career journey",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <WebVitals />
        {children}
      </body>
    </html>
  );
}
