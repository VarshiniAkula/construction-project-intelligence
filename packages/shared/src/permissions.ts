import { ProjectRole } from "./roles";

export const ROLE_PERMISSIONS: Record<string, Set<string>> = {
  [ProjectRole.ADMIN]: new Set([
    "project.create", "project.edit", "project.view",
    "member.manage", "member.view",
    "document.upload", "document.view", "document.manage_visibility",
    "chat.query",
    "audit.view",
  ]),
  [ProjectRole.PROJECT_MANAGER]: new Set([
    "project.edit", "project.view",
    "member.manage", "member.view",
    "document.upload", "document.view", "document.manage_visibility",
    "chat.query",
    "audit.view",
  ]),
  [ProjectRole.SUPERINTENDENT]: new Set([
    "project.view",
    "member.view",
    "document.upload", "document.view",
    "chat.query",
  ]),
  [ProjectRole.SUBCONTRACTOR]: new Set([
    "project.view",
    "document.upload", "document.view",
    "chat.query",
  ]),
  [ProjectRole.OWNER_VIEWER]: new Set([
    "project.view",
    "document.view",
    "chat.query",
  ]),
};
