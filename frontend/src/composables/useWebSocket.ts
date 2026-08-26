// composables/useWebSocket.ts
// 原生 WebSocket 封装：自动重连（指数退避）、心跳响应、按 type 分发消息
import { ref } from 'vue'

interface WsMessage {
  type: string
  data: Record<string, unknown>
  ts?: number
}

type MessageHandler = (msg: WsMessage) => void

const MAX_RETRY = 10
const MAX_DELAY = 30000

export function useWebSocket(url: string) {
  const connected = ref(false)
  let ws: WebSocket | null = null
  let retryCount = 0
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let handlers: MessageHandler[] = []

  // 注册消息处理函数（由调用方注入 Store 分发逻辑）
  function onMessage(handler: MessageHandler) {
    handlers.push(handler)
  }

  function dispatch(msg: WsMessage) {
    handlers.forEach((h) => h(msg))
  }

  function connect() {
    ws = new WebSocket(url)

    ws.onopen = () => {
      retryCount = 0
      connected.value = true
    }

    ws.onmessage = (e) => {
      let msg: WsMessage
      try {
        msg = JSON.parse(e.data)
      } catch {
        return
      }
      if (msg.type === 'heartbeat') {
        ws?.send(JSON.stringify({ type: 'heartbeat_ack' }))
        return
      }
      dispatch(msg)
    }

    ws.onclose = () => {
      connected.value = false
      if (retryCount < MAX_RETRY) {
        // 指数退避：1s, 2s, 4s, 8s, ... 上限 30s
        const delay = Math.min(1000 * Math.pow(2, retryCount), MAX_DELAY)
        retryCount++
        retryTimer = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      // onclose 会随后触发，此处仅记录
    }
  }

  function disconnect() {
    if (retryTimer) clearTimeout(retryTimer)
    retryCount = MAX_RETRY // 阻止自动重连
    ws?.close()
    ws = null
    handlers = []
  }

  function send(msg: Record<string, unknown>) {
    ws?.send(JSON.stringify(msg))
  }

  return { connected, connect, disconnect, send, onMessage }
}
