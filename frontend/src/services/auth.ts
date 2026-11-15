import api from './api';

export const authService = {
  async register(data: { email: string; username: string; password: string; full_name?: string }) {
    const res = await api.post('/auth/register', data);
    return res.data;
  },

  async login(data: { email: string; password: string }) {
    const res = await api.post('/auth/login', data);
    return res.data;
  },

  async getProfile() {
    const res = await api.get('/student/profile');
    return res.data;
  },

  async updateProfile(data: {
    full_name?: string;
    daily_goal_minutes?: number;
    subjects_of_interest?: string[];
    current_class?: string;
    board?: string;
    current_marks?: number;
    target_exam?: string;
    career_goal?: string;
    target_year?: number;
    category?: string;
  }) {
    const res = await api.put('/student/profile', data);
    return res.data;
  },

  async logout() {
    try {
      await api.post('/auth/logout');
    } catch {
      // Best-effort: server may be unreachable
    }
    // Clean up any pre-migration localStorage remnants
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
