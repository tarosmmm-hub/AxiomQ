"use client";

import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "./client";

export const queryKeys = {
  me: ["me"] as const,
  workspaces: ["me", "workspaces"] as const,
  entitlements: ["me", "entitlements"] as const,
};

export function useMe() {
  return useQuery({ queryKey: queryKeys.me, queryFn: () => unwrap(api.GET("/api/v1/me")) });
}

export function useWorkspaces() {
  return useQuery({
    queryKey: queryKeys.workspaces,
    queryFn: () => unwrap(api.GET("/api/v1/me/workspaces")),
  });
}

export function useEntitlements() {
  return useQuery({
    queryKey: queryKeys.entitlements,
    queryFn: () => unwrap(api.GET("/api/v1/me/entitlements")),
  });
}
