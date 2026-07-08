import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the four cockpit regions", () => {
    render(<App />);

    expect(screen.getByRole("complementary", { name: "章节" })).toBeInTheDocument();
    expect(screen.getByRole("main", { name: "正文" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "模块" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Agent 创作后台" })).toBeInTheDocument();
  });
});
