import React from 'react';
import { LayoutTemplate, BarChart2 } from 'lucide-react';

interface HeaderProps {
  mainView: 'benchmark' | 'leaderboard';
  setMainView: (view: 'benchmark' | 'leaderboard') => void;
}

export const Header: React.FC<HeaderProps> = ({ mainView, setMainView }) => {
  return (
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
          className={`pb-3 font-semibold text-sm transition-colors border-b-2 flex items-center ${
            mainView === 'benchmark'
              ? 'text-[#32C4B7] border-[#32C4B7]'
              : 'text-gray-400 border-transparent hover:text-gray-200'
          }`}
          onClick={() => setMainView('benchmark')}
        >
          <LayoutTemplate className="w-4 h-4 mr-2" /> Benchmark
        </button>
        <button
          className={`pb-3 font-semibold text-sm transition-colors border-b-2 flex items-center ${
            mainView === 'leaderboard'
              ? 'text-[#32C4B7] border-[#32C4B7]'
              : 'text-gray-400 border-transparent hover:text-gray-200'
          }`}
          onClick={() => setMainView('leaderboard')}
        >
          <BarChart2 className="w-4 h-4 mr-2" /> Leaderboard
        </button>
      </div>
    </header>
  );
};
