import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Research Agent</h1>
        <p className="text-2xl text-gray-600">Tech & Investing Intelligence</p>
        <p className="text-lg text-gray-500 max-w-2xl">
          AI-powered research agent that provides comprehensive analysis for technology
          evaluation and investment decisions.
        </p>
        <div className="pt-8">
          <Link
            href="/research"
            className="px-8 py-4 bg-blue-600 text-white text-lg font-medium rounded-lg hover:bg-blue-700 transition-colors inline-block"
          >
            Start Research
          </Link>
        </div>
      </div>
    </main>
  )
}
