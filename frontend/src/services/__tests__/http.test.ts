import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createApiService } from "../api/api-service";
import { api, getAccessToken, setAccessToken } from "../api/http";
import { RuleError } from "../types";

function installLocalStorage() {
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear(),
  });
}

beforeEach(() => {
  installLocalStorage();
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("api http helper", () => {
  it("throws RuleError with the API message on 400", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ message: "Enter a valid email address." }), {
        status: 400,
        statusText: "Bad Request",
      }),
    );

    const error = await api("POST", "/auth/code", { email: "nope" }).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(RuleError);
    expect(error).toHaveProperty("message", "Enter a valid email address.");
  });

  it("attaches the Bearer token on authenticated calls", async () => {
    setAccessToken("tok-abc");
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200 }),
    );

    await api("GET", "/families");

    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/families",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer tok-abc" }),
      }),
    );
  });

  it("stores the access token after verifyCode", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          user: { id: "u1", email: "maya@example.com", name: "maya" },
          activeFamilyId: null,
          accessToken: "access-xyz",
        }),
        { status: 200 },
      ),
    );

    const session = await createApiService().auth.verifyCode("maya@example.com", "123456");

    expect(getAccessToken()).toBe("access-xyz");
    expect(session).toEqual({
      user: { id: "u1", email: "maya@example.com", name: "maya" },
      activeFamilyId: null,
    });
  });
});
