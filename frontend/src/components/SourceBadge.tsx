import type { Source } from "../api/types";
import { sourceLabels } from "../format";

interface SourceBadgeProps {
  source: Source;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  return (
    <span className={`source-badge source-badge--${source}`}>
      <span aria-hidden="true" className="source-badge__dot" />
      {sourceLabels[source]}
    </span>
  );
}
