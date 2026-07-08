import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

function makeProject() {
  return {
    id: 42,
    title: "废城修书人",
    idea: "一个失忆修书人在废城里修补会改变现实的书",
    positioning: "悬念长篇",
    worldview: "书会改写现实",
    main_plot: "主角追查书的规则",
    chapters: [
      {
        id: 100,
        project_id: 42,
        number: 1,
        title: "异常出现",
        status: "not_generated",
        content: null,
        generated_content: null,
        summary: null,
      },
    ],
    characters: [],
    foreshadowing_items: [],
    inspirations: [],
  };
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders the four cockpit regions", () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("[]", { status: 200 }));
    render(<App />);

    expect(screen.getByRole("complementary", { name: "章节" })).toBeInTheDocument();
    expect(screen.getByRole("main", { name: "正文" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "模块" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Agent 创作后台" })).toBeInTheDocument();
  });

  it("loads the newest existing project on startup", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByRole("button", { name: /异常出现/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "异常出现" })).toBeInTheDocument();
  });

  it("shows an error when project creation fails", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      if (init?.method === "POST") {
        return Promise.resolve(new Response("backend down", { status: 500, statusText: "Internal Server Error" }));
      }
      return Promise.resolve(new Response("[]", { status: 200 }));
    });
    render(<App />);

    fireEvent.change(screen.getByLabelText("小说想法"), {
      target: { value: "一个失忆修书人在废城里修补会改变现实的书" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "生成项目" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("backend down");
    });
  });
});
