import type { Metadata } from "next";
import type React from "react";
import "./globals.css";
import { Inter } from "next/font/google";
import { Footer } from "@/components/footer";
import { Header } from "@/components/header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
	description: "Created with v0",
	generator: "v0.dev",
	title: "v0 App",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en">
			<body className={inter.className}>
				<Header />
				{children}
				<Footer />
			</body>
		</html>
	);
}
