import '@testing-library/jest-dom';
import 'katex/dist/katex.min.css';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './mocks/server';
import { resetRefreshCount } from './mocks/handlers';

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));

afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  resetRefreshCount();
});

afterAll(() => server.close());
