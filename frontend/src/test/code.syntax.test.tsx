import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MathMarkdown } from '../components/ui/MathMarkdown';
import { CodeBlock } from '../components/ui/CodeBlock';

describe('Code Syntax Highlighting & Markdown Integration', () => {
  beforeEach(() => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });
  });

  it('1. Highlights Python code with keywords and functions', () => {
    const pySnippet = `
\`\`\`python
def calculate_area(radius: float) -> float:
    # Compute circle area
    pi = 3.14159
    return pi * (radius ** 2)
\`\`\`
    `.trim();

    const { container } = render(<MathMarkdown content={pySnippet} />);

    // Verify language badge
    expect(screen.getByText('PYTHON')).toBeInTheDocument();
    // Verify tokens were generated
    const keywords = container.querySelectorAll('.token.keyword');
    expect(keywords.length).toBeGreaterThan(0);
    const comments = container.querySelectorAll('.token.comment');
    expect(comments.length).toBeGreaterThan(0);
  });

  it('2. Supports all required languages (JS, TS, Java, C, C++, HTML, CSS, JSON, SQL, Bash)', () => {
    const languages = [
      { lang: 'javascript', code: 'const sum = (a, b) => a + b;' },
      { lang: 'typescript', code: 'interface User { id: string; active: boolean; }' },
      { lang: 'java', code: 'public class Main { public static void main(String[] args) {} }' },
      { lang: 'c', code: '#include <stdio.h>\nint main() { return 0; }' },
      { lang: 'cpp', code: '#include <iostream>\nint main() { std::cout << "Hi"; }' },
      { lang: 'html', code: '<div class="card"><h1>Title</h1></div>' },
      { lang: 'css', code: '.card { display: flex; color: #fff; }' },
      { lang: 'json', code: '{\n  "status": "success",\n  "count": 42\n}' },
      { lang: 'sql', code: 'SELECT id, username FROM users WHERE is_active = 1;' },
      { lang: 'bash', code: '#!/bin/bash\necho "Running checks..."\nexit 0' },
    ];

    for (const { lang, code } of languages) {
      const markdown = `\`\`\`${lang}\n${code}\n\`\`\``;
      const { container } = render(<MathMarkdown content={markdown} />);
      // Language badge is rendered
      expect(screen.getByText(lang.toUpperCase())).toBeInTheDocument();
      // Code is wrapped with .code-highlight
      expect(container.querySelector('.code-highlight')).toBeInTheDocument();
      // Tokens are present
      expect(container.querySelectorAll('.token').length).toBeGreaterThan(0);
    }
  });

  it('3. Handles unknown languages gracefully without crashing', () => {
    const unknownSnippet = `
\`\`\`nonexistent_lang_xyz
RECORD Person
  NAME: string
  AGE: integer
END
\`\`\`
    `.trim();

    expect(() => {
      render(<MathMarkdown content={unknownSnippet} />);
    }).not.toThrow();

    // Renders the code content safely
    expect(screen.getByText(/RECORD Person/)).toBeInTheDocument();
    expect(screen.getByText('NONEXISTENT_LANG_XYZ')).toBeInTheDocument();
  });

  it('4. Handles plain code blocks with no language specified', () => {
    const plainSnippet = `
\`\`\`
plain text line 1
plain text line 2
\`\`\`
    `.trim();

    const { container } = render(<MathMarkdown content={plainSnippet} />);

    expect(screen.getByText(/plain text line 1/)).toBeInTheDocument();
    expect(container.querySelector('.code-highlight')).toBeInTheDocument();
  });

  it('5. Distinguishes inline code from fenced code blocks', () => {
    const content = 'Inline code is `let x = 10;` within regular text.';

    const { container } = render(<MathMarkdown content={content} />);

    // Inline code renders standard code tag, not full CodeBlock header with copy button
    expect(container.querySelector('code')).toHaveTextContent('let x = 10;');
    expect(screen.queryByLabelText('Copy code')).toBeNull();
  });

  it('6. Full compatibility: renders Headings, GFM Table, KaTeX Math, and Code together', () => {
    const mixedContent = `
## Quadratic Equation Solver

Calculate roots using formula: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$

\`\`\`python
import math
def solve_quadratic(a, b, c):
    disc = b**2 - 4*a*c
    return (-b + math.sqrt(disc)) / (2*a)
\`\`\`

| Coefficient | Value |
| ----------- | ----- |
| a | 1 |
| b | -5 |
| c | 6 |
    `.trim();

    const { container } = render(<MathMarkdown content={mixedContent} />);

    // 1. Heading
    expect(screen.getByRole('heading', { level: 2, name: /Quadratic Equation Solver/i })).toBeInTheDocument();
    // 2. KaTeX Math
    expect(container.querySelectorAll('.katex').length).toBeGreaterThan(0);
    // 3. Code Block
    expect(screen.getByText('PYTHON')).toBeInTheDocument();
    expect(container.querySelectorAll('.token.keyword').length).toBeGreaterThan(0);
    // 4. GFM Table
    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(screen.getByText('Coefficient')).toBeInTheDocument();
    expect(screen.getByText('Value')).toBeInTheDocument();
  });

  it('7. Copy button writes code to clipboard and indicates copied state', async () => {
    const code = 'const answer = 42;';
    render(<CodeBlock code={code} language="javascript" />);

    const copyBtn = screen.getByLabelText('Copy code');
    expect(copyBtn).toBeInTheDocument();

    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(code);
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });
});
