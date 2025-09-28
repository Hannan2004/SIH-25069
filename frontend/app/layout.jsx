import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { UserProvider } from "@/context/UserContext";

export const metadata = {
  title: "DhatuChakr - AI-Assisted LCA for Metals",
  description:
    "India-first Life Cycle Assessment platform for Aluminium, Copper & Critical Minerals with AI-powered gap filling and compliance-ready reporting.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <meta name="theme-color" content="#0B3D2E" />
      </head>
      <body className="min-h-screen flex flex-col">
        <UserProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </UserProvider>
      </body>
    </html>
  );
}
