import { useCompanyStore } from '../store/companyStore';

export function getCurrencyCode(): string {
  return useCompanyStore.getState().company?.currency ?? 'ETB';
}

export function formatCurrency(amount: number, currency?: string): string {
  const code = currency ?? getCurrencyCode();
  return `${code} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const today = new Date();
export const todayStr = today.toISOString().split('T')[0];
const monthAgo = new Date(today);
monthAgo.setMonth(monthAgo.getMonth() - 1);
export const monthAgoStr = monthAgo.toISOString().split('T')[0];
