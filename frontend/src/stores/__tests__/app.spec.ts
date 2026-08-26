// 应用 Store 逻辑测试（mock API）
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api', () => ({
  getStatus: vi.fn(async () => ({ apps: { search: 'stopped' } })),
  startApp: vi.fn(async () => ({ app_name: 'search', status: 'running' })),
  stopApp: vi.fn(async () => ({ app_name: 'search', status: 'stopped' })),
  getOutput: vi.fn(async () => ({ app_name: 'search', output_text: 'hello' })),
}))

import { useAppStore } from '@/stores/app'

describe('app store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetchStatus 更新 apps', async () => {
    const store = useAppStore()
    await store.fetchStatus()
    expect(store.apps.search).toBe('stopped')
  })

  it('start 更新状态为 running', async () => {
    const store = useAppStore()
    await store.start('search')
    expect(store.apps.search).toBe('running')
  })

  it('stop 更新状态为 stopped', async () => {
    const store = useAppStore()
    await store.stop('search')
    expect(store.apps.search).toBe('stopped')
  })

  it('handleOutput 追加输出', () => {
    const store = useAppStore()
    store.handleOutput('search', 'part1')
    store.handleOutput('search', 'part2')
    expect(store.outputs.search).toBe('part1part2')
  })

  it('handleStatus 更新状态', () => {
    const store = useAppStore()
    store.handleStatus('media', 'running')
    expect(store.apps.media).toBe('running')
  })
})
