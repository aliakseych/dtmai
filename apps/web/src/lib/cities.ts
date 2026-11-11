import { api } from "./api";

export type { City } from "./api";

/** `GET /v1/lyceums/cities` (public), ordered by name. */
export const fetchCities = () => api.unwrap(api.client.GET("/v1/lyceums/cities"));
