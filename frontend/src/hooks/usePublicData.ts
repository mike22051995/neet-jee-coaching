/**
 * React Query hooks for public (non-authenticated) API calls.
 */
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '@/services/api'

export function useSiteSettings() {
  return useQuery({
    queryKey: ['site-settings'],
    queryFn: publicApi.getSettings,
    staleTime: 1000 * 60 * 10, // 10 minutes — settings don't change often
  })
}

export function useActiveBatch() {
  return useQuery({
    queryKey: ['active-batch'],
    queryFn: publicApi.getActiveBatch,
    staleTime: 1000 * 60 * 5,
  })
}

export function useSchedule(batchId: string | undefined, fromDate?: string, toDate?: string) {
  return useQuery({
    queryKey: ['schedule', batchId, fromDate, toDate],
    queryFn: () => publicApi.getSchedule(batchId!, fromDate, toDate),
    enabled: !!batchId,
  })
}
