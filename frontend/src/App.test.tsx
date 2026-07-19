import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AgentWorkspace } from "./components/AgentWorkspace";
import { ChapterEditor } from "./components/ChapterEditor";

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
        status: "generated" as const,
        content: null,
        generated_content: "雨水敲在废城图书馆的穹顶上。",
        summary: "主角确认修书会改写现实。",
      },
    ],
    characters: [
      {
        id: 1,
        name: "修书人",
        role: "主角",
        personality: "克制",
        current_goal: "查明修书代价",
        key_memories: "遗忘母亲声音",
        relationships: null,
        writing_notes: null,
        period_stage: "失忆追索期",
        period_summary: "刚确认修书会改变现实，目标从旁观转为主动追查。",
        period_source_chapter_id: 100,
      },
    ],
    foreshadowing_items: [
      {
        id: 1,
        content: "手背页码从 17 变为 16",
        status: "active",
        notes: null,
      },
    ],
    inspirations: [{ id: 1, content: "后续出现一本会写出未来的书", applied: false }],
    story_events: [
      {
        id: 1,
        project_id: 42,
        source_chapter_id: 100,
        title: "第 1 章：异常出现",
        summary: "修书人确认修书会改变现实。",
        characters: "修书人",
        location: "废城图书馆",
        consequence: "修书代价进入正式时间线。",
      },
    ],
    world_rules: [
      {
        id: 1,
        project_id: 42,
        source_chapter_id: null,
        rule: "修补书页会改写现实。",
        limitation: "每次修补都会丢失一段记忆。",
        exception: null,
        status: "active",
      },
    ],
  };
}

function makeProjectWithoutGeneratedContent() {
  const project = makeProject();
  return {
    ...project,
    chapters: project.chapters.map((chapter) => ({
      ...chapter,
      generated_content: null,
    })),
  };
}

function makeProjectWithAcceptedSecondChapter() {
  const project = makeProjectWithoutGeneratedContent();
  return {
    ...project,
    chapters: [
      {
        ...project.chapters[0],
        status: "accepted" as const,
        content: "chapter one accepted content",
        generated_content: null,
      },
      {
        id: 101,
        project_id: 42,
        number: 2,
        title: "Chapter Two",
        status: "accepted" as const,
        content: "chapter two accepted content",
        generated_content: null,
        summary: "chapter two summary",
      },
    ],
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
    expect(screen.getByLabelText("章节正文")).toHaveValue("雨水敲在废城图书馆的穹顶上。");
    expect(screen.queryByRole("region", { name: "生成结果" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "采纳" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "拒绝" })).toBeInTheDocument();
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

  it("places auto mode controls in the editor top toolbar", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByText("全自动")).toBeInTheDocument();
    expect(screen.getByText("开启后自动生成、审核、更新上下文并进入下一章")).toBeInTheDocument();
    expect(screen.getByLabelText("自动生成章数")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始全自动" })).toBeInTheDocument();
  });

  it("shows backstage flow context and combined result tabs", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByRole("tab", { name: "流程节点" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "上下文" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "结果与更新" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "上下文" }));
    expect(screen.getByText("压缩状态")).toBeInTheDocument();
    expect(screen.getAllByText("悬念长篇").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("书会改写现实").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("手背页码从 17 变为 16").length).toBeGreaterThanOrEqual(2);

    fireEvent.click(screen.getByRole("tab", { name: "结果与更新" }));
    expect(screen.getByText("审核结果")).toBeInTheDocument();
    expect(screen.getByText("章节摘要")).toBeInTheDocument();
    expect(screen.getByText("伏笔变化")).toBeInTheDocument();
    expect(screen.getByText("角色卡变化")).toBeInTheDocument();
    expect(screen.getByText("后续线路变化")).toBeInTheDocument();
    expect(screen.getByText("入库动作")).toBeInTheDocument();
  });

  it("switches the backstage detail when a flow node is clicked", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByRole("button", { name: /1.*加载上下文/ })).toBeInTheDocument();
    expect(screen.getByText("读取本章生成所需的正式上下文包")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /9.*判断后续线路调整/ }));

    expect(screen.getByText("根据本章实际结果判断后续章节名和线路是否需要改变")).toBeInTheDocument();
    expect(screen.getByText(/第 4 章标题/)).toBeInTheDocument();
  });

  it("renders real generation step snapshots in the backstage", () => {
    const task = {
      id: 7,
      project_id: 42,
      chapter_id: 100,
      kind: "chapter_generation",
      status: "completed",
      current_step: "persist_candidate_result",
      error_type: null,
      error_message: null,
      chapter: makeProject().chapters[0],
      steps: [
        {
          id: 1,
          task_id: 7,
          name: "load_context",
          status: "completed",
          error_message: null,
          input_snapshot: { chapter_id: 100 },
          output_snapshot: {
            context_package: {
              positioning: "真实定位",
              worldview: "真实世界观",
              main_plot: "真实主线",
              characters: [{ name: "真实角色", current_goal: "真实目标" }],
              foreshadowing_items: [{ content: "真实伏笔" }],
              chapter_summaries: ["真实摘要"],
              inspirations: ["真实灵感"],
            },
          },
        },
        {
          id: 2,
          task_id: 7,
          name: "build_candidate_result",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            candidate_result: {
              summary: "真实候选摘要",
              audit: { findings: [{ message: "真实审核发现", blocking: false }] },
              foreshadowing: { advanced: ["真实伏笔推进"] },
              character_period: { updates: ["真实角色更新"] },
              future_plan: { suggestions: [{ change: "真实线路调整" }] },
            },
          },
        },
        {
          id: 3,
          task_id: 7,
          name: "persist_candidate_result",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            persistence_result: {
              saved_candidate: true,
              saved_summary: true,
              official_content_committed: false,
            },
          },
        },
      ],
    };

    render(
      <AgentWorkspace
        project={makeProject()}
        task={task}
        busy={false}
        collapsed={false}
        onToggleCollapsed={() => undefined}
        onRetry={() => undefined}
      />,
    );

    const completedNode = screen.getByRole("button", { name: /1.*加载上下文.*完成/ });
    expect(completedNode).toBeInTheDocument();
    expect(completedNode).not.toHaveTextContent("完成");
    expect(screen.getAllByText(/真实定位/).length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getByRole("tab", { name: "上下文" }));
    expect(screen.getByText("真实世界观")).toBeInTheDocument();
    expect(screen.getByText("真实伏笔")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "结果与更新" }));
    expect(screen.getByText(/真实审核发现/)).toBeInTheDocument();
    expect(screen.getByText("真实候选摘要")).toBeInTheDocument();
    expect(screen.getByText(/真实伏笔推进/)).toBeInTheDocument();
    expect(screen.getByText(/真实角色更新/)).toBeInTheDocument();
    expect(screen.getByText(/真实线路调整/)).toBeInTheDocument();
  });

  it("shows structured memory in the module panel and backstage context", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByText("失忆追索期")).toBeInTheDocument();
    expect(screen.getByText("事件时间线")).toBeInTheDocument();
    expect(screen.getByText("修书人确认修书会改变现实。")).toBeInTheDocument();
    expect(screen.getByText("世界观规则")).toBeInTheDocument();
    expect(screen.getByText("修补书页会改写现实。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "上下文" }));
    expect(screen.getAllByText(/失忆追索期/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/修书人确认修书会改变现实/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/修补书页会改写现实/).length).toBeGreaterThanOrEqual(1);
  });

  it("collapses and expands the backstage", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    const workspace = await screen.findByRole("region", { name: "Agent 创作后台" });
    expect(screen.getByRole("tab", { name: "流程节点" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "收起后台" }));

    expect(workspace).toHaveClass("collapsed");
    expect(screen.queryByRole("tab", { name: "流程节点" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "展开后台" })).toBeInTheDocument();
  });

  it("updates generation progress from the streaming endpoint", async () => {
    const encoder = new TextEncoder();
    const task = {
      id: 9,
      project_id: 42,
      chapter_id: 100,
      kind: "chapter_generation",
      status: "running",
      current_step: "load_context",
      error_type: null,
      error_message: null,
      chapter: makeProject().chapters[0],
      steps: [
        {
          id: 1,
          task_id: 9,
          name: "load_context",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { context_package: { worldview: "流式世界观" } },
          error_message: null,
        },
        {
          id: 2,
          task_id: 9,
          name: "generate_prose",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { generated_content: "流式正文候选第一段。" },
          error_message: null,
        },
      ],
    };
    const completed = {
      ...task,
      status: "completed",
      current_step: "persist_candidate_result",
      steps: [
        ...task.steps,
        {
          id: 3,
          task_id: 9,
          name: "persist_candidate_result",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { persistence_result: { saved_candidate: true } },
          error_message: null,
        },
      ],
    };

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/projects") {
        return Promise.resolve(new Response(JSON.stringify([makeProjectWithoutGeneratedContent()]), { status: 200 }));
      }
      if (url === "/api/chapters/100/generate/stream") {
        const body = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode(`event: task\ndata: ${JSON.stringify(task)}\n\n`));
            controller.enqueue(encoder.encode(`event: task\ndata: ${JSON.stringify(completed)}\n\n`));
            controller.enqueue(encoder.encode("event: done\ndata: {}\n\n"));
            controller.close();
          },
        });
        return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }));
      }
      if (url === "/api/projects/42") {
        return Promise.resolve(new Response(JSON.stringify(makeProjectWithoutGeneratedContent()), { status: 200 }));
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    });

    render(<App />);
    await screen.findByRole("button", { name: /异常出现/ });

    fireEvent.click(screen.getByRole("button", { name: "生成" }));

    expect(await screen.findByRole("button", { name: /1.*加载上下文.*完成/ })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /11.*保存候选结果.*完成/ })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByLabelText("章节正文")).toHaveValue("流式正文候选第一段。");
    });
    expect(screen.queryByRole("region", { name: "生成结果" })).not.toBeInTheDocument();
  });

  it("runs specified-count auto generation and shows total progress", async () => {
    const encoder = new TextEncoder();
    const childTask = {
      id: 21,
      project_id: 42,
      chapter_id: 100,
      kind: "chapter_generation",
      status: "completed",
      current_step: "persist_candidate_result",
      error_type: null,
      error_message: null,
      chapter: makeProject().chapters[0],
      steps: [
        {
          id: 1,
          task_id: 21,
          name: "generate_prose",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { generated_content: "全自动生成的正文。" },
          error_message: null,
        },
        {
          id: 2,
          task_id: 21,
          name: "persist_candidate_result",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { persistence_result: { saved_candidate: true } },
          error_message: null,
        },
      ],
    };
    const autoTask = {
      id: 30,
      project_id: 42,
      kind: "auto_chapter_generation",
      status: "completed",
      current_step: "auto_chapter_1",
      error_type: null,
      error_message: null,
      target_count: 1,
      completed_count: 1,
      current_chapter_id: 100,
      current_chapter_task: childTask,
      completed_chapters: [{ id: 100, number: 1, title: "异常出现" }],
      steps: [],
    };

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/projects") {
        return Promise.resolve(new Response(JSON.stringify([makeProjectWithoutGeneratedContent()]), { status: 200 }));
      }
      if (url === "/api/projects/42/auto-generate/stream") {
        const body = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode(`event: auto_task\ndata: ${JSON.stringify(autoTask)}\n\n`));
            controller.enqueue(encoder.encode("event: done\ndata: {}\n\n"));
            controller.close();
          },
        });
        return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }));
      }
      if (url === "/api/projects/42") {
        return Promise.resolve(new Response(JSON.stringify(makeProject()), { status: 200 }));
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    });

    render(<App />);
    await screen.findByRole("button", { name: /异常出现/ });

    fireEvent.change(screen.getByLabelText("自动生成章数"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "开始全自动" }));

    expect(await screen.findByText("全自动：1 / 1")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByLabelText("章节正文")).toHaveValue("全自动生成的正文。");
    });
  });
  it("keeps the generated chapter selected after auto generation refreshes the project", async () => {
    const encoder = new TextEncoder();
    const secondChapter = makeProjectWithAcceptedSecondChapter().chapters[1];
    const childTask = {
      id: 22,
      project_id: 42,
      chapter_id: 101,
      kind: "chapter_generation",
      status: "completed",
      current_step: "persist_candidate_result",
      error_type: null,
      error_message: null,
      chapter: secondChapter,
      steps: [
        {
          id: 1,
          task_id: 22,
          name: "generate_prose",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { generated_content: "chapter two streamed candidate" },
          error_message: null,
        },
        {
          id: 2,
          task_id: 22,
          name: "persist_candidate_result",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { persistence_result: { saved_candidate: true } },
          error_message: null,
        },
      ],
    };
    const autoTask = {
      id: 31,
      project_id: 42,
      kind: "auto_chapter_generation",
      status: "completed",
      current_step: "auto_chapter_1",
      error_type: null,
      error_message: null,
      target_count: 1,
      completed_count: 1,
      current_chapter_id: 101,
      current_chapter_task: childTask,
      completed_chapters: [{ id: 101, number: 2, title: "Chapter Two" }],
      steps: [],
    };

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/projects") {
        return Promise.resolve(new Response(JSON.stringify([makeProjectWithoutGeneratedContent()]), { status: 200 }));
      }
      if (url === "/api/projects/42/auto-generate/stream") {
        const body = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode(`event: auto_task\ndata: ${JSON.stringify(autoTask)}\n\n`));
            controller.enqueue(encoder.encode("event: done\ndata: {}\n\n"));
            controller.close();
          },
        });
        return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }));
      }
      if (url === "/api/projects/42") {
        return Promise.resolve(new Response(JSON.stringify(makeProjectWithAcceptedSecondChapter()), { status: 200 }));
      }
      return Promise.resolve(new Response("{}", { status: 200 }));
    });

    render(<App />);
    await screen.findByRole("button", { name: /异常出现/ });

    fireEvent.change(document.querySelector('input[type="number"]') as HTMLInputElement, { target: { value: "1" } });
    fireEvent.click(document.querySelector(".top-generation-toolbar .primary-button") as HTMLButtonElement);

    expect(await screen.findByRole("heading", { name: "Chapter Two" })).toBeInTheDocument();
    await waitFor(() => {
      expect(document.querySelector(".chapter-textarea")).toHaveValue("chapter two streamed candidate");
    });
  });
});

describe("ChapterEditor", () => {
  it("locks the chapter body while generation is busy", () => {
    render(
      <ChapterEditor
        chapter={makeProject().chapters[0]}
        editorContent="生成中的正文"
        liveGeneratedContent={null}
        autoChapterCount="3"
        autoTask={null}
        idea=""
        busy={true}
        error={null}
        onIdeaChange={() => undefined}
        onAutoChapterCountChange={() => undefined}
        onCreateProject={() => undefined}
        onEditorChange={() => undefined}
        onSave={() => undefined}
        onGenerate={() => undefined}
        onAutoGenerate={() => undefined}
        onAccept={() => undefined}
        onReject={() => undefined}
      />,
    );

    expect(screen.getByLabelText("章节正文")).toBeDisabled();
  });
});
