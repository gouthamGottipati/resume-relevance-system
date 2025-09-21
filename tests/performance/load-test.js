// K6 Load Testing Script for Resume AI System

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const evaluationTime = new Trend('evaluation_duration');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.02'],    // Error rate under 2%
    errors: ['rate<0.05'],             // Custom error rate under 5%
  },
};

// Test data
const testUsers = [
  { username: 'testuser1', password: 'TestPass123' },
  { username: 'testuser2', password: 'TestPass123' },
  { username: 'testuser3', password: 'TestPass123' },
];

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Login and get auth token
function login(username, password) {
  const loginPayload = JSON.stringify({
    email_or_username: username,
    password: password,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, params);
  
  const success = check(response, {
    'login successful': (r) => r.status === 200,
    'has access token': (r) => r.json('access_token') !== undefined,
  });

  if (success) {
    return response.json('access_token');
  }
  
  return null;
}

// Main test function
export default function () {
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  const token = login(user.username, user.password);
  
  if (!token) {
    errorRate.add(1);
    return;
  }

  const authHeaders = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };

  // Test 1: List resumes
  const resumesResponse = http.get(`${BASE_URL}/api/v1/resumes/`, authHeaders);
  check(resumesResponse, {
    'list resumes status is 200': (r) => r.status === 200,
    'resumes response has data': (r) => r.json('resumes') !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: List job descriptions
  const jobsResponse = http.get(`${BASE_URL}/api/v1/jobs/`, authHeaders);
  check(jobsResponse, {
    'list jobs status is 200': (r) => r.status === 200,
    'jobs response has data': (r) => r.json('jobs') !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: Get analytics dashboard
  const analyticsResponse = http.get(`${BASE_URL}/api/v1/analytics/dashboard`, authHeaders);
  check(analyticsResponse, {
    'analytics status is 200': (r) => r.status === 200,
    'analytics has metrics': (r) => r.json('total_resumes') !== undefined,
  }) || errorRate.add(1);

  sleep(1);

  // Test 4: Simulate evaluation (if test data exists)
  const resumes = resumesResponse.json('resumes') || [];
  const jobs = jobsResponse.json('jobs') || [];

  if (resumes.length > 0 && jobs.length > 0) {
    const evaluationPayload = JSON.stringify({
      resume_id: resumes[0].id,
      job_id: jobs[0].id,
    });

    const startTime = Date.now();
    const evaluationResponse = http.post(
      `${BASE_URL}/api/v1/matching/evaluate`,
      evaluationPayload,
      authHeaders
    );

    const evaluationDuration = Date.now() - startTime;
    evaluationTime.add(evaluationDuration);

    check(evaluationResponse, {
      'evaluation status is 200': (r) => r.status === 200,
      'evaluation has score': (r) => r.json('overall_score') !== undefined,
      'evaluation completed in reasonable time': (r) => evaluationDuration < 30000, // 30 seconds
    }) || errorRate.add(1);
  }

  sleep(2);
}

// Setup function (runs once per VU)
export function setup() {
  console.log('Starting load test...');
  
  // Health check
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'system is healthy': (r) => r.status === 200,
  });

  return { timestamp: Date.now() };
}

// Teardown function (runs once after all VUs finish)
export function teardown(data) {
  console.log(`Load test completed. Started at: ${new Date(data.timestamp)}`);
}