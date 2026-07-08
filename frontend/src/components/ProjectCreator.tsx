import { Wand2 } from "lucide-react";
import type { FormEvent } from "react";

interface ProjectCreatorProps {
  idea: string;
  busy: boolean;
  onIdeaChange: (value: string) => void;
  onCreate: () => void;
}

export function ProjectCreator({ idea, busy, onIdeaChange, onCreate }: ProjectCreatorProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreate();
  }

  return (
    <form className="project-creator" onSubmit={handleSubmit}>
      <label htmlFor="idea">小说想法</label>
      <textarea
        id="idea"
        value={idea}
        onChange={(event) => onIdeaChange(event.target.value)}
        placeholder="一个失忆修书人在废城里修补会改变现实的书"
      />
      <button className="primary-button" type="submit" disabled={busy || !idea.trim()} title="生成项目">
        <Wand2 size={16} />
        <span>{busy ? "生成中" : "生成项目"}</span>
      </button>
    </form>
  );
}
