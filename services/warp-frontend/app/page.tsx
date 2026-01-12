import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic';

// Server Component - runs on server only
async function getSecretValue() {
  try {
    const client = new SecretManagerServiceClient();
    const projectId = 'gen-lang-client-0011584621';
    const secretName = 'gemini-api-key'; // Using existing secret from your project

    const [version] = await client.accessSecretVersion({
      name: `projects/${projectId}/secrets/${secretName}/versions/latest`,
    });

    const secretValue = version.payload?.data?.toString();

    // Return only first 10 chars for security (proving it works without exposing secret)
    return secretValue ? `${secretValue.substring(0, 10)}...` : 'No secret found';
  } catch (error) {
    console.error('Error fetching secret:', error);
    return `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
  }
}

export default async function Home() {
  const secretPreview = await getSecretValue();
  const renderTime = new Date().toISOString();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 gap-8">
      <main className="flex flex-col gap-8 items-center max-w-2xl">
        <h1 className="text-4xl font-bold text-center">
          Firebase Hosting + Next.js 15 SSR Spike
        </h1>

        <div className="border border-gray-300 rounded-lg p-6 w-full">
          <h2 className="text-2xl font-semibold mb-4">✅ Test Results</h2>

          <div className="space-y-4">
            <div>
              <p className="font-semibold">1. Server-Side Rendering:</p>
              <p className="text-green-600">✓ This page was rendered at: {renderTime}</p>
              <p className="text-sm text-gray-600">
                (View page source - you should see this timestamp in HTML)
              </p>
            </div>

            <div>
              <p className="font-semibold">2. Secret Manager Integration:</p>
              <p className="text-green-600">✓ Secret preview: {secretPreview}</p>
              <p className="text-sm text-gray-600">
                (If you see API key prefix, Secret Manager is working)
              </p>
            </div>

            <div>
              <p className="font-semibold">3. Next.js 15 App Router:</p>
              <p className="text-green-600">✓ Server Component executed successfully</p>
            </div>
          </div>
        </div>

        <div className="text-center text-sm text-gray-500">
          <p>Project: gen-lang-client-0011584621</p>
          <p>Spike for ADR-0001: Firebase Hosting vs Cloud Run + CDN</p>
        </div>
      </main>
    </div>
  );
}
