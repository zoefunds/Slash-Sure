import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://slashsure-backend-prod.fly.dev";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
  exportKey: (password: string) =>
    api.post("/auth/export-key", { password }),
  verifyEmail: (token: string) =>
    api.post("/auth/verify-email", { token }),
  resendVerification: (email: string) =>
    api.post("/auth/resend-verification", { email }),
  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }),
  updateProfile: (data: { full_name?: string }) =>
    api.patch("/auth/me", data),
  balance: () => api.get("/auth/me/balance"),
};

// Admin
export const adminApi = {
  listUsers: (params?: Record<string, unknown>) => api.get("/admin/users", { params }),
};

// Operators
export const operatorsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/operators/", { params }),
  get: (id: string) => api.get(`/operators/${id}/`),
  create: (data: Record<string, unknown>) => api.post("/operators/", data),
};

// Incidents
export const incidentsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/incidents/", { params }),
  get: (id: string) => api.get(`/incidents/${id}/`),
  create: (data: Record<string, unknown>) => api.post("/incidents/", data),
  addEvidence: (id: string, data: Record<string, unknown>) =>
    api.post(`/incidents/${id}/evidence`, data),
  addWebEvidence: (id: string, data: Record<string, unknown>) =>
    api.post(`/incidents/${id}/web-evidence`, data),
};

// Slashing
export const slashingApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/slashing/", { params }),
  get: (id: string) => api.get(`/slashing/${id}/`),
  create: (data: Record<string, unknown>) => api.post("/slashing/", data),
  approve: (id: string, data: { approved: boolean; reason?: string }) =>
    api.post(`/slashing/${id}/approve/`, data),
};

// Insurance
export const insuranceApi = {
  list: (params?: Record<string, unknown>) =>
    api.get("/insurance/claims", { params }),
  get: (id: string) => api.get(`/insurance/claims/${id}`),
  submit: (data: Record<string, unknown>) =>
    api.post("/insurance/claims", data),
  payout: (id: string, data: { amount: number; recipient_address: string }) =>
    api.post(`/insurance/claims/${id}/payout`, data),
};

// Monitoring
export const monitoringApi = {
  events: (params?: Record<string, unknown>) =>
    api.get("/monitoring/events", { params }),
  alerts: (params?: Record<string, unknown>) =>
    api.get("/monitoring/alerts", { params }),
  acknowledgeAlert: (id: string) =>
    api.post(`/monitoring/alerts/${id}/acknowledge/`),
  dashboardStats: () => api.get("/monitoring/dashboard/stats"),
};

// Risk
export const riskApi = {
  computeReputation: (data: Record<string, unknown>) =>
    api.post("/risk/reputation/compute", data),
  predict: (data: Record<string, unknown>) =>
    api.post("/risk/predict", data),
  getOperatorRisk: (address: string) => api.get(`/risk/operator/${address}`),
};

// GenLayer on-chain — all calls go to StudioNet which can be slow
export const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS || "0x8565ecca2743945e4020aEB8D6F4a69f088329c8";

export const genlayerApi = {
  // 12s timeout — StudioNet can be slow; callers should handle rejection gracefully
  getContractStats: () => api.get("/genlayer/stats", { timeout: 12000 }),
  getOperator: (address: string) => api.get(`/genlayer/operators/${address}`, { timeout: 12000 }),
  getVerdict: (incidentId: string) => api.get(`/genlayer/verdicts/${incidentId}`, { timeout: 12000 }),
  getCase: (caseId: string) => api.get(`/genlayer/cases/${caseId}`, { timeout: 12000 }),
  getClaim: (claimId: string) => api.get(`/genlayer/claims/${claimId}`, { timeout: 12000 }),
  getAuditEntry: (index: number) => api.get(`/genlayer/audit/${index}`, { timeout: 12000 }),
  getProposals: () => api.get("/genlayer/proposals", { timeout: 12000 }),
  vote: (proposalId: string, vote: boolean) =>
    api.post(`/genlayer/proposals/${proposalId}/vote`, { vote }, { timeout: 20000 }),
};
