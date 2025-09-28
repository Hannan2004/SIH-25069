"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Menu, X, User } from "lucide-react";
import { useUser } from "@/context/UserContext";
import Button from "./Button";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, signOut } = useUser();

  const handleSignOut = async () => {
    await signOut();
    window.location.href = "/";
  };

  return (
    <nav className="bg-brand-blue text-white border-b border-brand-blue/70 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <span className="w-12 h-12 rounded-full bg-white shadow flex items-center justify-center ring-1 ring-white/40 overflow-hidden">
              <Image
                src="/DhatuChakr-logo.png"
                width={48}
                height={48}
                alt="DhatuChakr Logo"
                className="object-contain"
                priority
              />
            </span>
            <span className="font-bold text-2xl text-white">DhatuChakr</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
            >
              Home
            </Link>
            <Link
              href="/goal-scope"
              className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
            >
              Goal & Scope
            </Link>
            {user && (
              <Link
                href="/dashboard"
                className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
              >
                Dashboard
              </Link>
            )}
            <Link
              href="/projects/new"
              className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:-bottom-1 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
            >
              New Project
            </Link>

            {user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {user.photoURL ? (
                    <Image
                      src={user.photoURL}
                      alt="User"
                      width={36}
                      height={36}
                      className="rounded-full object-cover border border-gray-200"
                    />
                  ) : (
                    <div className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center text-white/70">
                      <User className="w-5 h-5" />
                    </div>
                  )}
                  <span className="text-white text-sm max-w-[140px] truncate">
                    {user.name || user.email}
                  </span>
                </div>
                <Button variant="outline" size="sm" onClick={handleSignOut}>
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link href="/auth/signin">
                  <Button variant="ghost" size="sm" className="text-white">
                    Sign In
                  </Button>
                </Link>
                <Link href="/auth/signup">
                  <Button size="sm">Get Started</Button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-md text-white hover:text-brand-copper"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 border-t border-white/10 bg-brand-blue/95">
            <div className="flex flex-col space-y-4">
              <Link
                href="/"
                className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
              >
                Home
              </Link>
              <Link
                href="/goal-scope"
                className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
              >
                Goal & Scope
              </Link>
              {user && (
                <Link
                  href="/dashboard"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  Dashboard
                </Link>
              )}
              <Link
                href="/projects/new"
                className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
              >
                New Project
              </Link>

              {user ? (
                <div className="flex flex-col space-y-3">
                  <div className="flex items-center space-x-3">
                    {user.photoURL ? (
                      <Image
                        src={user.photoURL}
                        alt={user.name || "User"}
                        width={40}
                        height={40}
                        className="rounded-full object-cover border border-gray-200"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white/70">
                        <User className="w-5 h-5" />
                      </div>
                    )}
                    <div className="flex flex-col">
                      <span className="text-white text-sm font-medium leading-tight">
                        {user.name || user.email}
                      </span>
                      {user.org && (
                        <span className="text-[11px] text-white/60 truncate max-w-[160px]">
                          {user.org}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSignOut}
                    className="w-fit"
                  >
                    Sign Out
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col space-y-2">
                  <Link href="/auth/signin">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-fit text-white"
                    >
                      Sign In
                    </Button>
                  </Link>
                  <Link href="/auth/signup">
                    <Button size="sm" className="w-fit">
                      Get Started
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
