import http from 'k6/http';
import { check } from 'k6';

const rps = Number(__ENV.TARGET_RPS || 1);
export const options = {
  scenarios: { benchmark: { executor: 'constant-arrival-rate', rate: rps, timeUnit: '1s', duration: __ENV.DURATION || '10s', preAllocatedVUs: Math.max(2, Math.ceil(rps)), maxVUs: Math.max(10, Math.ceil(rps * 2)) } },
  thresholds: { http_req_failed: ['rate<0.05'] },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

const config = JSON.parse(__ENV.WORKLOAD_CONFIG || '{}');
const headers = { 'Content-Type': 'application/json', 'X-Experiment-Run-Id': __ENV.RUN_ID || 'unknown' };

export default function () {
  headers['X-Correlation-Id'] = `${__ENV.RUN_ID}-${__ITER}-${__VU}`;
  let path = '/api/v1/workloads/chain';
  if (__ENV.SCENARIO === 'FAN_OUT') path = '/api/v1/workloads/fanout';
  if (__ENV.SCENARIO === 'PAYLOAD') path = '/api/v1/workloads/payload';
  if (__ENV.SCENARIO === 'ASYNC_PIPELINE') path = '/api/v1/workloads/async/tasks';
  const response = http.post(`${__ENV.TARGET_URL}${path}`, JSON.stringify(config), { headers });
  check(response, { 'status is successful': (r) => r.status >= 200 && r.status < 300 });
}
