/**
 * Send a POST request and parse SSE events from the response stream.
 * @param {string} url - API endpoint URL
 * @param {{topic: string}} body - Request body
 * @param {object} handlers - Event callbacks
 * @param {(data: object) => void} handlers.onStage - Stage start/complete
 * @param {(data: object) => void} handlers.onToken - Token received
 * @param {(data: object) => void} handlers.onDone - Pipeline complete
 * @param {(error: Error) => void} handlers.onError - Error occurred
 */
export async function fetchSSE(url, body, { onStage, onToken, onDone, onError }) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (currentEvent === 'stage' && onStage) onStage(data)
          else if (currentEvent === 'token' && onToken) onToken(data)
          else if (currentEvent === 'done' && onDone) onDone(data)
        }
      }
    }
  } catch (err) {
    if (onError) onError(err)
  }
}
