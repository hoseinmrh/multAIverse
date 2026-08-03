import type { Metadata } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";

import { Providers } from "@/app/providers";

import "./globals.css";

const description =
  "A local-first fictional alternate-life simulator for exploring decisions, trade-offs, and possible futures.";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") ? "http" : "https");
  const metadataBase = new URL(`${protocol}://${host}`);
  return {
    metadataBase,
    title: { default: "Multiverse", template: "%s · Multiverse" },
    description,
    openGraph: {
      title: "Multiverse — One choice. Three possible futures.",
      description,
      images: [
        {
          url: "/og.png",
          width: 1536,
          height: 1024,
          alt: "Three futures branching from one decision",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "Multiverse — One choice. Three possible futures.",
      description,
      images: ["/og.png"],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
