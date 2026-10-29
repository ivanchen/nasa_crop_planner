import { useCallback, useEffect, useRef, useState } from 'react'
import { analyze, getTask } from '../api/client'
import type { Job, Location, Priorities } from '../types'

const POLL_INTERVAL_MS = 5000

export function useAnalysis() {
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestId = useRef(0)

  const jobId = job?.job_id
  const processing = job?.status === 'processing'

  const run = useCallback(async (location: Location, priorities: Priorities) => {
    const id = ++requestId.current
    setLoading(true)
    setError(null)
    setJob(null)
    try {
      const result = await analyze(location, priorities)
      if (id === requestId.current) setJob(result)
    } catch (e) {
      if (id === requestId.current) setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!jobId || !processing) return
    const id = requestId.current
    const timer = setInterval(async () => {
      try {
        const result = await getTask(jobId)
        if (id === requestId.current) {
          setJob(result)
          setError(null)
        }
      } catch (e) {
        if (id === requestId.current) setError(e instanceof Error ? e.message : 'Polling failed')
      }
    }, POLL_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [jobId, processing])

  return { job, loading, error, run }
}
