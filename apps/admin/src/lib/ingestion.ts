"use client";
import type { components } from "@dtmai/api-client";
import { api } from "./api";

type S = components["schemas"];
export type Batch = S["BatchOut"];
export type BatchDetail = S["BatchDetail"];
export type BatchIn = S["BatchIn"];

/** Multipart fields of POST /v1/admin/ingestion/batches/upload (files repeated under the `files` key). */
export type UploadIn = Omit<BatchIn, "root" | "type_ids"> & { files: File[] };

function toForm({ files, ...rest }: UploadIn): FormData {
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.name);
  for (const [k, v] of Object.entries(rest)) if (v !== null && v !== undefined && v !== "") fd.append(k, String(v));
  return fd;
}
const A = api.client;
const u = api.unwrap;

export const ingestion = {
  list: (limit = 100, include_archived = false) => u(A.GET("/v1/admin/ingestion/batches", { params: { query: { limit, include_archived } } })),
  archive: (batch_id: string) => u(A.POST("/v1/admin/ingestion/batches/{batch_id}/archive", { params: { path: { batch_id } } })),
  unarchive: (batch_id: string) => u(A.POST("/v1/admin/ingestion/batches/{batch_id}/unarchive", { params: { path: { batch_id } } })),
  get: (batch_id: string) => u(A.GET("/v1/admin/ingestion/batches/{batch_id}", { params: { path: { batch_id } } })),
  start: (body: BatchIn) => u(A.POST("/v1/admin/ingestion/batches", { body })),
  upload: (body: UploadIn) =>
    u(
      A.POST("/v1/admin/ingestion/batches/upload", {
        // Multipart: the browser sets the boundary; the generated JSON body type is bypassed by the serializer.
        body: toForm(body) as never,
        bodySerializer: (b: unknown) => b as FormData,
      }),
    ),
  rerun: (batch_id: string, include_unfinished: boolean) =>
    u(A.POST("/v1/admin/ingestion/batches/{batch_id}/rerun", { params: { path: { batch_id } }, body: { include_unfinished } })),
};
