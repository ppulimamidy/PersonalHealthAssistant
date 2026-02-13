import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

export type HealthStatus = "excellent" | "good" | "moderate" | "poor" | "critical";

export function getHealthStatus(score: number): HealthStatus {
  if (score >= 85) return "excellent";
  if (score >= 70) return "good";
  if (score >= 55) return "moderate";
  if (score >= 40) return "poor";
  return "critical";
}

export function getHealthColor(status: string): string {
  const colors: Record<string, string> = {
    excellent: "text-health-excellent",
    good: "text-health-good",
    moderate: "text-health-moderate",
    poor: "text-health-poor",
    critical: "text-health-critical",
  };
  return colors[status] || "text-slate-500";
}

export function getHealthBgColor(status: string): string {
  const colors: Record<string, string> = {
    excellent: "bg-health-excellent",
    good: "bg-health-good",
    moderate: "bg-health-moderate",
    poor: "bg-health-poor",
    critical: "bg-health-critical",
  };
  return colors[status] || "bg-slate-500";
}
