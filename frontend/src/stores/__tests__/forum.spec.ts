// 论坛 Store 逻辑测试（mock API）
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api', () => ({
  forumStart: vi.fn(async () => ({ task_status: 'running' })),
  forumStop: vi.fn(async () => ({ task_status: 'stopped' })),
  forumLog: vi.fn(async () => ({ lines: ['line1', 'line2'] })),
  forumHistory: vi.fn(async () => ({ entries: [] })),
}))

import { useForumStore } from '@/stores/forum'
import { forumStart, forumStop, forumLog } from '@/api'

describe('forum store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('start 更新 taskStatus', async () => {
    const store = useForumStore()
    await store.start()
    expect(store.taskStatus).toBe('running')
    expect(forumStart).toHaveBeenCalled()
  })

  it('stop 更新 taskStatus', async () => {
    const store = useForumStore()
    await store.stop()
    expect(store.taskStatus).toBe('stopped')
    expect(forumStop).toHaveBeenCalled()
  })

  it('fetchLog 更新 logLines', async () => {
    const store = useForumStore()
    await store.fetchLog()
    expect(store.logLines).toEqual(['line1', 'line2'])
    expect(forumLog).toHaveBeenCalled()
  })

  it('handleLog 追加日志并更新状态', () => {
    const store = useForumStore()
    store.handleLog('新日志', 'running')
    expect(store.logLines).toContain('新日志')
    expect(store.taskStatus).toBe('running')
  })
})
