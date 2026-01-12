'use client';

import { useReportWebVitals } from 'next/web-vitals';
import * as Sentry from '@sentry/nextjs';

/**
 * Web Vitals Reporting Component
 *
 * Tracks Core Web Vitals and sends to Sentry for performance monitoring:
 * - LCP (Largest Contentful Paint): Measures loading performance
 * - FID (First Input Delay): Measures interactivity
 * - CLS (Cumulative Layout Shift): Measures visual stability
 * - TTFB (Time to First Byte): Measures server response time
 * - FCP (First Contentful Paint): Measures initial render
 * - INP (Interaction to Next Paint): Measures overall responsiveness
 */
export function WebVitals() {
  useReportWebVitals((metric) => {
    // Send to Sentry as measurement
    Sentry.metrics.distribution(metric.name, metric.value, {
      unit: 'millisecond',
      tags: {
        // Include rating (good, needs-improvement, poor)
        rating: metric.rating,
      },
    });

    // For debugging in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Web Vital:', {
        name: metric.name,
        value: metric.value,
        rating: metric.rating,
        delta: metric.delta,
        id: metric.id,
      });
    }

    // Optionally send to custom analytics endpoint
    // fetch('/api/analytics/web-vitals', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     name: metric.name,
    //     value: metric.value,
    //     rating: metric.rating,
    //     timestamp: new Date().toISOString(),
    //   }),
    // });
  });

  return null;
}
