import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Employa - Firebase Hosting Spike",
  description: "Testing Next.js 15 SSR with Firebase Hosting and Secret Manager",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
