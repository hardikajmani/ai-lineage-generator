import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// We will recreate these in the next step!
import { getLayoutedElements } from './utils/graphParser';
import CustomNode from './components/CustomNode';

const API_BASE_URL = 'http://localhost:8000/api';
const nodeTypes = { customNode: CustomNode };

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- API Calls ---
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/generate`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to generate lineage');
      const data = await response.json();
      console.log('Generation Success:', data);
      // Automatically load the graph once generation is done
      handleLoadGraph();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLoadGraph = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/lineage`);
      if (!response.ok) throw new Error('No lineage found. Please run generation first.');
      const data = await response.json();

      // Pass the API JSON through our layout engine
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(data);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Graph Handlers ---
  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'sans-serif' }}>

      {/* HEADER */}
      <header style={{ padding: '1rem 2rem', backgroundColor: '#1e293b', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>AI Lineage Generator</h1>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            style={{ padding: '0.5rem 1rem', cursor: isGenerating ? 'wait' : 'pointer', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            {isGenerating ? 'AI is Processing...' : '1. Run Lineage Generation'}
          </button>
          <button
            onClick={handleLoadGraph}
            disabled={isLoading}
            style={{ padding: '0.5rem 1rem', cursor: isLoading ? 'wait' : 'pointer', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            {isLoading ? 'Loading...' : '2. Load Lineage Graph'}
          </button>
        </div>
      </header>

      {/* MAIN GRAPH CANVAS */}
      {/* MAIN GRAPH CANVAS */}
      <main style={{ flexGrow: 1, width: '100%', height: '100%', position: 'relative', backgroundColor: '#f8fafc' }}>
        {error && (
          <div style={{ position: 'absolute', top: '1rem', left: '50%', transform: 'translateX(-50%)', zIndex: 10, background: '#fee2e2', color: '#dc2626', padding: '0.5rem 1rem', borderRadius: '4px', border: '1px solid #fca5a5' }}>
            {error}
          </div>
        )}

        {/* Added a strict 100% wrapper for ReactFlow */}
        <div style={{ width: '100%', height: '100%' }}>
          {nodes.length === 0 && !isLoading && !isGenerating && !error ? (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
              <p>Click "Run Lineage Generation" or "Load Lineage Graph" to begin.</p>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.2 }} // Adds a nice margin around the zoomed graph
            >
              <Background color="#ccc" gap={16} />
              <Controls />
            </ReactFlow>
          )}
        </div>
      </main>

      {/* FOOTER */}
      <footer style={{ padding: '0.75rem', backgroundColor: '#1e293b', color: '#94a3b8', textAlign: 'center', fontSize: '0.875rem' }}>
        Made with ❤️ by Hardik Ajmani. 2026
      </footer>

    </div>
  );
}