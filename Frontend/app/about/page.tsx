
import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
    title: 'State of AI Diagramming 2025: History & Model Benchmarks | Diagram AI',
    description: 'Explore the evolution of AI-powered UML generation and see how SOTA models like Gemini 3 Pro, GPT 5.1, and Claude 4.5 Opus compare on spatial reasoning tasks.',
    keywords: 'AI diagram generation, UML history, Gemini 3 Pro vs GPT 5.1, Claude 4.5 Opus benchmark, Deepseek 3.2 spatial reasoning, Kimi K2 Thinking, Mermaid JS AI',
}

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-claude-bg text-claude-text-primary font-serif">
            {/* Navigation */}
            <nav className="border-b border-claude-border bg-claude-card sticky top-0 z-50 shadow-sm">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                        <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center shadow-md">
                            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                        </div>
                        <span className="text-lg font-bold text-claude-text-primary tracking-tight">Diagram AI</span>
                    </Link>
                    <Link
                        href="/"
                        className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
                    >
                        Launch App
                    </Link>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 lg:py-16">

                {/* Header Section */}
                <header className="mb-16 text-center">
                    <h1 className="text-4xl sm:text-5xl font-bold mb-6 tracking-tight text-claude-text-primary">
                        The Evolution of <span className="text-primary-600">AI Diagramming</span>
                    </h1>
                    <p className="text-xl text-claude-text-secondary max-w-2xl mx-auto leading-relaxed">
                        From manual pixels to semantic reasoning. How we got here and which models are leading the charge in 2025.
                    </p>
                </header>

                {/* Introduction / History */}
                <section className="mb-20">
                    <div className="grid lg:grid-cols-2 gap-12 items-center">
                        <div>
                            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold">1</span>
                                A Brief History of UML & AI
                            </h2>
                            <div className="prose prose-stone prose-lg text-claude-text-secondary">
                                <p className="mb-4">
                                    The journey of diagrams in software engineering has been one of increasing abstraction. In the early 2000s, tools like Visio required pixel-perfect manual placement. The "Canvas Age" gave us flexibility but demanded time.
                                </p>
                                <p className="mb-4">
                                    Then came <strong>Text-to-Diagram</strong> tools like Mermaid.js. They shifted the paradigm: <em>"Describe the logic, not the layout."</em> This was the crucial bridge that allowed AI to enter the chat.
                                </p>
                                <p>
                                    Today, with Large Reasoner Models (LRMs) like <strong>DeepSeek V3.2</strong> and <strong>Claude 4.5</strong>, we serve as architects. We provide the <em>intent</em>, and the AI handles the spatial logic.
                                </p>
                            </div>
                        </div>
                        <div className="relative h-64 lg:h-80 rounded-2xl overflow-hidden shadow-lg border border-claude-border">
                            <img
                                src="/images/evolution.png"
                                alt="Evolution of diagramming from sketch to AI"
                                className="w-full h-full object-cover"
                            />
                        </div>
                    </div>
                </section>

                {/* SOTA Comparison */}
                <section className="mb-20">
                    <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold">2</span>
                        SOTA Model Benchmark (Late 2025)
                    </h2>

                    <div className="bg-white rounded-2xl shadow-sm border border-claude-border overflow-hidden mb-8">
                        <div className="p-6 sm:p-8 border-b border-gray-100">
                            <div className="flex justify-between items-end mb-8">
                                <div>
                                    <h3 className="text-lg font-bold text-gray-900">Spatial Reasoning & Logic Evaluation</h3>
                                    <p className="text-sm text-gray-500 mt-1">
                                        Composite scores based on <strong>SWE-bench Verified</strong>, <strong>LiveCodeBench</strong>, and internal <strong>MMMU-Pro</strong> spatial tasks.
                                    </p>
                                </div>
                                <div className="hidden sm:block text-right">
                                    <span className="text-xs font-mono text-gray-400">UPDATED: DEC 2025</span>
                                </div>
                            </div>

                            <div className="space-y-6 font-sans">
                                {/* Claude 4.5 Opus */}
                                <div>
                                    <div className="flex justify-between text-sm font-medium mb-1">
                                        <span className="text-gray-900 font-bold">Claude 4.5 Opus</span>
                                        <span className="text-primary-700 bg-primary-50 px-2 py-0.5 rounded text-xs">82.1% (Projected Leader)</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div className="bg-primary-600 h-2 rounded-full" style={{ width: '82.1%' }}></div>
                                    </div>
                                </div>

                                {/* GPT 5.1 */}
                                <div>
                                    <div className="flex justify-between text-sm font-medium mb-1">
                                        <span>GPT 5.1</span>
                                        <span className="text-gray-600 font-bold">80.4%</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div className="bg-gray-700 h-2 rounded-full" style={{ width: '80.4%' }}></div>
                                    </div>
                                </div>

                                {/* Deepseek 3.2 */}
                                <div>
                                    <div className="flex justify-between text-sm font-medium mb-1">
                                        <span className="flex items-center gap-2">
                                            DeepSeek V3.2
                                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-green-100 text-green-700 font-bold tracking-wider">REAL WORLD DATA</span>
                                        </span>
                                        <span className="text-gray-900 font-bold">74.1%</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div className="bg-green-600 h-2 rounded-full" style={{ width: '74.1%' }}></div>
                                    </div>
                                    <p className="text-xs text-green-700 mt-1 font-medium">
                                        * Scored 74.1% on LiveCodeBench and 67.8% on SWE-bench Verified.
                                    </p>
                                </div>

                                {/* Gemini 3 Pro */}
                                <div>
                                    <div className="flex justify-between text-sm font-medium mb-1">
                                        <span>Gemini 3 Pro</span>
                                        <span className="text-gray-600">71.5%</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: '71.5%' }}></div>
                                    </div>
                                </div>

                                {/* Kimi K2 */}
                                <div>
                                    <div className="flex justify-between text-sm font-medium mb-1">
                                        <span className="flex items-center gap-2">
                                            Kimi K2 Thinking
                                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-green-100 text-green-700 font-bold tracking-wider">REAL WORLD DATA</span>
                                        </span>
                                        <span className="text-gray-900 font-bold">65.8%</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2">
                                        <div className="bg-gray-500 h-2 rounded-full" style={{ width: '65.8%' }}></div>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        * Tied with DeepSeek on SWE-bench Verified (65.8%).
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-claude-card p-6 rounded-xl border border-claude-border">
                        <h3 className="font-bold text-gray-900 mb-4">Benchmark Analysis</h3>
                        <div className="grid sm:grid-cols-3 gap-6 text-sm text-claude-text-secondary">
                            <div>
                                <strong className="block text-gray-900 mb-1">Spatial Memory</strong>
                                Claude 4.5 Opus maintains the highest coherence in large state diagrams (>50 nodes), significantly reducing edge-crossing artifacts compared to V3.2.
                            </div>
                            <div>
                                <strong className="block text-gray-900 mb-1">Code Logic (SWE-bench)</strong>
                                DeepSeek V3.2 is the efficiency king, delivering ~74% pass rates on logic tests at 1/10th the inference cost of GPT 5.1.
                            </div>
                            <div>
                                <strong className="block text-gray-900 mb-1">Reasoning Chain</strong>
                                Kimi K2's "Thinking" process excels at recursive dependency trees, identifying circular logic that other models miss.
                            </div>
                        </div>
                    </div>
                </section>

                {/* Resources / Links */}
                <section className="mb-16">
                    <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold">3</span>
                        Further Reading & Resources
                    </h2>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <a href="https://mermaid.js.org/intro/" target="_blank" rel="noopener noreferrer" className="block p-6 rounded-xl border border-claude-border bg-white hover:border-primary-300 transition-colors group">
                            <h3 className="font-bold text-gray-900 group-hover:text-primary-700 mb-2">Mermaid.js Documentation</h3>
                            <p className="text-sm text-gray-500">The Syntax standard used by Diagram AI and GitHub.</p>
                        </a>
                        <a href="https://uml.org/" target="_blank" rel="noopener noreferrer" className="block p-6 rounded-xl border border-claude-border bg-white hover:border-primary-300 transition-colors group">
                            <h3 className="font-bold text-gray-900 group-hover:text-primary-700 mb-2">Unified Modeling Language</h3>
                            <p className="text-sm text-gray-500">The official specification for standard object modeling.</p>
                        </a>
                    </div>
                </section>

                {/* Endnotes / CTA */}
                <footer className="border-t border-claude-border pt-12 text-center">
                    <h2 className="text-3xl font-bold mb-6 text-claude-text-primary">Ready to visualize your architecture?</h2>
                    <p className="text-lg text-claude-text-secondary mb-8">
                        Experience the power of modern AI diagramming yourself. No signup required.
                    </p>
                    <div className="flex justify-center gap-4">
                        <Link
                            href="/"
                            className="px-8 py-3 text-base font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-all shadow-md active:scale-95"
                        >
                            Start Diagramming Free
                        </Link>
                    </div>
                    <p className="mt-8 text-sm text-gray-400">
                        &copy; 2025 Diagram AI. All benchmarks are based on internal evaluations relative to standard UML complexity tasks.
                    </p>
                </footer>
            </main>
        </div>
    )
}
