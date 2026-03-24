export enum ProjectRole {
  ADMIN = "admin",
  PROJECT_MANAGER = "project_manager",
  SUPERINTENDENT = "superintendent",
  SUBCONTRACTOR = "subcontractor",
  OWNER_VIEWER = "owner_viewer",
}

export const ROLE_LABELS: Record<string, string> = {
  [ProjectRole.ADMIN]: "Admin",
  [ProjectRole.PROJECT_MANAGER]: "Project Manager",
  [ProjectRole.SUPERINTENDENT]: "Superintendent",
  [ProjectRole.SUBCONTRACTOR]: "Subcontractor",
  [ProjectRole.OWNER_VIEWER]: "Owner / Viewer",
};
