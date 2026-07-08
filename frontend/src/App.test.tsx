import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders the four cockpit regions", () => {
    render(<App />);

    expect(screen.getByRole("complementary", { name: "章节" })).toBeInTheDocument();
    expect(screen.getByRole("main", { name: "正文" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "模块" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Agent 创作后台" })).toBeInTheDocument();
  });

  it("shows an error when project creation fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("backend down", { status: 500, statusText: "Internal Server Error" }),
    );
    render(<App />);

    fireEvent.change(screen.getByLabelText("小说想法"), {
      target: { value: "一个失忆修书人在废城里修补会改变现实的书" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成项目" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("backend down");
    });
  });
});
