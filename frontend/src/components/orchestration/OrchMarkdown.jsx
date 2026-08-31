import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function OrchMarkdown({ children }) {
  return (
    <div className="orch-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node, ...props }) => (
            <div className="orch-table-wrap">
              <table {...props} />
            </div>
          ),
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {children || ""}
      </ReactMarkdown>
    </div>
  );
}
