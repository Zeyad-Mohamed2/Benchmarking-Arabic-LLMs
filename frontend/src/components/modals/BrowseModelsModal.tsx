import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  Search,
  Check,
  Plus,
  Sparkles,
  Cpu,
  Trash2,
} from 'lucide-react';
import { ProviderType, ModelCatalogItem } from '../../types';
import {
  getAllModels,
  saveCustomModel,
  removeCustomModel,
} from '../../data/modelsCatalog';

interface BrowseModelsModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider: ProviderType;
  selectedModelIds: string[];
  onApplySelection: (selectedModels: ModelCatalogItem[]) => void;
}

export const BrowseModelsModal: React.FC<BrowseModelsModalProps> = ({
  isOpen,
  onClose,
  provider,
  selectedModelIds,
  onApplySelection,
}) => {
  const [activeTabProvider, setActiveTabProvider] = useState<ProviderType>(provider);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterFreeOnly, setFilterFreeOnly] = useState(false);
  const [tempSelectedIds, setTempSelectedIds] = useState<string[]>(selectedModelIds);

  // Custom model form state
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [customSlug, setCustomSlug] = useState('');
  const [customName, setCustomName] = useState('');
  const [customParamSize, setCustomParamSize] = useState('7B');
  const [customIsFree, setCustomIsFree] = useState(true);

  if (!isOpen) return null;

  const catalog = getAllModels(activeTabProvider);

  const filteredModels = catalog.filter((m) => {
    const matchesQuery =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.tags && m.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())));

    if (filterFreeOnly && !m.isFree) return false;
    return matchesQuery;
  });

  const toggleSelect = (modelId: string) => {
    if (tempSelectedIds.includes(modelId)) {
      setTempSelectedIds(tempSelectedIds.filter((id) => id !== modelId));
    } else {
      if (tempSelectedIds.length >= 3) {
        alert('You can select up to 3 models simultaneously for comparison.');
        return;
      }
      setTempSelectedIds([...tempSelectedIds, modelId]);
    }
  };

  // Presets
  const applyPreset = (presetType: 'free' | 'giants' | 'groq') => {
    if (presetType === 'free') {
      setActiveTabProvider('openrouter');
      setTempSelectedIds([
        'google/gemma-3-27b-it:free',
        'openai/gpt-oss-20b:free',
        'qwen/qwen3-4b:free',
      ]);
    } else if (presetType === 'giants') {
      setActiveTabProvider('openrouter');
      setTempSelectedIds([
        'meta-llama/llama-3.3-70b-instruct:free',
        'qwen/qwen-2.5-72b-instruct',
        'google/gemma-3-27b-it:free',
      ]);
    } else if (presetType === 'groq') {
      setActiveTabProvider('groq');
      setTempSelectedIds([
        'qwen/qwen3-32b',
        'meta-llama/llama-4-maverick-17b-128e-instruct',
        'openai/gpt-oss-20b',
      ]);
    }
  };

  const handleAddCustomModel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customSlug.trim()) return alert('Please enter a valid model slug');

    const newModel: ModelCatalogItem = {
      id: customSlug.trim(),
      name: customName.trim() || customSlug.trim(),
      provider: activeTabProvider,
      paramSize: customParamSize.trim() || 'Custom',
      isFree: customIsFree,
      description: 'Custom user-defined model endpoint.',
      tags: ['Custom', customParamSize.trim() || 'LLM'],
      isCustom: true,
    };

    saveCustomModel(newModel);
    // Add to selected if space
    if (tempSelectedIds.length < 3) {
      setTempSelectedIds([...tempSelectedIds, newModel.id]);
    }
    setCustomSlug('');
    setCustomName('');
    setShowAddCustom(false);
  };

  const handleDeleteCustom = (modelId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    removeCustomModel(modelId);
    setTempSelectedIds(tempSelectedIds.filter((id) => id !== modelId));
  };

  const handleApply = () => {
    const all = getAllModels();
    const selectedObjs = tempSelectedIds
      .map((id) => all.find((m) => m.id === id) || { id, name: id, provider: activeTabProvider })
      .slice(0, 3);
    onApplySelection(selectedObjs);
    onClose();
  };

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto animate-fadeIn">
      <div className="bg-[#111827] border border-gray-700/80 rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-800 flex items-center justify-between bg-[#0b0f19]">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-[#32C4B7]" />
              Browse & Select Models
            </h3>
            <p className="text-xs text-gray-400 mt-1">
              Select up to 3 models to benchmark simultaneously. Compare across architectures, parameter sizes, and provider tiers.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Top Controls: Provider Switcher, Presets, and Filters */}
        <div className="p-5 border-b border-gray-800/80 bg-[#161f30] space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Provider Tabs */}
            <div className="flex bg-[#0b0f19] rounded-lg p-1 border border-gray-700">
              <button
                onClick={() => setActiveTabProvider('openrouter')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTabProvider === 'openrouter'
                    ? 'bg-[#32C4B7] text-[#0b0f19] shadow'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                OpenRouter Catalog
              </button>
              <button
                onClick={() => setActiveTabProvider('groq')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTabProvider === 'groq'
                    ? 'bg-[#32C4B7] text-[#0b0f19] shadow'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Groq (LPU Speed)
              </button>
            </div>

            {/* Presets */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 font-medium flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-yellow-400" /> Presets:
              </span>
              <button
                onClick={() => applyPreset('free')}
                className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 px-2.5 py-1 rounded border border-gray-700 transition"
              >
                ⚡ Free Arabic
              </button>
              <button
                onClick={() => applyPreset('giants')}
                className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 px-2.5 py-1 rounded border border-gray-700 transition"
              >
                🧠 70B+ Giants
              </button>
              <button
                onClick={() => applyPreset('groq')}
                className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 px-2.5 py-1 rounded border border-gray-700 transition"
              >
                🏎️ Fast Groq
              </button>
            </div>
          </div>

          {/* Search bar & Free only checkbox */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search models by name, slug (e.g. llama-3, qwen), or tag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#0b0f19] border border-gray-700 rounded-lg pl-9 pr-4 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7]"
              />
            </div>

            <label className="flex items-center text-xs text-gray-300 cursor-pointer select-none bg-[#0b0f19] px-3 py-2 rounded-lg border border-gray-700 hover:border-gray-600 transition">
              <input
                type="checkbox"
                checked={filterFreeOnly}
                onChange={(e) => setFilterFreeOnly(e.target.checked)}
                className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
              />
              🟢 Free Tier Only
            </label>

            <button
              onClick={() => setShowAddCustom(!showAddCustom)}
              className="text-xs flex items-center gap-1.5 bg-[#32C4B7]/20 hover:bg-[#32C4B7]/30 text-[#32C4B7] border border-[#32C4B7]/40 px-3 py-2 rounded-lg font-medium transition"
            >
              <Plus className="w-3.5 h-3.5" />
              {showAddCustom ? 'Hide Custom Form' : '➕ Plug Custom Model'}
            </button>
          </div>

          {/* Collapsible Add Custom Model Form */}
          {showAddCustom && (
            <form
              onSubmit={handleAddCustomModel}
              className="bg-[#0b0f19] p-4 rounded-xl border border-[#32C4B7]/40 space-y-3 animate-fadeIn"
            >
              <h4 className="text-xs font-bold text-[#32C4B7] uppercase tracking-wider">
                Plug a New Model (OpenRouter / Groq / HuggingFace Slug)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-400 mb-1">Model Slug (API identifier)</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. mistralai/mistral-large-2411 or custom-provider/model-name"
                    value={customSlug}
                    onChange={(e) => setCustomSlug(e.target.value)}
                    className="w-full bg-[#111827] border border-gray-700 rounded p-2 text-xs text-white focus:outline-none focus:border-[#32C4B7]"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Display Name (optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Mistral Large Arabic"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    className="w-full bg-[#111827] border border-gray-700 rounded p-2 text-xs text-white focus:outline-none focus:border-[#32C4B7]"
                  />
                </div>
              </div>
              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <label className="text-gray-400 mr-2">Param Size:</label>
                    <input
                      type="text"
                      placeholder="e.g. 70B"
                      value={customParamSize}
                      onChange={(e) => setCustomParamSize(e.target.value)}
                      className="w-16 bg-[#111827] border border-gray-700 rounded p-1 text-xs text-white"
                    />
                  </div>
                  <label className="flex items-center text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={customIsFree}
                      onChange={(e) => setCustomIsFree(e.target.checked)}
                      className="mr-1.5 rounded border-gray-700 text-[#32C4B7]"
                    />
                    Free endpoint
                  </label>
                </div>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-bold text-xs rounded transition"
                >
                  Save & Add to Catalog
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Models Grid */}
        <div className="p-6 overflow-y-auto flex-1 custom-scrollbar scrollbar-thin space-y-3">
          {filteredModels.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-sm">
              No models match your search or filter. You can plug any model using the "➕ Plug Custom Model" button above!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {filteredModels.map((m) => {
                const isSelected = tempSelectedIds.includes(m.id);
                return (
                  <div
                    key={m.id}
                    onClick={() => toggleSelect(m.id)}
                    className={`relative p-4 rounded-xl border transition-all cursor-pointer select-none flex flex-col justify-between ${
                      isSelected
                        ? 'bg-[#1e293b]/90 border-[#32C4B7] ring-1 ring-[#32C4B7]/50 shadow-[0_0_15px_rgba(50,196,183,0.15)]'
                        : 'bg-[#111827] border-gray-800 hover:border-gray-700 hover:bg-[#151d2d]'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-5 h-5 rounded-md flex items-center justify-center text-xs font-bold transition-colors ${
                              isSelected
                                ? 'bg-[#32C4B7] text-[#0b0f19]'
                                : 'border border-gray-600 bg-gray-800 text-transparent'
                            }`}
                          >
                            {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                          </div>
                          <span className="font-bold text-sm text-white leading-tight">{m.name}</span>
                        </div>

                        {/* Badges */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          {m.isFree && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-green-900/40 text-green-400 border border-green-800/60">
                              FREE
                            </span>
                          )}
                          {m.paramSize && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-900/30 text-blue-300 border border-blue-800/50">
                              {m.paramSize}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-[11px] font-mono text-gray-400 truncate mb-2" title={m.id}>
                        {m.id}
                      </div>

                      {m.description && (
                        <p className="text-xs text-gray-300 line-clamp-2 leading-relaxed mb-3">
                          {m.description}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-gray-800/60 text-[10px] text-gray-500">
                      <div className="flex flex-wrap gap-1">
                        {m.tags &&
                          m.tags.slice(0, 3).map((tag) => (
                            <span
                              key={tag}
                              className="px-1.5 py-0.5 bg-gray-800/80 text-gray-400 rounded text-[10px]"
                            >
                              {tag}
                            </span>
                          ))}
                      </div>

                      {m.isCustom && (
                        <button
                          onClick={(e) => handleDeleteCustom(m.id, e)}
                          className="text-red-400 hover:text-red-300 p-1 rounded hover:bg-red-900/20 transition"
                          title="Delete custom model from catalog"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-gray-800 bg-[#0b0f19] flex items-center justify-between">
          <div className="text-xs text-gray-400">
            <span className="font-bold text-white text-sm mr-1">{tempSelectedIds.length}</span>
            of 3 models selected
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={tempSelectedIds.length === 0}
              className="px-5 py-2 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-bold text-xs rounded-lg shadow-lg transition disabled:opacity-50 flex items-center gap-1.5"
            >
              <Check className="w-4 h-4 stroke-[2.5]" />
              Apply Selection ({tempSelectedIds.length})
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};
