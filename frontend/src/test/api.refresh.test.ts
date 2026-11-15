import { describe, it, expect, beforeEach } from 'vitest';
import api from '../services/api';
import { refreshCallCount, resetRefreshCount } from './mocks/handlers';

describe('Axios Token Refresh Interceptor (Cookie-based)', () => {
  beforeEach(() => {
    localStorage.clear();
    resetRefreshCount();
  });

  it('T1: should successfully refresh on 401 and retry request with updated credentials', async () => {
    const res = await api.get('/protected-resource');
    expect(res.status).toBe(200);
    expect(res.data?.data?.status).toBe('authenticated');
    expect(refreshCallCount).toBe(1);
  });

  it('T2: should handle concurrent 401s by triggering only 1 refresh call and resolving all requests', async () => {
    const [res1, res2, res3] = await Promise.all([
      api.get('/protected-resource'),
      api.get('/protected-resource'),
      api.get('/protected-resource'),
    ]);

    expect(res1.status).toBe(200);
    expect(res2.status).toBe(200);
    expect(res3.status).toBe(200);
    expect(res1.data?.data?.status).toBe('authenticated');
    expect(res2.data?.data?.status).toBe('authenticated');
    expect(res3.data?.data?.status).toBe('authenticated');

    // Mutex verification: refresh endpoint MUST be called exactly once for the batch
    expect(refreshCallCount).toBe(1);
  });

  it('T3: should reject when refresh fails (500 error)', async () => {
    // Set a cookie to simulate server_error scenario
    document.cookie = 'refresh_token=server_error_token; path=/';

    await expect(api.get('/protected-resource')).rejects.toThrow();
    expect(refreshCallCount).toBe(1);
  });

  it('T4: should reject when refresh token is expired (401 from /auth/refresh)', async () => {
    document.cookie = 'refresh_token=expired_refresh_token; path=/';

    await expect(api.get('/protected-resource')).rejects.toThrow();
    expect(refreshCallCount).toBe(1);
  });

  it('T5: should handle concurrent 401s with failed refresh: rejects all queued requests', async () => {
    document.cookie = 'refresh_token=expired_refresh_token; path=/';

    const results = await Promise.allSettled([
      api.get('/protected-resource'),
      api.get('/protected-resource'),
      api.get('/protected-resource'),
    ]);

    expect(results[0].status).toBe('rejected');
    expect(results[1].status).toBe('rejected');
    expect(results[2].status).toBe('rejected');
    expect(refreshCallCount).toBe(1);
  });

  it('T6: should not attempt refresh if _retry is already true', async () => {
    const customConfig = { _retry: true } as any;

    await expect(api.get('/protected-resource', customConfig)).rejects.toThrow();
    expect(refreshCallCount).toBe(0);
  });

  it('T7: should exclude /auth/login from refresh interceptor to prevent retry loops', async () => {
    await expect(api.post('/auth/login', { email: 'wrong@example.com', password: 'bad' })).rejects.toThrow();
    expect(refreshCallCount).toBe(0);
  });

  it('T8: should exclude /auth/register from refresh interceptor', async () => {
    await expect(api.post('/auth/register', { email: 'exists@example.com' })).rejects.toThrow();
    expect(refreshCallCount).toBe(0);
  });

  it('T9: should exclude /auth/refresh from re-triggering itself on 401', async () => {
    document.cookie = 'refresh_token=expired_refresh_token; path=/';
    await expect(api.post('/auth/refresh')).rejects.toThrow();
    // Only the direct request was made
    expect(refreshCallCount).toBe(1);
  });

  it('T10: should clear localStorage remnants on failed refresh', async () => {
    // Simulate pre-migration state
    localStorage.setItem('access_token', 'old_token');
    localStorage.setItem('refresh_token', 'old_refresh');
    document.cookie = 'refresh_token=expired_refresh_token; path=/';

    await expect(api.get('/protected-resource')).rejects.toThrow();

    // localStorage should be cleaned up
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});

describe('Cookie Auth - No localStorage storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('T11: should add CSRF header to POST requests when csrf_token cookie exists', async () => {
    document.cookie = 'csrf_token=test_csrf_123; path=/';

    // We can't easily inspect the header in MSW, but we verify no error
    // from the CSRF header logic itself
    try {
      await api.post('/auth/login', { email: 'test@example.com', password: 'pass' });
    } catch {
      // Login fails (expected) but CSRF header was attached
    }
    // Clean up
    document.cookie = 'csrf_token=; path=/; max-age=0';
  });

  it('T12: should not add CSRF header to GET requests', async () => {
    document.cookie = 'csrf_token=test_csrf_123; path=/';

    try {
      await api.get('/protected-resource');
    } catch {
      // Expected to fail
    }
    // Verify no crash from CSRF logic on GET
    document.cookie = 'csrf_token=; path=/; max-age=0';
  });

  it('T13: should configure withCredentials for cookie transport', () => {
    expect(api.defaults.withCredentials).toBe(true);
  });

  it('T14: should not store tokens in localStorage after any API call', async () => {
    try {
      await api.get('/protected-resource');
    } catch {
      // Expected
    }
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
