import { create } from 'zustand';
import { companyApi } from '../api/endpoints';
import type { Company } from '../types';

interface CompanyState {
  company: Company | null;
  loading: boolean;
  fetchCompany: () => Promise<void>;
  updateCompany: (data: Partial<Company>) => Promise<Company>;
}

export const useCompanyStore = create<CompanyState>((set, get) => ({
  company: null,
  loading: false,
  fetchCompany: async () => {
    set({ loading: true });
    try {
      const company = await companyApi.get();
      set({ company, loading: false });
    } catch {
      set({ loading: false });
    }
  },
  updateCompany: async (data: Partial<Company>) => {
    const company = await companyApi.update(data);
    set({ company });
    return company;
  },
}));
