import { afterEach, describe, expect, it, vi } from "vitest";

import { getSummary, queryString } from "./api.js";

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("serializes shared filters and omits blank optional values", () => {
    expect(
      queryString({
        start_date: "2025-01-01",
        end_date: "2025-12-31",
        min_magnitude: "",
        include_assignments: true,
      }),
    ).toBe("?start_date=2025-01-01&end_date=2025-12-31&include_assignments=true");
  });

  it("calls the summary endpoint with the same filter parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ record_count: 794 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getSummary({ start_date: "2025-01-01", end_date: "2025-12-31" })).resolves.toEqual({ record_count: 794 });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/analytics/summary?start_date=2025-01-01&end_date=2025-12-31",
    );
  });

  it("preserves safe database error status for the UI", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ detail: "Database is not ready" }),
      }),
    );

    await expect(getSummary({})).rejects.toMatchObject({ status: 503, message: "Database is not ready" });
  });
});
