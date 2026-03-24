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

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export const DOC_TYPE_LABELS: Record<string, string> = {
  drawing: "Drawing",
  specification: "Specification",
  rfi: "RFI",
  submittal: "Submittal",
  daily_report: "Daily Report",
  meeting_minutes: "Meeting Minutes",
  safety: "Safety",
  change_order: "Change Order",
  general: "General",
};

export const VISIBILITY_LABELS: Record<string, string> = {
  project_full: "Full Project",
  field_team: "Field Team",
  trade_scoped: "Trade Scoped",
  owner_shared: "Owner Shared",
  management_only: "Management Only",
};

export const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  project_manager: "Project Manager",
  superintendent: "Superintendent",
  subcontractor: "Subcontractor",
  owner_viewer: "Owner / Viewer",
};

export const STATUS_COLORS: Record<string, string> = {
  processing: "badge-processing",
  ready: "badge-approved",
  error: "badge-error",
  rendering_pages: "badge-processing",
  extracting_text: "badge-processing",
  vlm_processing: "badge-processing",
  chunking: "badge-processing",
  embedding: "badge-processing",
};
