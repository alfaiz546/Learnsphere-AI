import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import clsx from 'clsx';
import { CodeBlock } from './CodeBlock';

interface MathMarkdownProps {
  content: string;
  className?: string;
  inline?: boolean;
}

interface ErrorBoundaryProps {
  fallbackText: string;
  className?: string;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class MathErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('MathMarkdown render error caught by boundary, falling back to raw text:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <span className={clsx('font-mono text-sm text-amber-700 dark:text-amber-300', this.props.className)}>
          {this.props.fallbackText}
        </span>
      );
    }
    return this.props.children;
  }
}

/**
 * Normalizes LaTeX delimiters so that both \(...\) / \[...\] and $...$ / $$...$$ are parsed by remark-math.
 */
function normalizeDelimiters(text: string): string {
  if (!text) return '';
  // Convert \[ ... \] block math to $$ ... $$
  let normalized = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, math) => `\n$$\n${math}\n$$\n`);
  // Convert \( ... \) inline math to $ ... $
  normalized = normalized.replace(/\\\(([\s\S]*?)\\\)/g, (_, math) => `$${math}$`);
  return normalized;
}

export const MathMarkdown: React.FC<MathMarkdownProps> = ({
  content,
  className,
  inline = false,
}) => {
  if (!content) return null;

  const normalizedContent = normalizeDelimiters(content);

  const katexOptions = {
    throwOnError: false,
    strict: false,
    errorColor: '#dc2626',
  };

  return (
    <MathErrorBoundary fallbackText={content} className={className}>
      <div
        className={clsx(
          'math-markdown leading-relaxed',
          inline ? 'inline' : 'space-y-2',
          className
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkMath, remarkGfm]}
          rehypePlugins={[[rehypeKatex, katexOptions]]}
          components={{
            p: ({ node, ...props }) =>
              inline ? <span {...props} /> : <p className="leading-relaxed" {...props} />,
            pre: ({ children }) => <>{children}</>,
            code: ({ node, className: codeClass, children, ...props }) => {
              const match = /language-([a-zA-Z0-9_+]+)/.exec(codeClass || '');
              const isFencedBlock = !!match || String(children).includes('\n');
              if (isFencedBlock && !inline) {
                return (
                  <CodeBlock
                    code={String(children)}
                    language={match ? match[1] : ''}
                  />
                );
              }
              return (
                <code
                  className={clsx(
                    'px-1.5 py-0.5 rounded text-xs font-mono bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200',
                    codeClass
                  )}
                  {...props}
                >
                  {children}
                </code>
              );
            },
            ul: ({ children }) => <ul className="list-disc ml-5 space-y-1 my-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal ml-5 space-y-1 my-2">{children}</ol>,
            li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            h1: ({ children }) => <h1 className="text-xl font-bold my-2 text-slate-900 dark:text-white">{children}</h1>,
            h2: ({ children }) => <h2 className="text-lg font-bold my-2 text-slate-900 dark:text-white">{children}</h2>,
            h3: ({ children }) => <h3 className="text-base font-semibold my-1.5 text-slate-900 dark:text-white">{children}</h3>,
            table: ({ children }) => (
              <div className="overflow-x-auto my-3 rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left divide-y divide-slate-200 dark:divide-slate-800">
                  {children}
                </table>
              </div>
            ),
            th: ({ children }) => (
              <th className="px-3 py-2 bg-slate-100 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-200">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="px-3 py-2 border-t border-slate-100 dark:border-slate-800/40 text-slate-600 dark:text-slate-300">
                {children}
              </td>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 underline hover:opacity-80 transition-opacity"
              >
                {children}
              </a>
            ),
          }}
        >
          {normalizedContent}
        </ReactMarkdown>
      </div>
    </MathErrorBoundary>
  );
};
