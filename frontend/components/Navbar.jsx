"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Menu, X, User } from "lucide-react";
import Button from "./Button";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [hasProject, setHasProject] = useState(false);

  useEffect(() => {
    // Check for logged in user
    const userData = localStorage.getItem("dc_user");
    if (userData) setUser(JSON.parse(userData));
    const projects = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    setHasProject(Object.keys(projects).length > 0);
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("dc_user");
    setUser(null);
    window.location.href = "/";
  };

  return (
    <nav className="bg-white/95 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-brand-emerald to-brand-forest rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">DC</span>
            </div>
            <span className="font-bold text-xl text-gray-900">DhatuChakr</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="text-gray-700 hover:text-brand-emerald transition-colors"
            >
              Home
            </Link>
            <Link
              href="/goal-scope"
              className="text-gray-700 hover:text-brand-emerald transition-colors"
            >
              Goal & Scope
            </Link>
            {user && (
              <Link
                href="/dashboard"
                className="text-gray-700 hover:text-brand-emerald transition-colors"
              >
                Dashboard
              </Link>
            )}
            <Link
              href="/projects/new"
              className="text-gray-700 hover:text-brand-emerald transition-colors"
            >
              New Project
            </Link>
            <span
              className={`text-gray-400 ${
                hasProject ? "" : "cursor-not-allowed"
              }`}
            >
              |
            </span>
            <Link
              href={
                hasProject
                  ? "/projects/" +
                    Object.keys(
                      JSON.parse(localStorage.getItem("dc_projects") || "{}")
                    )[0] +
                    "/results"
                  : "#"
              }
              className={`transition-colors ${
                hasProject
                  ? "text-gray-700 hover:text-brand-emerald"
                  : "text-gray-400 pointer-events-none"
              }`}
            >
              Results
            </Link>

            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-700 text-sm">
                  Welcome, {user.name}
                </span>
                <Button variant="outline" size="sm" onClick={handleSignOut}>
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link href="/auth/signin">
                  <Button variant="ghost" size="sm">
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
              className="p-2 rounded-md text-gray-700 hover:text-brand-emerald"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 border-t border-gray-100">
            <div className="flex flex-col space-y-4">
              <Link
                href="/"
                className="text-gray-700 hover:text-brand-emerald transition-colors"
              >
                Home
              </Link>
              <Link
                href="/goal-scope"
                className="text-gray-700 hover:text-brand-emerald transition-colors"
              >
                Goal & Scope
              </Link>
              {user && (
                <Link
                  href="/dashboard"
                  className="text-gray-700 hover:text-brand-emerald transition-colors"
                >
                  Dashboard
                </Link>
              )}
              <Link
                href="/projects/new"
                className="text-gray-700 hover:text-brand-emerald transition-colors"
              >
                New Project
              </Link>

              {user ? (
                <div className="flex flex-col space-y-2">
                  <span className="text-gray-700 text-sm">
                    Welcome, {user.name}
                  </span>
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
                    <Button variant="ghost" size="sm" className="w-fit">
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
