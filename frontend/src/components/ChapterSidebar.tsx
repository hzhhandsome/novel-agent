import { FilePlus2, RotateCcw } from "lucide-react";
import type { Chapter } from "../types";

interface ChapterSidebarProps {
  chapters: Chapter[];
  selectedChapterId: number | null;
  onSelect: (chapter: Chapter) => void;
  onGenerate: () => void;
}

const statusLabel: Record<string, string> = {
  not_generated: "未生成",
  generating: "生成中",
  generated: "已生成",
  accepted: "已采纳",
};

export function ChapterSidebar({ chapters, selectedChapterId, onSelect, onGenerate }: ChapterSidebarProps) {
  return (
    <aside className="sidebar" aria-label="章节">
      <div className="panel-heading">
        <h2>章节</h2>
        <button className="icon-button" type="button" title="新建章节" disabled>
          <FilePlus2 size={17} />
        </button>
      </div>
      <div className="chapter-list">
        {chapters.map((chapter) => (
          <button
            key={chapter.id}
            className={chapter.id === selectedChapterId ? "chapter-item active" : "chapter-item"}
            type="button"
            onClick={() => onSelect(chapter)}
          >
            <span>{chapter.number}. {chapter.title}</span>
            <small>{statusLabel[chapter.status] ?? chapter.status}</small>
          </button>
        ))}
      </div>
      <button className="secondary-button" type="button" onClick={onGenerate} disabled={!selectedChapterId}>
        <RotateCcw size={16} />
        <span>重生成</span>
      </button>
    </aside>
  );
}
