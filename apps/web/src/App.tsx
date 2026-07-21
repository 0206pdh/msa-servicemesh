import { useState } from 'react'

type Status = 'idle' | 'checking' | 'up' | 'down'

const metrics = [
  ['p50', '—'],
  ['p95', '—'],
  ['p99', '—'],
  ['Throughput', '—'],
  ['Error rate', '—'],
  ['CPU / Memory', '—'],
]

export default function App() {
  const [status, setStatus] = useState<Status>('idle')
  const [message, setMessage] = useState('연결 확인 전')

  async function checkPlatform() {
    setStatus('checking')
    setMessage('확인 중')
    try {
      const response = await fetch('/api/v1/system/ping', {
        headers: { 'X-Correlation-Id': crypto.randomUUID() },
      })
      if (!response.ok) throw new Error(String(response.status))
      const result = await response.json()
      setStatus('up')
      setMessage(`${result.service} → ${result.downstream.service}`)
    } catch {
      setStatus('down')
      setMessage('연결 실패')
    }
  }

  return <main className="console">
    <header>
      <div>
        <h1>Mesh Performance Lab</h1>
        <p>Experiment console</p>
      </div>
      <div className="connection">
        <span className={`dot ${status}`} />
        <span>{message}</span>
        <button className="secondary" onClick={checkPlatform} disabled={status === 'checking'}>연결 확인</button>
      </div>
    </header>

    <section className="panel setup">
      <div className="section-title">
        <div><span>01</span><h2>실험 조건</h2></div>
        <small>한 번에 하나의 변수만 변경</small>
      </div>
      <div className="fields">
        <label>Mesh profile<select defaultValue="no-mesh"><option value="no-mesh">No Mesh</option><option>Istio Sidecar</option><option>Ambient</option><option>Ambient + Waypoint</option></select></label>
        <label>Scenario<select defaultValue="sync"><option value="sync">Sync Chain</option><option>Fan-out</option><option>Async</option><option>Payload</option></select></label>
        <label>Request rate<input value="100 req/s" readOnly /></label>
        <label>Duration<input value="10 min" readOnly /></label>
      </div>
      <div className="action-row">
        <p>실행 API는 Phase 1 workload 구현 후 연결됩니다.</p>
        <button disabled>실험 시작</button>
      </div>
    </section>

    <section className="panel results">
      <div className="section-title">
        <div><span>02</span><h2>측정 결과</h2></div>
        <small>No experiment selected</small>
      </div>
      <div className="metric-grid">
        {metrics.map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}
      </div>
      <div className="empty-state">
        <strong>아직 측정 결과가 없습니다.</strong>
        <p>부하는 k6가 생성하고, 이 화면은 실행 상태와 저장된 결과만 조회합니다.</p>
      </div>
    </section>
  </main>
}
