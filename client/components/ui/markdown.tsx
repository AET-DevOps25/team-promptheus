import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface MarkdownProps {
  children: string;
  className?: string;
  variant?: "default" | "compact";
}

export function Markdown({ children, className, variant = "default" }: MarkdownProps) {
  const baseStyles = {
    compact:
      "prose prose-xs max-w-none prose-gray prose-headings:text-gray-900 prose-headings:font-medium prose-p:text-gray-600 prose-p:leading-normal prose-a:text-blue-600 hover:prose-a:text-blue-800 prose-strong:text-gray-800 prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-pre:bg-gray-50 prose-pre:border prose-pre:text-xs prose-blockquote:border-l-2 prose-blockquote:border-blue-400 prose-blockquote:bg-blue-50 prose-blockquote:pl-3 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5",
    default:
      "prose prose-sm max-w-none prose-gray prose-headings:text-gray-900 prose-headings:font-semibold prose-p:text-gray-700 prose-p:leading-relaxed prose-a:text-blue-600 hover:prose-a:text-blue-800 prose-strong:text-gray-900 prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-50 prose-pre:border prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50 prose-blockquote:pl-4 prose-ul:my-4 prose-ol:my-4 prose-li:my-1",
  };

  return (
    <div className={cn(baseStyles[variant], className)}>
      <ReactMarkdown
        components={{
          blockquote: ({ ...props }) => <blockquote className="my-3 italic" {...props} />,
          code: ({ inline, ...props }: any) =>
            inline ? (
              <code className="text-sm" {...props} />
            ) : (
              <code className="block text-sm" {...props} />
            ),
          // Custom rendering for specific elements
          h1: ({ ...props }) => <h1 className="text-xl font-semibold mb-3 mt-0" {...props} />,
          h2: ({ ...props }) => <h2 className="text-lg font-semibold mb-2 mt-4" {...props} />,
          h3: ({ ...props }) => <h3 className="text-base font-medium mb-2 mt-3" {...props} />,
          li: ({ ...props }) => <li className="leading-relaxed" {...props} />,
          ol: ({ ...props }) => <ol className="mb-3 last:mb-0 space-y-1" {...props} />,
          p: ({ ...props }) => <p className="mb-3 last:mb-0" {...props} />,
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border-collapse border border-gray-300" {...props} />
            </div>
          ),
          td: ({ ...props }) => <td className="border border-gray-300 px-3 py-2" {...props} />,
          th: ({ ...props }) => (
            <th
              className="border border-gray-300 bg-gray-50 px-3 py-2 text-left font-medium"
              {...props}
            />
          ),
          ul: ({ ...props }) => <ul className="mb-3 last:mb-0 space-y-1" {...props} />,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
