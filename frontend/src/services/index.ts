// Single entry point for every backend call in the app.
// Swap the implementation here when a real backend arrives.

import { createMockService } from "./mock/mock-service";
import type { KanbanService } from "./types";

export const services: KanbanService = createMockService();

export * from "./types";
export * from "./rules";
export { createMockService };
