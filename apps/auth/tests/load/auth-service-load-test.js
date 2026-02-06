import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users
    { duration: '5m', target: 10 },  // Stay at 10 users
    { duration: '2m', target: 50 },  // Ramp up to 50 users
    { duration: '5m', target: 50 },  // Stay at 50 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be less than 10%
    errors: ['rate<0.1'],              // Custom error rate
  },
};

// Test data
const testUsers = [
  { email: 'test1@example.com', password: 'TestPassword123!' },
  { email: 'test2@example.com', password: 'TestPassword123!' },
  { email: 'test3@example.com', password: 'TestPassword123!' },
  { email: 'test4@example.com', password: 'TestPassword123!' },
  { email: 'test5@example.com', password: 'TestPassword123!' },
];

// Helper function to get random user
function getRandomUser() {
  return testUsers[Math.floor(Math.random() * testUsers.length)];
}

// Helper function to create auth header
function createAuthHeader(token) {
  return { 'Authorization': `Bearer ${token}` };
}

// Main test function
export default function() {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  const user = getRandomUser();
  
  // Test 1: Health Check
  const healthCheck = http.get(`${baseUrl}/health`);
  check(healthCheck, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  // Test 2: Login
  const loginPayload = JSON.stringify({
    email: user.email,
    password: user.password,
  });
  
  const loginResponse = http.post(`${baseUrl}/api/v1/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const loginCheck = check(loginResponse, {
    'login status is 200 or 401': (r) => r.status === 200 || r.status === 401,
    'login response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  if (!loginCheck) {
    errorRate.add(1);
  }
  
  // If login successful, test authenticated endpoints
  if (loginResponse.status === 200) {
    const loginData = JSON.parse(loginResponse.body);
    const token = loginData.session.session_token;
    
    // Test 3: Get Current User
    const userResponse = http.get(`${baseUrl}/api/v1/auth/me`, {
      headers: createAuthHeader(token),
    });
    
    check(userResponse, {
      'get user status is 200': (r) => r.status === 200,
      'get user response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    // Test 4: Get User Profile
    const profileResponse = http.get(`${baseUrl}/api/v1/auth/users/profile`, {
      headers: createAuthHeader(token),
    });
    
    check(profileResponse, {
      'get profile status is 200': (r) => r.status === 200,
      'get profile response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    // Test 5: Get User Sessions
    const sessionsResponse = http.get(`${baseUrl}/api/v1/auth/sessions`, {
      headers: createAuthHeader(token),
    });
    
    check(sessionsResponse, {
      'get sessions status is 200': (r) => r.status === 200,
      'get sessions response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    // Test 6: Refresh Token
    const refreshResponse = http.post(`${baseUrl}/api/v1/auth/refresh`, null, {
      headers: { 'Cookie': `refresh_token=${loginData.session.refresh_token}` },
    });
    
    check(refreshResponse, {
      'refresh token status is 200': (r) => r.status === 200,
      'refresh token response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    // Test 7: Logout
    const logoutResponse = http.post(`${baseUrl}/api/v1/auth/logout`, null, {
      headers: createAuthHeader(token),
    });
    
    check(logoutResponse, {
      'logout status is 200': (r) => r.status === 200,
      'logout response time < 1000ms': (r) => r.timings.duration < 1000,
    });
  }
  
  // Test 8: Registration (occasionally)
  if (Math.random() < 0.1) { // 10% chance
    const registerPayload = JSON.stringify({
      email: `loadtest${Date.now()}@example.com`,
      password: 'TestPassword123!',
      confirm_password: 'TestPassword123!',
      first_name: 'Load',
      last_name: 'Test',
      user_type: 'patient',
    });
    
    const registerResponse = http.post(`${baseUrl}/api/v1/auth/register`, registerPayload, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    check(registerResponse, {
      'register status is 201 or 409': (r) => r.status === 201 || r.status === 409,
      'register response time < 3000ms': (r) => r.timings.duration < 3000,
    });
  }
  
  // Test 9: Rate Limiting
  if (Math.random() < 0.05) { // 5% chance
    // Make multiple rapid requests to test rate limiting
    for (let i = 0; i < 10; i++) {
      const rapidResponse = http.get(`${baseUrl}/health`);
      check(rapidResponse, {
        'rapid requests handled': (r) => r.status === 200 || r.status === 429,
      });
    }
  }
  
  // Sleep between iterations
  sleep(1);
}

// Setup function (runs once at the beginning)
export function setup() {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  
  // Check if service is available
  const healthCheck = http.get(`${baseUrl}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Service not available at ${baseUrl}`);
  }
  
  console.log(`Load test starting against ${baseUrl}`);
  return { baseUrl };
}

// Teardown function (runs once at the end)
export function teardown(data) {
  console.log('Load test completed');
}

// Handle errors
export function handleSummary(data) {
  return {
    'load-test-results.json': JSON.stringify(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
} 