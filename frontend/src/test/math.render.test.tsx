import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MathMarkdown } from '../components/ui/MathMarkdown';

describe('MathMarkdown Component — KaTeX & Markdown Rendering', () => {
  it('renders normal Markdown (bold, italic, lists, inline code) correctly', () => {
    const content = `
### Concept Overview
This is **bold concept** and *italic note*.
Here is an inline code: \`x = y + 1\`.

- First principle
- Second principle
    `.trim();

    const { container } = render(<MathMarkdown content={content} />);

    // Check headings, strong, em, and code tags
    expect(screen.getByText('bold concept').tagName.toLowerCase()).toBe('strong');
    expect(screen.getByText('italic note').tagName.toLowerCase()).toBe('em');
    expect(screen.getByText('x = y + 1').tagName.toLowerCase()).toBe('code');
    const listItems = container.querySelectorAll('li');
    expect(listItems.length).toBe(2);
    expect(listItems[0].textContent).toContain('First principle');
  });

  it('renders inline math expressions with $...$ delimiters into KaTeX DOM', () => {
    const content = 'The Pythagorean theorem states that $a^2 + b^2 = c^2$ for right triangles.';

    const { container } = render(<MathMarkdown content={content} />);

    expect(screen.getByText(/The Pythagorean theorem states that/)).toBeInTheDocument();
    // KaTeX outputs elements with the .katex class
    const katexElements = container.querySelectorAll('.katex');
    expect(katexElements.length).toBeGreaterThan(0);
    // Should not render as raw dollar signs
    expect(container.textContent).not.toContain('$a^2 + b^2 = c^2$');
  });

  it('renders block math expressions with $$...$$ delimiters into display KaTeX DOM', () => {
    const content = `
Calculate the Gaussian integral:

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$
    `.trim();

    const { container } = render(<MathMarkdown content={content} />);

    // KaTeX display math containers have .katex-display class
    const displayElements = container.querySelectorAll('.katex-display');
    expect(displayElements.length).toBe(1);
    expect(container.querySelectorAll('.katex').length).toBeGreaterThan(0);
  });

  it('normalizes and renders LaTeX delimiters \\(...\\) and \\[...\\]', () => {
    const content = 'Inline fraction \\(\\frac{1}{2}\\) and block formula: \\[E = mc^2\\]';

    const { container } = render(<MathMarkdown content={content} />);

    const katexElements = container.querySelectorAll('.katex');
    expect(katexElements.length).toBeGreaterThanOrEqual(2);
    // Display block for \\[...\\]
    const displayElements = container.querySelectorAll('.katex-display');
    expect(displayElements.length).toBe(1);
  });

  it('handles invalid LaTeX gracefully without crashing or throwing', () => {
    // Malformed LaTeX: unknown macro and missing braces
    const content = 'Here is an invalid formula: $\\undefinedMacroNonExistent{abc}$ and incomplete $\\frac{1}$.';

    // Must render cleanly without throwing an exception
    expect(() => {
      render(<MathMarkdown content={content} />);
    }).not.toThrow();

    // KaTeX with throwOnError:false renders error text with errorColor or fallback span
    expect(screen.getByText(/Here is an invalid formula/)).toBeInTheDocument();
  });

  it('renders plain text without math delimiters unchanged', () => {
    const content = 'A completely standard sentence with numbers 123 and symbols like #, @, %, but no LaTeX.';

    const { container } = render(<MathMarkdown content={content} />);

    expect(screen.getByText(content)).toBeInTheDocument();
    expect(container.querySelectorAll('.katex').length).toBe(0);
  });

  it('renders inline mode without wrapping in block paragraph', () => {
    const content = '$\\alpha + \\beta$';

    const { container } = render(<MathMarkdown content={content} inline />);

    // In inline mode, root is inline or span, not a block p
    expect(container.querySelector('p')).toBeNull();
    expect(container.querySelectorAll('.katex').length).toBeGreaterThan(0);
  });
});
