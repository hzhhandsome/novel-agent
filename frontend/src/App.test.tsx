import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AgentWorkspace } from "./components/AgentWorkspace";
import { ChapterEditor } from "./components/ChapterEditor";
import { ModulePanel } from "./components/ModulePanel";
import { ProjectCreator } from "./components/ProjectCreator";

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

  it("blocks project creation when input review rejects the idea", async () => {
    let createCalled = false;
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url === "/api/projects/input-review") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              input_kind: "project_idea",
              decision: "block",
              reason: "输入过于模糊，无法稳定指导后续生成。",
              suggestions: ["补充主角和核心冲突。"],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url === "/api/projects" && init?.method === "POST") {
        createCalled = true;
      }
      return Promise.resolve(new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } }));
    });
    render(<App />);

    fireEvent.change(screen.getByLabelText("小说想法"), { target: { value: "爽文" } });
    fireEvent.click(await screen.findByRole("button", { name: "生成项目" }));

    expect(await screen.findByText(/输入评判：阻止/)).toBeInTheDocument();
    expect(screen.getByText(/输入过于模糊/)).toBeInTheDocument();
    expect(createCalled).toBe(false);
  });

  it("blocks adding inspiration when input review rejects it", async () => {
    let addCalled = false;
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url === "/api/projects/42/input-review") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              project_id: 42,
              input_kind: "inspiration",
              decision: "block",
              reason: "输入可能提前泄露伏笔。",
              suggestions: ["只推进一个线索。"],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url === "/api/projects/42/inspirations" && init?.method === "POST") {
        addCalled = true;
      }
      return Promise.resolve(
        new Response(JSON.stringify([makeProject()]), { status: 200, headers: { "Content-Type": "application/json" } }),
      );
    });
    render(<App />);

    await screen.findByRole("button", { name: /异常出现/ });
    fireEvent.change(screen.getByLabelText("作者灵感输入"), { target: { value: "提前泄露所有伏笔" } });
    fireEvent.click(screen.getByRole("button", { name: "加入" }));

    expect(await screen.findByText(/输入评判：阻止/)).toBeInTheDocument();
    expect(screen.getByText(/提前泄露伏笔/)).toBeInTheDocument();
    expect(addCalled).toBe(false);
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

  it("collapses and expands the editor top toolbar", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    expect(await screen.findByText("全自动")).toBeInTheDocument();
    expect(screen.getByLabelText("模型供应商")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "收起工具栏" }));

    expect(screen.queryByLabelText("模型供应商")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "开始全自动" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "展开工具栏" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "展开工具栏" }));

    expect(screen.getByLabelText("模型供应商")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始全自动" })).toBeInTheDocument();
  });

  it("updates the runtime model config from the top toolbar", async () => {
    let savedBody = "";
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url === "/api/model-config" && init?.method === "PUT") {
        savedBody = String(init.body);
        return Promise.resolve(
          new Response(
            JSON.stringify({
              provider: "deepseek",
              base_url: "https://api.deepseek.com/anthropic",
              model: "deepseek-v4-flash",
              max_tokens: 2048,
              api_key_set: true,
              routes: {
                generation: {
                  provider: "deepseek",
                  base_url: "https://api.deepseek.com/anthropic",
                  model: "writer-model-v2",
                  max_tokens: 2048,
                  api_key_set: true,
                },
                audit: {
                  provider: "deepseek",
                  base_url: "https://api.deepseek.com/anthropic",
                  model: "audit-model-v2",
                  max_tokens: 2048,
                  api_key_set: true,
                },
                summary: {
                  provider: "deepseek",
                  base_url: "https://api.deepseek.com/anthropic",
                  model: "summary-model-v2",
                  max_tokens: 2048,
                  api_key_set: true,
                },
              },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url === "/api/model-config") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              provider: "mock",
              base_url: "https://api.deepseek.com/anthropic",
              model: "mock-model",
              max_tokens: 4096,
              api_key_set: false,
              routes: {
                generation: {
                  provider: "mock",
                  base_url: "https://api.deepseek.com/anthropic",
                  model: "writer-model",
                  max_tokens: 4096,
                  api_key_set: false,
                },
              },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify([makeProject()]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    render(<App />);

    expect(await screen.findByLabelText("模型名称")).toHaveValue("mock-model");
    expect(screen.getByLabelText("生成模型")).toHaveValue("writer-model");
    fireEvent.change(screen.getByLabelText("模型供应商"), { target: { value: "deepseek" } });
    fireEvent.change(screen.getByLabelText("模型名称"), { target: { value: "deepseek-v4-flash" } });
    fireEvent.change(screen.getByLabelText("模型最大 token"), { target: { value: "2048" } });
    fireEvent.change(screen.getByLabelText("模型 API Key"), { target: { value: "secret-key" } });
    fireEvent.change(screen.getByLabelText("生成模型"), { target: { value: "writer-model-v2" } });
    fireEvent.change(screen.getByLabelText("审核模型"), { target: { value: "audit-model-v2" } });
    fireEvent.change(screen.getByLabelText("摘要模型"), { target: { value: "summary-model-v2" } });
    fireEvent.click(screen.getByRole("button", { name: "保存模型" }));

    await waitFor(() => {
      expect(savedBody).toContain("deepseek-v4-flash");
    });
    expect(savedBody).toContain("secret-key");
    expect(JSON.parse(savedBody).routes.generation.model).toBe("writer-model-v2");
    expect(JSON.parse(savedBody).routes.audit.model).toBe("audit-model-v2");
    expect(JSON.parse(savedBody).routes.summary.model).toBe("summary-model-v2");
    expect(screen.getByText("密钥已设置")).toBeInTheDocument();
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
    const resultList = document.querySelector(".result-list") as HTMLElement;
    expect(within(resultList).queryByText("主角确认修书会改写现实。")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("章节摘要"));
    expect(within(resultList).getByText("主角确认修书会改写现实。")).toBeInTheDocument();
  });

  it("resizes the backstage by dragging its top edge", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([makeProject()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<App />);

    const shell = document.querySelector(".app-shell") as HTMLElement;
    expect(await screen.findByRole("button", { name: /异常出现/ })).toBeInTheDocument();
    expect(shell.style.getPropertyValue("--backstage-height")).toBe("420px");

    fireEvent.mouseDown(screen.getByLabelText("拖拽调整后台高度"), { clientY: 700 });
    window.dispatchEvent(new MouseEvent("mousemove", { clientY: 560 }));
    window.dispatchEvent(new MouseEvent("mouseup"));

    await waitFor(() => expect(shell.style.getPropertyValue("--backstage-height")).toBe("560px"));
  });

  it("runs built-in evals from the backstage and shows the report", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/evals/builtin") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              summary: {
                case_count: 2,
                average_retention_rate: 0.75,
                passed_count: 1,
                cases: [
                  {
                    case: "summary_case_1",
                    passed: false,
                    retained: ["废城图书馆"],
                    missing: ["记忆代价"],
                  },
                ],
              },
              audit: {
                case_count: 2,
                average_recall_rate: 0.5,
                passed_count: 1,
                cases: [
                  {
                    case: "audit_case_1",
                    passed: false,
                    detected: ["人设冲突"],
                    missed: ["伏笔提前泄露"],
                  },
                ],
              },
              rag: {
                case_count: 1,
                average_recall_at_k: 1,
                average_precision_at_k: 0.333333,
                average_hit_rate_at_k: 1,
                average_mrr: 1,
                passed_count: 1,
                cases: [
                  {
                    case: "rag_case_1",
                    passed: true,
                    detected: ["红封书页未知批注"],
                    missed: [],
                  },
                ],
              },
              overall: { case_count: 5, passed_count: 3 },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify([makeProject()]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    render(<App />);

    await screen.findByRole("button", { name: /异常出现/ });
    fireEvent.click(screen.getByRole("button", { name: "运行 Eval" }));

    expect(await screen.findByText("Eval 评测")).toBeInTheDocument();
    expect(screen.getByText("通过 3 / 5")).toBeInTheDocument();
    expect(screen.getByText("摘要事实保留率 75%")).toBeInTheDocument();
    expect(screen.getByText("审核冲突检出率 50%")).toBeInTheDocument();
    expect(screen.getByText("RAG 召回率 100%")).toBeInTheDocument();
    expect(screen.getByText("RAG MRR 100%")).toBeInTheDocument();
    expect(screen.getByText(/summary_case_1/)).toBeInTheDocument();
    expect(screen.getByText(/伏笔提前泄露/)).toBeInTheDocument();
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
              story_events: [{ title: "真实事件", summary: "真实事件摘要" }],
              world_rules: [{ rule: "真实规则", limitation: "真实限制" }],
              chapter_summaries: ["真实摘要"],
              inspirations: ["真实灵感"],
              retrieval_results: {
                backend: "local_vector",
                query: "废城 图书馆 修书",
                hits: [
                  {
                    source: "story_events",
                    source_id: "7",
                    score: 0.82,
                    text: "RELEVANT_EVENT_MARKER 手背页码在废城图书馆出现。",
                    metadata: { source_chapter_id: 2 },
                  },
                ],
              },
              context_budget: {
                total_budget: 6000,
                used: 4200,
                sections: [
                  {
                    name: "chapter_summaries",
                    budget: 1600,
                    used: 1200,
                    included_count: 3,
                    omitted_count: 7,
                  },
                ],
                omitted: {
                  chapter_summaries: ["被裁剪的旧摘要"],
                  story_events: ["被裁剪的旧事件"],
                },
              },
            },
          },
        },
        {
          id: 2,
          task_id: 7,
          name: "build_chapter_target",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            chapter_target: "真实本章线路：主角确认修书代价。",
          },
        },
        {
          id: 3,
          task_id: 7,
          name: "build_prompt_package",
          status: "completed",
          error_message: null,
          input_snapshot: {
            context: "真实上下文",
            chapter_target: "真实本章线路：主角确认修书代价。",
          },
          output_snapshot: {
            prompt_package: "真实提示包：目标、限制、角色状态、伏笔。",
          },
        },
        {
          id: 4,
          task_id: 7,
          name: "generate_prose",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            generate_prose_model_usage: {
              estimated_input_tokens: 120,
              estimated_output_tokens: 300,
              duration_ms: 50,
              estimated_cost: 0.42,
            },
          },
        },
        {
          id: 5,
          task_id: 7,
          name: "audit_prose",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            audit_prose_model_usage: {
              estimated_input_tokens: 80,
              estimated_output_tokens: 20,
              duration_ms: 20,
              estimated_cost: 0.08,
            },
          },
        },
        {
          id: 6,
          task_id: 7,
          name: "summarize_chapter",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            summary: "真实章节摘要：主角确认修书代价。",
            summary_result: { summary: "真实章节摘要：主角确认修书代价。", source: "post_audit" },
          },
        },
        {
          id: 7,
          task_id: 7,
          name: "judge_foreshadowing",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            foreshadowing_decisions: {
              new: ["真实新增伏笔"],
              advanced: ["真实伏笔推进"],
              resolved: ["真实回收伏笔"],
              leaked: [],
              notes: "真实伏笔备注",
            },
          },
        },
        {
          id: 8,
          task_id: 7,
          name: "judge_character_period",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            character_period_decisions: {
              updates: ["真实角色更新"],
              new_period_cards: [{ character: "真实角色", stage: "真实新阶段", summary: "真实阶段摘要" }],
              memory_changes: ["真实记忆变化"],
              relationship_changes: ["真实关系变化"],
              stage_changed: true,
            },
          },
        },
        {
          id: 9,
          task_id: 7,
          name: "propose_future_plan_updates",
          status: "completed",
          error_message: null,
          input_snapshot: {},
          output_snapshot: {
            future_plan_updates: {
              suggestions: [{ chapter: "第 4 章", change: "真实线路调整", reason: "真实调整原因" }],
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
        evalReport={null}
        busy={false}
        collapsed={false}
        onResizeStart={() => undefined}
        onToggleCollapsed={() => undefined}
        onRetry={() => undefined}
        onRunEval={() => undefined}
      />,
    );

    const completedNode = screen.getByRole("button", { name: /1.*加载上下文.*完成/ });
    expect(completedNode).toBeInTheDocument();
    expect(completedNode).not.toHaveTextContent("完成");
    expect(screen.getByText("上下文包已加载，预算和召回信息可在下方查看。")).toBeInTheDocument();
    expect(screen.getByText(/估算 token：520/)).toBeInTheDocument();
    expect(screen.getByText(/估算成本：0.5/)).toBeInTheDocument();
    expect(screen.getByText(/上下文 4200 \/ 6000/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /2.*确认本章线路.*完成/ }));
    expect(screen.getByText("本章线路")).toBeInTheDocument();
    expect(screen.getByText("真实本章线路：主角确认修书代价。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /3.*生成本章提示包.*完成/ }));
    expect(screen.getByText("提示包摘要")).toBeInTheDocument();
    expect(screen.getByText(/真实提示包/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /4.*生成章节正文.*完成/ }));
    expect(screen.getByText("模型用量")).toBeInTheDocument();
    expect(screen.queryByText(/generate_prose_model_usage/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("原始输出"));
    expect(screen.getByText(/generate_prose_model_usage/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /6.*章节摘要.*完成/ }));
    expect(screen.getByText("真实章节摘要：主角确认修书代价。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /7.*伏笔判断.*完成/ }));
    expect(screen.getByText(/真实新增伏笔/)).toBeInTheDocument();
    expect(screen.getByText(/真实回收伏笔/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /8.*角色时期卡判断.*完成/ }));
    expect(screen.getByText(/真实新阶段/)).toBeInTheDocument();
    expect(screen.getByText(/真实记忆变化/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /9.*判断后续线路调整.*完成/ }));
    expect(screen.getByText(/真实调整原因/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /11.*保存候选结果.*完成/ }));
    expect(screen.getByText(/正式正文未写入/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "上下文" }));
    expect(screen.getByText("真实世界观")).toBeInTheDocument();
    expect(screen.getByText("真实伏笔")).toBeInTheDocument();
    expect(screen.getAllByText(/4200 \/ 6000/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/chapter_summaries/)).toBeInTheDocument();
    expect(screen.getByText(/被裁剪的旧摘要/)).toBeInTheDocument();
    expect(screen.getByText(/local_vector/)).toBeInTheDocument();
    expect(screen.getByText(/废城 图书馆 修书/)).toBeInTheDocument();
    expect(screen.getByText(/RELEVANT_EVENT_MARKER/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "结果与更新" }));
    expect(screen.queryByText(/真实审核发现/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("审核结果"));
    expect(screen.getByText(/真实审核发现/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("章节摘要"));
    expect(screen.getByText("真实候选摘要")).toBeInTheDocument();
    fireEvent.click(screen.getByText("伏笔变化"));
    expect(screen.getByText(/真实伏笔推进/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("角色卡变化"));
    expect(screen.getByText(/真实角色更新/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("后续线路变化"));
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
        modelConfig={{
          provider: "mock",
          base_url: "https://api.deepseek.com/anthropic",
          model: "mock-model",
          max_tokens: 4096,
          api_key_set: false,
        }}
        modelApiKey=""
        inputReview={null}
        idea=""
        busy={true}
        error={null}
        toolbarCollapsed={false}
        onToggleToolbarCollapsed={() => undefined}
        onIdeaChange={() => undefined}
        onAutoChapterCountChange={() => undefined}
        onModelConfigChange={() => undefined}
        onModelApiKeyChange={() => undefined}
        onSaveModelConfig={() => undefined}
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

describe("ProjectCreator", () => {
  it("locks the idea input while generation is busy", () => {
    render(<ProjectCreator idea="废城修书人" busy={true} onIdeaChange={() => undefined} onCreate={() => undefined} />);

    expect(screen.getByLabelText("小说想法")).toBeDisabled();
  });
});

describe("ModulePanel", () => {
  it("locks the inspiration input while generation is busy", () => {
    render(
      <ModulePanel
        project={makeProject()}
        inspirationText="加入一个新伏笔"
        busy={true}
        onInspirationChange={() => undefined}
        onAddInspiration={() => undefined}
      />,
    );

    expect(screen.getByLabelText("作者灵感输入")).toBeDisabled();
  });

  it("shows foreshadowing records by default with status", () => {
    render(
      <ModulePanel
        project={makeProject()}
        inspirationText=""
        busy={false}
        onInspirationChange={() => undefined}
        onAddInspiration={() => undefined}
      />,
    );

    expect(screen.getByText("伏笔记录")).toBeInTheDocument();
    const foreshadowingRow = screen.getByText("手背页码从 17 变为 16").closest("article") as HTMLElement;
    expect(foreshadowingRow).toBeInTheDocument();
    expect(within(foreshadowingRow).getByText("active")).toBeInTheDocument();
  });

  it("shows an empty state when there are no foreshadowing records", () => {
    render(
      <ModulePanel
        project={{ ...makeProject(), foreshadowing_items: [] }}
        inspirationText=""
        busy={false}
        onInspirationChange={() => undefined}
        onAddInspiration={() => undefined}
      />,
    );

    expect(screen.getByText("暂无伏笔记录")).toBeInTheDocument();
  });
});
