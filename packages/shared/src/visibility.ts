import { ProjectRole } from "./roles";

export enum VisibilityScope {
  PROJECT_FULL = "project_full",
  FIELD_TEAM = "field_team",
  TRADE_SCOPED = "trade_scoped",
  OWNER_SHARED = "owner_shared",
  MANAGEMENT_ONLY = "management_only",
}

export const VISIBILITY_LABELS: Record<string, string> = {
  [VisibilityScope.PROJECT_FULL]: "Full Project",
  [VisibilityScope.FIELD_TEAM]: "Field Team",
  [VisibilityScope.TRADE_SCOPED]: "Trade Scoped",
  [VisibilityScope.OWNER_SHARED]: "Owner Shared",
  [VisibilityScope.MANAGEMENT_ONLY]: "Management Only",
};

export const ROLE_VISIBILITY_MAP: Record<string, Set<VisibilityScope>> = {
  [ProjectRole.ADMIN]: new Set(Object.values(VisibilityScope)),
  [ProjectRole.PROJECT_MANAGER]: new Set(Object.values(VisibilityScope)),
  [ProjectRole.SUPERINTENDENT]: new Set([
    VisibilityScope.PROJECT_FULL,
    VisibilityScope.FIELD_TEAM,
    VisibilityScope.TRADE_SCOPED,
    VisibilityScope.OWNER_SHARED,
  ]),
  [ProjectRole.SUBCONTRACTOR]: new Set([
    VisibilityScope.FIELD_TEAM,
    VisibilityScope.TRADE_SCOPED,
  ]),
  [ProjectRole.OWNER_VIEWER]: new Set([VisibilityScope.OWNER_SHARED]),
};
