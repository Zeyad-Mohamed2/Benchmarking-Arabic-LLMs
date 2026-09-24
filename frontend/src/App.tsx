import { useState, useEffect } from 'react';
import { Settings, Play, Database, Key, LayoutTemplate, CheckCircle2, XCircle, Loader2, Plus, Minus, BrainCircuit, Download, BarChart2 } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

const OPENROUTER_MODELS: Record<string, string> = {
   "Google Gemma 3 27B IT": "google/gemma-3-27b-it:free",
   "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b:free",
   "Qwen 3 4B": "qwen/qwen3-4b:free",
   "Cohere Command R7B": "cohere/command-r7b-12-2024",
   "Meta Llama 3.3 70B Instruct": "meta-llama/llama-3.3-70b-instruct:free",
   "Other (custom)": "Other (custom)"
};

const GROQ_MODELS: Record<string, string> = {
   "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b",
   "Qwen 3 32B": "qwen/qwen3-32b",
   "Llama 4 Maverick 17B 128E": "meta-llama/llama-4-maverick-17b-128e-instruct",
   "Kimi K2 0905": "moonshotai/kimi-k2-instruct-0905",
   "Other (custom)": "Other (custom)"
};

export default function App() {
   const [task, setTask] = useState('question_answering');
   const [provider, setProvider] = useState('openrouter');
   const [apiKey, setApiKey] = useState('');
   const [numSamples, setNumSamples] = useState(1);
   const [customPrompt, setCustomPrompt] = useState<string | null>(null);

   // Model Selectors
   const [models, setModels] = useState<{ display: string, custom: string }[]>([{ display: Object.keys(OPENROUTER_MODELS)[0], custom: '' }]);

   // Semantic Matching
   const [useSemanticMatching, setUseSemanticMatching] = useState(false);
   const [geminiApiKey, setGeminiApiKey] = useState('');
   const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash-lite');

   // Checkpoint Mode
   const [enableCheckpointMode, setEnableCheckpointMode] = useState(false);
   const [checkpointInterval, setCheckpointInterval] = useState(50);

   // Dataset
   const [datasetFile, setDatasetFile] = useState<File | null>(null);

   // Execution State
   const [runId, setRunId] = useState<string | null>(null);
   const [isRunning, setIsRunning] = useState(false);
   const [progress, setProgress] = useState<{ current: number, total: number, status: string } | null>(null);
   const [results, setResults] = useState<any>(null);
   const [errorMsg, setErrorMsg] = useState<string | null>(null);
   const [activeTab, setActiveTab] = useState('summary');

   // Leaderboard State
   const [mainView, setMainView] = useState('benchmark'); // 'benchmark' | 'leaderboard'
   const [leaderboardData, setLeaderboardData] = useState<Record<string, any[]> | null>(null);
   const [leaderboardTask, setLeaderboardTask] = useState('question_answering');
   const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(false);
   const [leaderboardError, setLeaderboardError] = useState<string | null>(null);
   const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc'|'desc'} | null>(null);

   // Test Connection
   const [testStatus, setTestStatus] = useState<{ success: boolean, messages: Record<string, string> } | null>(null);
   const [isTesting, setIsTesting] = useState(false);

   // Update models dropdown automatically when changing providers
   useEffect(() => {
      const opts = provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS;
      const defaultKey = Object.keys(opts)[0];
      setModels(prev => prev.map(m => {
         if (opts[m.display]) return m; // keep if it exists in new provider
         return { display: defaultKey, custom: '' }; // reset if it doesn't //
      }));
   }, [provider]);

   // Derived API Model List Computation
   const getCompiledModelsList = () => {
      const opts = provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS;
      return models.map(m => m.display === "Other (custom)" && m.custom ? m.custom : opts[m.display]).filter(Boolean);
   };

   const handleTestConnection = async () => {
      setIsTesting(true);
      setTestStatus(null);
      try {
         const activeModels = getCompiledModelsList();
         if (activeModels.length === 0) throw new Error("Please select at least one active model");

         const res = await fetch(`${API_BASE}/test-connection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, api_key: apiKey, models: activeModels })
         });
         const data = await res.json();
         if (!res.ok) throw new Error(data.detail || 'Connection test failed');
         setTestStatus(data);
      } catch (err: any) {
         setTestStatus({ success: false, messages: { 'Error': err.message } });
      }
      setIsTesting(false);
   };

   const handleRunBenchmark = async () => {
      if (!apiKey) return alert("Provider API Key is required");
      if (useSemanticMatching && !geminiApiKey) return alert("Gemini API Key required for semantic matching");

      setIsRunning(true);
      setErrorMsg(null);
      setProgress(null);
      setResults(null);

      try {
         const activeModels = getCompiledModelsList();
         const formData = new FormData();
         formData.append('task', task);
         formData.append('provider', provider);
         formData.append('api_key', apiKey);
         formData.append('models', activeModels.join(','));
         formData.append('number_of_samples', numSamples.toString());
         if (customPrompt) formData.append('custom_prompt', customPrompt);
         formData.append('use_semantic_matching', useSemanticMatching.toString());
         if (useSemanticMatching) {
            formData.append('gemini_api_key', geminiApiKey);
            formData.append('gemini_model_name', geminiModel);
         }
         formData.append('enable_checkpoint_mode', enableCheckpointMode.toString());
         formData.append('checkpoint_interval', checkpointInterval.toString());
         if (datasetFile) {
            formData.append('dataset', datasetFile);
         }

         const res = await fetch(`${API_BASE}/run-benchmark`, {
            method: 'POST',
            body: formData
         });

         const data = await res.json();
         if (!res.ok) throw new Error(data.detail || 'Failed to start benchmark');

         setRunId(data.run_id);
      } catch (err: any) {
         setErrorMsg(err.message);
         setIsRunning(false);
      }
   };

   useEffect(() => {
      if (!runId) return;

      const eventSource = new EventSource(`${API_BASE}/progress/${runId}`);

      eventSource.addEventListener('progress', (e) => {
         const data = JSON.parse(e.data);
         setProgress(data);
      });

      eventSource.addEventListener('done', (e) => {
         const data = JSON.parse(e.data);
         setResults(data);
         setIsRunning(false);
         eventSource.close();
      });

      eventSource.addEventListener('error', (e: any) => {
         setErrorMsg(e.data || "Lost connection to server");
         setIsRunning(false);
         eventSource.close();
      });

      return () => {
         eventSource.close();
      };
   }, [runId]);

   // Fetch Leaderboard Data
   useEffect(() => {
      if (mainView === 'leaderboard' && !leaderboardData) {
         setIsLoadingLeaderboard(true);
         setLeaderboardError(null);
         fetch(`${API_BASE}/leaderboard`)
            .then(res => res.json())
            .then(data => {
               if (data.success) {
                  setLeaderboardData(data.data);
               } else {
                  setLeaderboardError(data.error || 'Failed to load leaderboard data');
               }
            })
            .catch(err => setLeaderboardError(err.message))
            .finally(() => setIsLoadingLeaderboard(false));
      }
   }, [mainView]);

   return (
      <div className="flex h-screen bg-[#0b0f19] text-gray-200 overflow-hidden font-sans">
         {/* Sidebar Configuration */}
         {mainView === 'benchmark' && (
            <aside className="w-80 bg-[#111827] border-r border-gray-800 p-6 flex flex-col shrink-0 overflow-y-auto relative z-10 custom-scrollbar scrollbar-thin">
               <h2 className="text-xl font-bold mb-6 text-white flex items-center tracking-tight">
                  <Settings className="mr-2 h-5 w-5 text-[#32C4B7]" /> Configuration
               </h2>

               <div className="space-y-6">
                  {/* Task */}
                  <div>
                     <label className="block text-sm font-medium mb-2 text-gray-400">Task Selection</label>
                     <select
                        className="w-full bg-[#1f2937] border border-gray-700 rounded-md p-2 text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                        value={task} onChange={(e) => setTask(e.target.value)}
                     >
                        <option value="question_answering">Question Answering</option>
                        <option value="summarization">Text Summarization</option>
                        <option value="sarcasm">Sarcasm Detection</option>
                     </select>
                  </div>

                  {/* Provider */}
                  <div>
                     <label className="block text-sm font-medium mb-2 text-gray-400">Model Provider</label>
                     <div className="flex bg-[#1f2937] rounded-md p-1 border border-gray-700">
                        <button
                           className={`flex-1 py-1.5 text-sm rounded transition-colors ${provider === 'openrouter' ? 'bg-[#374151] text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
                           onClick={() => setProvider('openrouter')}
                        >OpenRouter</button>
                        <button
                           className={`flex-1 py-1.5 text-sm rounded transition-colors ${provider === 'groq' ? 'bg-[#374151] text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
                           onClick={() => setProvider('groq')}
                        >Groq</button>
                     </div>
                  </div>

                  {/* Models */}
                  <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg">
                     <div className="flex justify-between items-center mb-3">
                        <label className="text-sm font-medium text-gray-300 flex items-center">
                           <Database className="mr-1.5 h-4 w-4 text-[#32C4B7]" /> Select Models
                        </label>
                     </div>

                     {models.map((m, idx) => (
                        <div key={idx} className="mb-3 relative group">
                           <label className="block text-xs text-gray-500 mb-1">Model {idx + 1}</label>
                           <div className="flex gap-2">
                              <div className="flex-1 space-y-2">
                                 <select
                                    className="w-full bg-[#1f2937] border border-gray-700 rounded p-2 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7]"
                                    value={m.display}
                                    onChange={(e) => {
                                       const newMw = [...models];
                                       newMw[idx].display = e.target.value;
                                       setModels(newMw);
                                    }}
                                 >
                                    {Object.keys(provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS).map(opt => (
                                       <option key={opt} value={opt}>{opt}</option>
                                    ))}
                                 </select>

                                 {m.display === 'Other (custom)' && (
                                    <input
                                       type="text" placeholder="e.g. meta-llama/llama-3..."
                                       className="w-full bg-[#111827] border border-gray-700 rounded p-2 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7]"
                                       value={m.custom} onChange={(e) => { const n = [...models]; n[idx].custom = e.target.value; setModels(n); }}
                                    />
                                 )}
                              </div>
                              {models.length > 1 && (
                                 <button onClick={() => setModels(models.filter((_, i) => i !== idx))} className="mt-1 h-[34px] px-2 text-gray-500 hover:text-red-400 bg-gray-800/50 hover:bg-gray-800 rounded border border-transparent">
                                    <Minus className="h-4 w-4" />
                                 </button>
                              )}
                           </div>
                        </div>
                     ))}
                     {models.length < 3 && (
                        <button onClick={() => setModels([...models, { display: Object.keys(provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS)[0], custom: '' }])} className="text-xs flex items-center text-[#32C4B7] hover:text-[#2aa69b] font-medium transition-colors">
                           <Plus className="h-3 w-3 mr-1" /> Add Model
                        </button>
                     )}
                  </div>

                  {/* Connect Keys */}
                  <div>
                     <label className="block text-sm font-medium mb-2 text-gray-400 flex items-center">
                        <Key className="mr-1.5 h-4 w-4" /> API Key ({provider === 'groq' ? 'Groq' : 'OpenRouter'})
                     </label>
                     <input
                        type="password" placeholder="Enter API key..."
                        className="w-full bg-[#1f2937] border border-gray-700 rounded-md p-2.5 text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7] mb-2 text-sm"
                        value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                     />
                     <button
                        onClick={handleTestConnection} disabled={isTesting}
                        className="w-full py-2 bg-[#374151] hover:bg-[#4b5563] text-gray-200 rounded-md xl text-sm flex justify-center items-center font-medium transition"
                     >
                        {isTesting ? <Loader2 className="animate-spin h-4 w-4" /> : "🔌 Test Connection"}
                     </button>
                     {testStatus && (
                        <div className={`mt-3 p-3 rounded text-xs border ${testStatus.success ? 'bg-green-900/10 text-green-400 border-green-900/50' : 'bg-red-900/10 text-red-400 border-red-900/50'}`}>
                           <div className="font-semibold mb-1 flex items-center">
                              {testStatus.success ? <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> : <XCircle className="w-3.5 h-3.5 mr-1.5" />}
                              {testStatus.success ? 'Success' : 'Connection Failed'}
                           </div>
                           {Object.entries(testStatus.messages).map(([k, v]) => (
                              <div key={k} className="mt-1 opacity-90 truncate leading-relaxed" title={`${k}: ${v}`}>- {k}: {v}</div>
                           ))}
                        </div>
                     )}
                  </div>

                  {/* Dataset Upload */}
                  <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg space-y-3">
                     <label className="block text-sm font-medium text-gray-300">📁 Custom Dataset (Optional)</label>
                     <input
                        type="file" accept=".csv,.xlsx"
                        onChange={(e) => setDatasetFile(e.target.files ? e.target.files[0] : null)}
                        className="w-full text-sm text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#374151] file:text-white hover:file:bg-[#4b5563]"
                     />
                     {task && (
                        <p className="text-xs text-gray-500 mt-1">
                           Required cols: {task === 'summarization' ? 'text, summary' : task === 'question_answering' ? 'text, question, answer' : 'text, sarcasm'}
                        </p>
                     )}
                  </div>

                  {/* Advanced / Eval Settings */}
                  <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg space-y-4">
                     <div>
                        <label className="block text-sm font-medium mb-2 text-gray-300">Samples (N)</label>
                        <input
                           type="number" min="1" max="1000"
                           value={numSamples} onChange={(e) => setNumSamples(Number(e.target.value))}
                           className="w-full bg-[#1f2937] border border-gray-700 rounded p-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                        />
                     </div>

                     {/* Checkpoint Mode */}
                     <div className="pt-2 border-t border-gray-700/50">
                        <label className="flex items-center text-sm font-medium text-gray-300 mb-2 cursor-pointer group">
                           <input type="checkbox" className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
                              checked={enableCheckpointMode} onChange={(e) => setEnableCheckpointMode(e.target.checked)} />
                           💾 Enable Checkpoint Mode
                        </label>
                        {enableCheckpointMode && (
                           <div className="mt-2 ml-6">
                              <label className="block text-xs text-gray-400 mb-1">Save Every N Samples</label>
                              <input
                                 type="number" min="10" max="500" step="10"
                                 value={checkpointInterval} onChange={(e) => setCheckpointInterval(Number(e.target.value))}
                                 className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                              />
                           </div>
                        )}
                     </div>

                     {task !== 'sarcasm' && (
                        <div className="pt-2 border-t border-gray-700/50">
                           <label className="flex items-center text-sm font-medium text-gray-300 mb-2 cursor-pointer group">
                              <input type="checkbox" className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
                                 checked={useSemanticMatching} onChange={(e) => setUseSemanticMatching(e.target.checked)} />
                              <BrainCircuit className="h-4 w-4 mr-1 text-[#4FC3F7] group-hover:text-[#29b6f6]" /> Use Semantic Eval
                           </label>
                           {useSemanticMatching && (
                              <div className="space-y-2 mt-2 ml-6">
                                 <select
                                    className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                                    value={geminiModel} onChange={(e) => setGeminiModel(e.target.value)}
                                 >
                                    <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</option>
                                    <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                                    <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                                    <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                                    <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                                    <option value="gemini-2.0-pro">gemini-2.0-pro</option>
                                 </select>
                                 <input
                                    type="password" placeholder="Gemini API Key required"
                                    value={geminiApiKey} onChange={(e) => setGeminiApiKey(e.target.value)}
                                    className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                                 />
                              </div>
                           )}
                        </div>
                     )}
                  </div>
               </div>

               {/* Global Action */}
               <div className="mt-8 pt-4 border-t border-gray-800">
                  <button
                     onClick={handleRunBenchmark}
                     disabled={isRunning || !apiKey}
                     className={`w-full py-3.5 font-semibold text-sm rounded-lg flex items-center justify-center transition-all duration-200 shadow-lg  ${isRunning ? 'bg-[#1f2937] text-gray-500 cursor-not-allowed shadow-none' : 'bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19]'}`}
                  >
                     {isRunning ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4 fill-current" />}
                     {isRunning ? 'Running...' : 'Run Benchmark'}
                  </button>
               </div>
            </aside>
         )}

         {/* Main Content Area */}
         <main className="flex-1 flex flex-col min-w-0 relative bg-gradient-to-br from-[#0b0f19] to-[#111827]">
            <header className="px-10 py-5 border-b border-gray-800 bg-[#0b0f19] z-10 shrink-0">
               <div className="flex items-center justify-between mb-4">
                  <h1 className="text-[2.2rem] font-bold text-white tracking-tight flex items-center">
                     <LayoutTemplate className="h-8 w-8 mr-3 text-[#32C4B7]" />
                     Framework for Open-Source Multilingual Large Language Models
                  </h1>
                  <div className="flex items-center space-x-6">
                     <img src="/assets/Fayoum University Logo.jpeg" alt="Fayoum University" className="h-16 object-contain" />
                     <img src="/assets/FCAI Fayoum University Logo.jpeg" alt="FCAI Fayoum University" className="h-16 object-contain" />
                  </div>
               </div>
               <p className="text-gray-400 text-sm max-w-4xl leading-relaxed">
                  Evaluate and compare state-of-the-art Arabic Large Language Models.
                  Results are evaluated via unified heuristics across Q&A, Text Summarization, and Sarcasm detection tasks.
               </p>

               <div className="flex space-x-6 mt-8 border-b border-gray-800">
                  <button
                     className={`pb-3 font-semibold text-sm transition-colors border-b-2 flex items-center ${mainView === 'benchmark' ? 'text-[#32C4B7] border-[#32C4B7]' : 'text-gray-400 border-transparent hover:text-gray-200'}`}
                     onClick={() => setMainView('benchmark')}
                  >
                     <LayoutTemplate className="w-4 h-4 mr-2" /> Benchmark
                  </button>
                  <button
                     className={`pb-3 font-semibold text-sm transition-colors border-b-2 flex items-center ${mainView === 'leaderboard' ? 'text-[#32C4B7] border-[#32C4B7]' : 'text-gray-400 border-transparent hover:text-gray-200'}`}
                     onClick={() => setMainView('leaderboard')}
                  >
                     <BarChart2 className="w-4 h-4 mr-2" /> Leaderboard
                  </button>
               </div>
            </header>

            {/* Dashboard Stage */}
            <div className="p-10 flex-1 overflow-y-auto scrollbar-thin">

               {mainView === 'leaderboard' ? (
                  <div className="w-full max-w-6xl mx-auto">
                     <div className="flex space-x-2 mb-8 border-b border-gray-800 pb-2">
                        {['question_answering', 'summarization', 'sarcasm'].map(t => (
                           <button key={t} onClick={() => setLeaderboardTask(t)}
                              className={`px-5 py-2.5 text-sm font-bold rounded-t-lg transition-all ${leaderboardTask === t ? 'bg-[#32C4B7] text-[#0b0f19] shadow-[0_-4px_10px_rgba(50,196,183,0.2)]' : 'text-gray-400 hover:text-gray-200 hover:bg-[#1f2937]'}`}>
                              {t === 'question_answering' ? 'Question Answering' : t === 'summarization' ? 'Summarization' : 'Sarcasm Detection'}
                           </button>
                        ))}
                     </div>

                     {isLoadingLeaderboard && (
                        <div className="flex items-center justify-center p-20 text-gray-400">
                           <Loader2 className="animate-spin mr-3 h-8 w-8 text-[#32C4B7]" />
                           <span className="text-lg">Loading leaderboard data...</span>
                        </div>
                     )}

                     {leaderboardError && (
                        <div className="text-red-400 bg-red-950/50 border border-red-900/50 p-6 rounded-xl flex items-center shadow-lg">
                           <XCircle className="w-6 h-6 mr-3 shrink-0" />
                           {leaderboardError}
                        </div>
                     )}

                     {!isLoadingLeaderboard && leaderboardData && leaderboardData[leaderboardTask] && (
                        <div className="bg-[#111827] border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden ring-1 ring-white/5">
                           <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse whitespace-nowrap">
                                 <thead>
                                    <tr className="bg-gradient-to-r from-[#1f2937]/80 to-[#111827] border-b border-gray-700/80">
                                       <th className="p-5 font-bold text-[#32C4B7] text-sm uppercase tracking-wider sticky left-0 bg-[#1f2937] z-10 w-16 text-center">Rank</th>
                                       {Object.keys(leaderboardData[leaderboardTask][0]).map((k, i) => (
                                          <th 
                                             key={k} 
                                             className={`p-5 font-bold text-gray-300 text-xs uppercase tracking-wider cursor-pointer hover:bg-gray-700/50 transition-colors ${i === 0 ? 'sticky left-16 bg-[#1f2937] z-10 shadow-[2px_0_5px_rgba(0,0,0,0.1)]' : ''}`}
                                             onClick={() => {
                                                if (sortConfig?.key === k) {
                                                   if (sortConfig.direction === 'desc') setSortConfig({ key: k, direction: 'asc' });
                                                   else setSortConfig(null);
                                                } else {
                                                   setSortConfig({ key: k, direction: 'desc' });
                                                }
                                             }}
                                          >
                                             <div className="flex items-center space-x-1">
                                                <span>{k.replace(/_/g, ' ')}</span>
                                                {sortConfig?.key === k && (
                                                   <span className="text-[#32C4B7] font-sans">{sortConfig.direction === 'desc' ? '↓' : '↑'}</span>
                                                )}
                                             </div>
                                          </th>
                                       ))}
                                    </tr>
                                 </thead>
                                 <tbody className="divide-y divide-gray-800/60">
                                    {(sortConfig ? [...leaderboardData[leaderboardTask]].sort((a, b) => {
                                       if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
                                       if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
                                       return 0;
                                    }) : leaderboardData[leaderboardTask]).map((row, idx) => {
                                       const isTop1 = idx === 0;
                                       const isTop2 = idx === 1;
                                       const isTop3 = idx === 2;

                                       let rankDisplay = `#${idx + 1}`;
                                       let rankClass = "text-gray-400 font-medium";
                                       let rowClass = "hover:bg-[#1f2937]/40 transition-colors duration-150";

                                       if (isTop1) {
                                          rankDisplay = "🥇 1";
                                          rankClass = "text-yellow-400 font-black text-lg drop-shadow-[0_0_8px_rgba(250,204,21,0.4)]";
                                          rowClass += " bg-gradient-to-r from-yellow-900/10 to-transparent";
                                       } else if (isTop2) {
                                          rankDisplay = "🥈 2";
                                          rankClass = "text-gray-300 font-bold text-lg drop-shadow-[0_0_8px_rgba(209,213,219,0.3)]";
                                          rowClass += " bg-gradient-to-r from-gray-700/10 to-transparent";
                                       } else if (isTop3) {
                                          rankDisplay = "🥉 3";
                                          rankClass = "text-amber-600 font-bold text-lg drop-shadow-[0_0_8px_rgba(217,119,6,0.3)]";
                                          rowClass += " bg-gradient-to-r from-amber-900/10 to-transparent";
                                       }

                                       return (
                                          <tr key={idx} className={rowClass}>
                                             <td className={`p-4 text-center sticky left-0 ${isTop1 ? 'bg-[#182132]' : isTop2 ? 'bg-[#151d2c]' : isTop3 ? 'bg-[#141b2a]' : 'bg-[#111827]'} group-hover:bg-[#1f2937]/40 z-10 ${rankClass}`}>
                                                {rankDisplay}
                                             </td>
                                             {Object.entries(row).map(([k, v], i) => (
                                                <td key={k} className={`p-4 ${i === 0 ? `font-semibold sticky left-16 z-10 shadow-[2px_0_5px_rgba(0,0,0,0.1)] ${isTop1 ? 'text-yellow-400 bg-[#182132]' : isTop2 ? 'text-gray-200 bg-[#151d2c]' : isTop3 ? 'text-amber-500 bg-[#141b2a]' : 'text-[#32C4B7] bg-[#111827]'}` : 'text-gray-300 font-mono text-sm'}`}>
                                                   {typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(4) : String(v)}
                                                </td>
                                             ))}
                                          </tr>
                                       );
                                    })}
                                 </tbody>
                              </table>
                           </div>
                        </div>
                     )}

                     {!isLoadingLeaderboard && leaderboardData && !leaderboardData[leaderboardTask] && (
                        <div className="flex flex-col items-center justify-center p-20 bg-[#111827]/50 border border-gray-800 rounded-xl border-dashed">
                           <Database className="w-12 h-12 text-gray-600 mb-4" />
                           <p className="text-gray-400 text-lg">No leaderboard data found for {leaderboardTask.replace(/_/g, ' ')}.</p>
                           <p className="text-gray-500 text-sm mt-2">Run some benchmarks to generate results!</p>
                        </div>
                     )}
                  </div>
               ) : (
                  <>
                     {errorMsg && (
                        <div className="mb-8 bg-red-950 border border-red-900 text-red-200 px-5 py-4 rounded-xl flex items-start shadow-xl">
                           <XCircle className="w-5 h-5 mr-3 shrink-0 mt-0.5 text-red-400" />
                           <span className="leading-relaxed">{errorMsg}</span>
                        </div>
                     )}

                     {/* Configuration and Status Cards (Mirrors Streamlit Main Area) */}
                     {(!results?.success || isRunning) && (
                        <div className="grid grid-cols-3 gap-8 mb-8">
                           {/* Prompt Configuration */}
                           <div className="col-span-2 bg-[#111827] border border-gray-700/50 rounded-xl p-6 shadow-lg">
                              <h3 className="text-lg font-bold text-white mb-4">Prompt Configuration</h3>
                              <label className="flex items-center text-sm font-medium text-gray-300 mb-4 cursor-pointer group w-fit">
                                 <input type="checkbox" className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
                                    checked={customPrompt !== null} onChange={(e) => setCustomPrompt(e.target.checked ? '' : null)} />
                                 Use Custom Prompt Template
                              </label>
                              {customPrompt !== null ? (
                                 <div className="space-y-3">
                                    <h4 className="text-sm font-bold text-white">Custom Prompt Template</h4>
                                    <textarea
                                       placeholder="Example: Analyze the sentiment: {text}"
                                       className="w-full h-28 bg-[#1f2937] border border-gray-700 rounded-md p-3 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7] resize-none"
                                       value={customPrompt} onChange={(e) => setCustomPrompt(e.target.value)}
                                    ></textarea>
                                    {customPrompt && <div className="text-xs bg-green-900/10 text-green-400 border border-green-900/50 p-2 rounded">✅ Custom prompt will be used</div>}
                                 </div>
                              ) : (
                                 <div className="text-sm bg-blue-900/10 text-blue-400 border border-blue-900/50 p-3 rounded">
                                    ℹ️ Default prompt template will be used
                                 </div>
                              )}
                           </div>

                           {/* Status Reference */}
                           <div className="col-span-1 bg-[#111827] border border-gray-700/50 rounded-xl p-6 shadow-lg">
                              <h3 className="text-lg font-bold text-white mb-4">Benchmark Status</h3>
                              <div className="space-y-2 text-sm text-gray-300">
                                 <p><strong className="text-white">Task:</strong> {task === 'question_answering' ? 'Question Answering' : task === 'summarization' ? 'Text Summarization' : 'Sarcasm Detection'}</p>
                                 <p><strong className="text-white">Models:</strong> {models.length}</p>
                                 <p><strong className="text-white">Samples:</strong> {numSamples}</p>
                                 <p><strong className="text-white">Dataset:</strong> Default</p>
                                 <p><strong className="text-white">Evaluation:</strong> {useSemanticMatching ? 'Metrics + LLM as a Judge (Gemini)' : 'Metrics'}</p>
                                 <p className="mt-4 pt-4 border-t border-gray-700 text-xs text-gray-500">
                                    💡 API keys are only stored in memory for this session
                                 </p>
                              </div>
                           </div>
                        </div>
                     )}

                     {/* Running Spinner/Progress Container */}
                     {isRunning && !progress && (
                        <div className="mb-8 max-w-4xl bg-[#111827] border border-gray-700/50 rounded-xl p-8 shadow-2xl flex items-center">
                           <Loader2 className="animate-spin text-[#32C4B7] mr-4 h-8 w-8" />
                           <h3 className="text-xl font-bold text-white">Connecting to server and initializing workflow...</h3>
                        </div>
                     )}

                     {isRunning && progress && (
                        <div className="mb-8 w-full bg-[#111827] border border-gray-700/50 rounded-xl p-8 shadow-2xl">
                           <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                              <Loader2 className="animate-spin text-[#32C4B7] mr-3 h-6 w-6" />
                              🔄 Benchmark Progress
                           </h3>

                           <div className="w-full bg-gray-900 rounded-full h-3.5 border border-gray-800 p-0.5 relative mb-6">
                              <div className="bg-[#32C4B7] h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(50,196,183,0.4)]" style={{ width: `${(progress.current / progress.total) * 100}%` }}></div>
                           </div>

                           <div className="grid grid-cols-3 gap-6">
                              <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
                                 <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Current Stage</span>
                                 <span className="text-xl font-bold text-white">{progress.current < 20 ? '🔧 Initialization' : progress.current < 80 ? '⚙️ Processing' : '📊 Evaluation'}</span>
                              </div>
                              <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
                                 <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Progress</span>
                                 <span className="text-xl font-bold text-white">{Math.round((progress.current / progress.total) * 100)}%</span>
                              </div>
                              <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
                                 <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Status</span>
                                 <span className="text-sm font-medium text-[#32C4B7] truncate" title={progress.status}>{progress.status}</span>
                              </div>
                           </div>
                        </div>
                     )}

                     {results?.success ? (
                        <div className="bg-[#111827] border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden max-w-6xl mb-8">
                           {/* Download Section */}
                           <div className="p-6 border-b border-gray-700/50 bg-[#1f2937]/30">
                              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                                 <Download className="h-5 w-5 mr-2 text-[#32C4B7]" /> Download Results
                              </h3>
                              <div className="flex flex-wrap gap-4">
                                 {results.comparison_excel_path && (
                                    <button
                                       onClick={() => window.open(`${API_BASE}/download?file_path=${encodeURIComponent(results.comparison_excel_path)}`, '_blank')}
                                       className="px-4 py-2 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-semibold rounded shadow transition-colors flex items-center text-sm"
                                    >
                                       <BarChart2 className="h-4 w-4 mr-2" /> Download Comparison Summary
                                    </button>
                                 )}
                                 {results.excel_path && !results.comparison_excel_path && (
                                    <button
                                       onClick={() => window.open(`${API_BASE}/download?file_path=${encodeURIComponent(results.excel_path)}`, '_blank')}
                                       className="px-4 py-2 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-semibold rounded shadow transition-colors flex items-center text-sm"
                                    >
                                       <BarChart2 className="h-4 w-4 mr-2" /> Download Summary Results
                                    </button>
                                 )}
                                 {results.detailed_samples_path && (
                                    <button
                                       onClick={() => window.open(`${API_BASE}/download?file_path=${encodeURIComponent(results.detailed_samples_path)}`, '_blank')}
                                       className="px-4 py-2 bg-[#374151] hover:bg-[#4b5563] text-gray-200 font-semibold rounded shadow transition-colors flex items-center text-sm"
                                    >
                                       <Database className="h-4 w-4 mr-2" /> Download Detailed Samples
                                    </button>
                                 )}
                              </div>
                           </div>

                           {/* Tabs */}
                           <div className="flex border-b border-gray-700/50 bg-[#0b0f19]">
                              <button
                                 onClick={() => setActiveTab('summary')}
                                 className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'summary' ? 'border-[#32C4B7] text-[#32C4B7]' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
                              >📊 Summary</button>
                              {results?.stats?.semantic_matching_enabled && (
                                 <button
                                    onClick={() => setActiveTab('llm')}
                                    className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'llm' ? 'border-[#32C4B7] text-[#32C4B7]' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
                                 >🧠 LLM Analysis</button>
                              )}
                              <button
                                 onClick={() => setActiveTab('scores')}
                                 className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'scores' ? 'border-[#32C4B7] text-[#32C4B7]' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
                              >📈 Detailed Scores</button>
                              <button
                                 onClick={() => setActiveTab('stats')}
                                 className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'stats' ? 'border-[#32C4B7] text-[#32C4B7]' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
                              >📋 Statistics</button>
                           </div>

                           {/* Tab Content */}
                           <div className="p-6">
                              {activeTab === 'summary' && (
                                 <div>
                                    <h3 className="text-xl font-bold text-white mb-6">Benchmark Summary</h3>
                                    <div className="overflow-x-auto">
                                       <table className="w-full text-sm text-left">
                                          <thead className="text-xs text-gray-400 uppercase bg-[#1f2937]/50 border-b border-gray-700">
                                             <tr>
                                                <th className="px-6 py-4 font-semibold tracking-wider">Model Configuration</th>
                                                <th className="px-6 py-4 font-semibold tracking-wider">Total Examples</th>
                                                <th className="px-6 py-4 font-semibold tracking-wider">Errors</th>
                                                <th className="px-6 py-4 font-semibold tracking-wider">API Success Rate</th>
                                                <th className="px-6 py-4 font-semibold tracking-wider">Primary Score</th>
                                             </tr>
                                          </thead>
                                          <tbody className="divide-y divide-gray-800">
                                             {Object.entries((results as any).model_results).map(([model, metrics]: [string, any]) => {
                                                const stats = metrics.stats || {};
                                                const scores = metrics.scores || {};
                                                const n_examples = stats.n_examples || 1;
                                                const n_errors = stats.n_errors || 0;
                                                const success_rate = ((n_examples - n_errors) / Math.max(n_examples, 1)) * 100;

                                                let primaryScoreStr = "N/A";
                                                const acc = scores.Accuracy ?? scores.accuracy;
                                                const r1 = scores.ROUGE1 ?? scores.rouge1;
                                                const rl = scores.ROUGEL ?? scores.rougeL ?? scores.ROUGE ?? scores.rouge;
                                                const em = scores.EM ?? scores.em;
                                                const f1 = scores.F1 ?? scores.f1;

                                                if (acc !== undefined && typeof acc === 'number') primaryScoreStr = `Accuracy: ${acc.toFixed(3)}`;
                                                else if (r1 !== undefined && typeof r1 === 'number') primaryScoreStr = `ROUGE-1: ${r1.toFixed(3)}`;
                                                else if (rl !== undefined && typeof rl === 'number') primaryScoreStr = `ROUGE-L: ${rl.toFixed(3)}`;
                                                else if (em !== undefined && typeof em === 'number') primaryScoreStr = `EM: ${em.toFixed(3)}`;
                                                else if (f1 !== undefined && typeof f1 === 'number') primaryScoreStr = `F1: ${f1.toFixed(3)}`;

                                                return (
                                                   <tr key={model} className="hover:bg-[#1f2937]/40 transition-colors">
                                                      <td className="px-6 py-4 font-semibold text-gray-200">
                                                         <div className="flex items-center">
                                                            <div className="w-2 h-2 rounded-full bg-[#32C4B7] mr-3"></div>
                                                            {model.replace(':free', '')}
                                                         </div>
                                                      </td>
                                                      <td className="px-6 py-4 text-gray-300 font-mono">{n_examples}</td>
                                                      <td className="px-6 py-4 text-gray-300 font-mono text-red-400">{n_errors}</td>
                                                      <td className="px-6 py-4 text-gray-300 font-mono">{success_rate.toFixed(1)}%</td>
                                                      <td className="px-6 py-4 text-[#32C4B7] font-mono font-semibold">{primaryScoreStr}</td>
                                                   </tr>
                                                );
                                             })}
                                          </tbody>
                                       </table>
                                    </div>
                                 </div>
                              )}

                              {activeTab === 'llm' && (
                                 <div>
                                    <h3 className="text-xl font-bold text-white mb-6">Semantic Matching Analysis</h3>
                                    <div className="space-y-6">
                                       {Object.entries((results as any).model_results).map(([model, metrics]: [string, any]) => {
                                          const stats = metrics.stats || {};
                                          const avg_conf = stats.avg_semantic_confidence || 0;
                                          return (
                                             <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                                                <h4 className="font-bold text-gray-200 mb-4">{model.replace(':free', '')}</h4>
                                                <div className="grid grid-cols-3 gap-4 mb-4">
                                                   <div className="bg-[#111827] p-3 rounded">
                                                      <div className="text-xs text-gray-500 mb-1">Semantic Matches</div>
                                                      <div className="text-lg font-bold text-white">{stats.semantic_matches || 0}</div>
                                                   </div>
                                                   <div className="bg-[#111827] p-3 rounded">
                                                      <div className="text-xs text-gray-500 mb-1">Semantic Match Rate</div>
                                                      <div className="text-lg font-bold text-white">{((stats.semantic_match_rate || 0) * 100).toFixed(1)}%</div>
                                                   </div>
                                                   <div className="bg-[#111827] p-3 rounded">
                                                      <div className="text-xs text-gray-500 mb-1">Avg Confidence</div>
                                                      <div className="text-lg font-bold text-white">{avg_conf.toFixed(2)}</div>
                                                   </div>
                                                </div>
                                                {avg_conf >= 0.7 ? (
                                                   <div className="text-sm text-green-400 flex items-center"><CheckCircle2 className="w-4 h-4 mr-2" /> High confidence - model outputs are semantically very close</div>
                                                ) : avg_conf >= 0.4 ? (
                                                   <div className="text-sm text-yellow-400 flex items-center">⚠️ Moderate confidence - some outputs differ but convey similar meaning</div>
                                                ) : (
                                                   <div className="text-sm text-red-400 flex items-center"><XCircle className="w-4 h-4 mr-2" /> Low confidence - significant semantic differences</div>
                                                )}
                                             </div>
                                          )
                                       })}
                                    </div>
                                 </div>
                              )}

                              {activeTab === 'scores' && (
                                 <div>
                                    <h3 className="text-xl font-bold text-white mb-6">Detailed Scores</h3>
                                    <div className="space-y-6">
                                       {Object.entries((results as any).model_results).map(([model, metrics]: [string, any]) => (
                                          <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                                             <h4 className="font-bold text-[#32C4B7] mb-4 text-lg">{model.replace(':free', '')}</h4>
                                             <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                {Object.entries(metrics.scores || {}).map(([key, value]) => (
                                                   <div key={key} className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm flex flex-col justify-center transition-transform hover:scale-[1.02]">
                                                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1 truncate" title={key}>{key}</div>
                                                      <div className="text-xl font-bold text-white">
                                                         {typeof value === 'number' ? value.toFixed(4) : String(value)}
                                                      </div>
                                                   </div>
                                                ))}
                                                {Object.keys(metrics.scores || {}).length === 0 && (
                                                   <div className="text-sm text-gray-500 col-span-full">No detailed scores available.</div>
                                                )}
                                             </div>
                                          </div>
                                       ))}
                                    </div>
                                 </div>
                              )}

                              {activeTab === 'stats' && (
                                 <div>
                                    <h3 className="text-xl font-bold text-white mb-6">Processing Statistics</h3>
                                    <div className="space-y-6">
                                       {Object.entries((results as any).model_results).map(([model, metrics]: [string, any]) => {
                                          const stats = metrics.stats || {};
                                          return (
                                             <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                                                <h4 className="font-bold text-[#32C4B7] mb-4 text-lg">{model.replace(':free', '')}</h4>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                   <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                                                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Total Examples</div>
                                                      <div className="text-xl font-bold text-white">{stats.n_examples || 0}</div>
                                                   </div>
                                                   <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                                                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Successful</div>
                                                      <div className="text-xl font-bold text-green-400">{stats.n_successful || (stats.n_examples - (stats.n_errors || 0)) || 0}</div>
                                                   </div>
                                                   <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                                                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Errors</div>
                                                      <div className={`text-xl font-bold ${stats.n_errors > 0 ? 'text-red-400' : 'text-gray-300'}`}>{stats.n_errors || 0}</div>
                                                   </div>
                                                   <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                                                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Success Rate</div>
                                                      <div className="text-xl font-bold text-white">{((stats.api_success_rate || 0) * 100).toFixed(1)}%</div>
                                                   </div>
                                                </div>

                                                {/* Additional stats if they exist and aren't the basic ones or semantic ones */}
                                                {Object.keys(stats).filter(k => !['n_examples', 'n_successful', 'n_errors', 'api_success_rate', 'semantic_matches', 'semantic_match_rate', 'avg_semantic_confidence', 'semantic_matching_enabled'].includes(k)).length > 0 && (
                                                   <div className="mt-4 pt-4 border-t border-gray-700/50">
                                                      <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Other Information</h5>
                                                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                         {Object.entries(stats)
                                                            .filter(([k]) => !['n_examples', 'n_successful', 'n_errors', 'api_success_rate', 'semantic_matches', 'semantic_match_rate', 'avg_semantic_confidence', 'semantic_matching_enabled'].includes(k))
                                                            .map(([key, value]) => (
                                                               <div key={key} className="bg-[#111827] p-3 rounded border border-gray-800 shadow-sm">
                                                                  <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1 truncate" title={key}>{key.replace(/_/g, ' ')}</div>
                                                                  <div className="text-sm font-medium text-gray-300 truncate" title={String(value)}>
                                                                     {typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(4) : String(value)}
                                                                  </div>
                                                               </div>
                                                            ))
                                                         }
                                                      </div>
                                                   </div>
                                                )}
                                             </div>
                                          );
                                       })}
                                    </div>
                                 </div>
                              )}
                           </div>
                        </div>
                     ) : null}
                  </>
               )}
            </div> {/* closes p-10 */}
         </main>
      </div>
   );
}