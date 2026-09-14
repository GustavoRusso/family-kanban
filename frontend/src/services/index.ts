// Single entry point for every backend call in the app.

import { createApiService } from "./api/api-service";
import type { KanbanService } from "./types";

export const services: KanbanService = createApiService();

export * from "./types";
export * from "./rules";
