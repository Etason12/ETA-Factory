import { useCompanyStore } from '../store/companyStore';

export function getCurrencyCode(): string {
  return useCompanyStore.getState().company?.currency ?? 'ETB';
}

export function formatCurrency(amount: number, currency?: string): string {
  const code = currency ?? getCurrencyCode();
  return `${code} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
