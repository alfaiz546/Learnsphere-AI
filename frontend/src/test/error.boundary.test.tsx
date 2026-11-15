import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RouteErrorBoundary } from '../components/ui/RouteErrorBoundary';

// Mock component simulating a failed dynamic chunk import
const FailingChunkComponent: React.FC = () => {
  throw new Error('TypeError: Failed to fetch dynamically imported module: ./assets/Lesson-chunk.js');
};

// Mock component simulating a generic render error
const GenericFailingComponent: React.FC = () => {
  throw new Error('Unexpected rendering exception in child component');
};

describe('RouteErrorBoundary — Lazy Route Chunk Failure Recovery', () => {
  beforeEach(() => {
    // Suppress console.error in tests for expected thrown errors
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('1. Normal rendering: renders child content without errors', () => {
    render(
      <RouteErrorBoundary>
        <div data-testid="normal-content">Active Route Content</div>
      </RouteErrorBoundary>
    );

    expect(screen.getByTestId('normal-content')).toBeInTheDocument();
    expect(screen.getByText('Active Route Content')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reload Page/i })).toBeNull();
  });

  it('2. Lazy chunk failure: catches chunk import failure and renders clean fallback screen', () => {
    render(
      <RouteErrorBoundary>
        <FailingChunkComponent />
      </RouteErrorBoundary>
    );

    // Verifies friendly headline for dynamic import / chunk failure
    expect(screen.getByText(/Application Update Available/i)).toBeInTheDocument();
    expect(
      screen.getByText(/A new version of LearnSphere AI was deployed or a temporary network disruption occurred/i)
    ).toBeInTheDocument();

    // Verifies user-friendly Reload button is present
    expect(screen.getByRole('button', { name: /Reload Page/i })).toBeInTheDocument();

    // Verifies no blank screen was presented
    expect(screen.queryByText('Active Route Content')).toBeNull();
  });

  it('3. Reload behavior: reload is triggered ONLY when user explicitly clicks the button (no automatic loops)', () => {
    const onReloadMock = vi.fn();

    render(
      <RouteErrorBoundary onReload={onReloadMock}>
        <FailingChunkComponent />
      </RouteErrorBoundary>
    );

    // Must NOT auto-reload upon mounting
    expect(onReloadMock).not.toHaveBeenCalled();

    // User explicitly clicks "Reload Page"
    const reloadButton = screen.getByRole('button', { name: /Reload Page/i });
    fireEvent.click(reloadButton);

    // Reload function is called exactly once
    expect(onReloadMock).toHaveBeenCalledTimes(1);
  });

  it('4. Generic error: renders standard error message with reload action', () => {
    render(
      <RouteErrorBoundary>
        <GenericFailingComponent />
      </RouteErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/We encountered an unexpected error while loading this route/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reload Page/i })).toBeInTheDocument();
  });
});
