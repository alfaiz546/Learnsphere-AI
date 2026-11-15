import { http, HttpResponse } from 'msw';

export let refreshCallCount = 0;
export let isAuthenticatedAfterRefresh = false;

export const resetRefreshCount = () => {
  refreshCallCount = 0;
  isAuthenticatedAfterRefresh = false;
};

export const handlers = [
  // Refresh endpoint — now cookie-based (no body needed)
  http.post('*/api/auth/refresh', async ({ request, cookies }) => {
    refreshCallCount++;

    // In MSW, cookies from withCredentials are available via the cookies parameter
    // For tests, we simulate cookie-based refresh by checking the cookie
    const refreshToken = cookies?.refresh_token;

    if (refreshToken === 'expired_refresh_token') {
      return HttpResponse.json(
        { success: false, detail: 'Refresh token expired' },
        { status: 401 }
      );
    }

    if (refreshToken === 'server_error_token') {
      return HttpResponse.json(
        { success: false, detail: 'Internal server error' },
        { status: 500 }
      );
    }

    // For tests without cookies set, also check body (backward compat)
    if (!refreshToken) {
      try {
        const body = (await request.json().catch(() => ({}))) as any;
        if (body?.refresh_token === 'expired_refresh_token') {
          return HttpResponse.json(
            { success: false, detail: 'Refresh token expired' },
            { status: 401 }
          );
        }
        if (body?.refresh_token === 'server_error_token') {
          return HttpResponse.json(
            { success: false, detail: 'Internal server error' },
            { status: 500 }
          );
        }
      } catch {}
    }

    isAuthenticatedAfterRefresh = true;
    return HttpResponse.json({
      success: true,
      data: {
        user_id: 'test-user-id',
        username: 'testuser',
        role: 'student',
        csrf_token: 'new_csrf_token',
      },
    });
  }),

  http.get('*/api/protected-resource', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    // If request has Bearer header or was authenticated after refresh
    if (authHeader === 'Bearer new_valid_access_token' || isAuthenticatedAfterRefresh) {
      return HttpResponse.json({ success: true, data: { status: 'authenticated' } });
    }
    return HttpResponse.json({ detail: 'Invalid or expired token' }, { status: 401 });
  }),

  http.post('*/api/auth/login', () => {
    return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
  }),

  http.post('*/api/auth/register', () => {
    return HttpResponse.json({ detail: 'Email already registered' }, { status: 401 });
  }),
];
