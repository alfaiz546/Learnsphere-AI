import React, { useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-bash';
import { Check, Copy, Code2 } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  className?: string;
}

function normalizeLanguage(lang: string): string {
  const map: Record<string, string> = {
    py: 'python',
    js: 'javascript',
    ts: 'typescript',
    'c++': 'cpp',
    cc: 'cpp',
    html: 'markup',
    xml: 'markup',
    svg: 'markup',
    sh: 'bash',
    shell: 'bash',
    zsh: 'bash',
  };
  const normalized = (lang || '').toLowerCase().trim();
  return map[normalized] || normalized;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language = '', className }) => {
  const [copied, setCopied] = useState(false);
  const trimmedCode = code.replace(/\n$/, '');

  const normLang = normalizeLanguage(language);
  const grammar = Prism.languages[normLang];

  let highlightedHtml: string;
  const displayLang = (language || normLang || 'code').toUpperCase();

  if (grammar) {
    try {
      highlightedHtml = Prism.highlight(trimmedCode, grammar, normLang);
    } catch {
      highlightedHtml = trimmedCode
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  } else {
    // Unknown language: render escaped code safely without crashing
    highlightedHtml = trimmedCode
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(trimmedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore copy error
    }
  };

  return (
    <div className={`rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 text-slate-100 my-3 shadow-md ${className || ''}`}>
      {/* Code Header bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/80 bg-slate-900/90 text-xs text-slate-400">
        <div className="flex items-center gap-2 font-mono text-[11px] font-medium tracking-wide">
          <Code2 className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-slate-300 font-semibold">{displayLang}</span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy code"
          className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors text-[11px]"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      <div className="p-4 overflow-x-auto text-xs font-mono leading-relaxed">
        <pre className="m-0 p-0 bg-transparent">
          <code
            className="code-highlight"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        </pre>
      </div>
    </div>
  );
};
