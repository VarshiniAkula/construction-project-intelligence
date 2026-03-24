export enum DocType {
  DRAWING = "drawing",
  SPECIFICATION = "specification",
  RFI = "rfi",
  SUBMITTAL = "submittal",
  DAILY_REPORT = "daily_report",
  MEETING_MINUTES = "meeting_minutes",
  SAFETY = "safety",
  CHANGE_ORDER = "change_order",
  GENERAL = "general",
}

export const DOC_TYPE_LABELS: Record<string, string> = {
  [DocType.DRAWING]: "Drawing",
  [DocType.SPECIFICATION]: "Specification",
  [DocType.RFI]: "RFI",
  [DocType.SUBMITTAL]: "Submittal",
  [DocType.DAILY_REPORT]: "Daily Report",
  [DocType.MEETING_MINUTES]: "Meeting Minutes",
  [DocType.SAFETY]: "Safety",
  [DocType.CHANGE_ORDER]: "Change Order",
  [DocType.GENERAL]: "General",
};
