"use client";
import { api } from "./api";

/** PENDING CONTRACT: `POST /v1/admin/media` (multipart `file`) → `{key}`. Not in openapi.json yet; needs backend + regeneration. */
export async function uploadMedia(file: File): Promise<{ key: string }> {
  const body = new FormData();
  body.append("file", file);
  return api.raw<{ key: string }>("POST", "/v1/admin/media", { body });
}
