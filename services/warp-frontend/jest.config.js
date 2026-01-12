const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
    '!**/*.config.{ts,js}',
    '!**/node_modules/**',
  ],
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/tests/e2e/', // Exclude Playwright E2E tests from Jest
  ],
  // Temporarily lower coverage threshold while building out test suite
  // Current baseline: 13.65% statements, 14.42% lines, 22.64% functions, 28.88% branches
  // Target: Reach 85% coverage by end of Phase 2 (Week 5-6)
  coverageThreshold: {
    global: {
      branches: 13,
      functions: 13,
      lines: 13,
      statements: 13,
    },
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
