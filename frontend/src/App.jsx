import { useState, useCallback, useEffect } from 'react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { getLayoutedElements } from './utils/graphParser';
import CustomNode, { NODE_COLORS } from './components/CustomNode';

const API_BASE_URL = 'http://localhost:8000/api';
const nodeTypes = { customNode: CustomNode };

export default function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null); 
  const [zoomLevel, setZoomLevel] = useState(1);

  const [verifiedEdges, setVerifiedEdges] = useState(new Set());
  const [showHighRisk, setShowHighRisk] = useState(false);

  // --- Dynamic Styling Effect with 85% Confidence Logic ---
  useEffect(() => {
    setNodes((nds) => nds.map((node) => ({
      ...node,
      style: { 
        ...node.style, 
        opacity: (showHighRisk && !node.data.is_high_risk) ? 0.2 : 1, 
        transition: 'opacity 0.3s' 
      }
    })));

    setEdges((eds) => eds.map((edge) => {
      const confidence = edge.data.confidence || 0;
      const isHighConfidence = confidence >= 0.85;
      const isVerified = verifiedEdges.has(edge.id);
      
      // Needs review if it's under 85% and hasn't been verified by a human yet
      const needsReview = !isHighConfidence && !isVerified;
      
      // If we are auditing, dim the highly confident/safe edges
      const isDimmed = showHighRisk && isHighConfidence;

      let stroke = '#64748b'; // Default Slate for AI-Confident edges
      let strokeWidth = 2;
      let animated = edge.data.originalAnimated;

      if (isVerified) {
        stroke = '#10b981'; // Human Verified = Solid Green
        strokeWidth = 3;
        animated = false;   // Stops the AI dotted animation
      } else if (needsReview) {
        stroke = '#ef4444'; // Needs Review = Bright Red
        strokeWidth = 2;
      }

      return {
        ...edge,
        animated,
        style: { ...edge.style, stroke, strokeWidth, opacity: isDimmed ? 0.1 : 1, transition: 'all 0.3s' },
        markerEnd: { ...edge.markerEnd, color: stroke }
      };
    }));
  }, [showHighRisk, verifiedEdges]);

  const handleVerifyEdge = (edgeId) => {
    setVerifiedEdges(prev => {
      const newSet = new Set(prev);
      if (newSet.has(edgeId)) newSet.delete(edgeId);
      else newSet.add(edgeId);
      return newSet;
    });
  };

  const handleGenerate = async () => { 
    setIsGenerating(true); setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/generate`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to generate lineage');
      handleLoadGraph();
    } catch (err) { setError(err.message); } 
    finally { setIsGenerating(false); }
  };

  const handleLoadGraph = async () => { 
    setIsLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/lineage`);
      if (!response.ok) throw new Error('No lineage data exists. Please run the AI generation first.');
      const data = await response.json();
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(data);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setSelectedEdge(null); 
      setVerifiedEdges(new Set()); 
      setShowHighRisk(false);
    } catch (err) { setError(err.message); } 
    finally { setIsLoading(false); }
  };

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  const onEdgeClick = (event, edge) => {
    setSelectedEdge(edge);
  };

  const onPaneClick = () => {
    setSelectedEdge(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'sans-serif', overflow: 'hidden' }}>
      
      <header style={{ padding: '1rem 2rem', backgroundColor: '#1e293b', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold', letterSpacing: '-0.5px' }}>
          LineageGuard<span style={{ color: '#10b981' }}>.ai</span>
        </h1>
        <div style={{ display: 'flex', gap: '1rem' }}>
          
          {nodes.length > 0 && (
            <button 
              onClick={() => setShowHighRisk(!showHighRisk)} 
              style={{ padding: '0.5rem 1rem', cursor: 'pointer', backgroundColor: showHighRisk ? '#ef4444' : '#475569', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}
            >
              {showHighRisk ? 'Show Full Pipeline' : '🔍 Isolate High-Risk Paths'}
            </button>
          )}

          <button onClick={handleGenerate} disabled={isGenerating} style={{ padding: '0.5rem 1rem', cursor: isGenerating ? 'wait' : 'pointer', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}>
            {isGenerating ? 'AI is Processing...' : '1. Run Lineage Generation'}
          </button>
          <button onClick={handleLoadGraph} disabled={isLoading} style={{ padding: '0.5rem 1rem', cursor: isLoading ? 'wait' : 'pointer', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px' }}>
            {isLoading ? 'Loading...' : '2. Load Lineage Graph'}
          </button>
        </div>
      </header>

      <main style={{ flexGrow: 1, position: 'relative', backgroundColor: '#f8fafc', display: 'flex' }}>
        
        {nodes.length === 0 && (
          <div style={{ 
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, 
            display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', 
            backgroundColor: '#f8fafc', zIndex: 50, padding: '20px', textAlign: 'center' 
          }}>
            <div style={{ backgroundColor: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', border: '1px solid #cbd5e1', maxWidth: '500px' }}>
              <h2 style={{ margin: '0 0 10px 0', color: '#1e293b', fontSize: '24px' }}>
                {error ? 'No Data Found' : 'Ready to Map Your Pipeline'}
              </h2>
              <p style={{ margin: '0 0 20px 0', color: '#64748b', lineHeight: '1.5', alignContent: 'left' }}>
                {error 
                  ? "No lineage data exists in the cache. Please click 'Run Lineage Generation' to have the AI analyze your codebase."
                  : (
                    <>
                      Welcome to LineageGuard.ai <br />
                      Click '1. Run Lineage Generation' to parse your codebase, <br />
                      or '2. Load Lineage Graph' if you already have cached data.
                    </>
                  )
                }
              </p>
              {error && (
                <div style={{ backgroundColor: '#fef2f2', color: '#ef4444', padding: '10px', borderRadius: '6px', fontSize: '14px', border: '1px solid #fecaca' }}>
                  Backend says: {error}
                </div>
              )}
            </div>
          </div>
        )}

        <div style={{ flexGrow: 1, position: 'relative', visibility: nodes.length > 0 ? 'visible' : 'hidden' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick} 
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            onMove={(event, viewport) => setZoomLevel(viewport.zoom)}
          >
            <Background color="#ccc" gap={16} />
            <Controls />
            
            {zoomLevel >= 0.6 && (
              <MiniMap 
                position="top-right"
                nodeColor={(node) => {
                  const rawType = (node.data?.node_type || 'default').toLowerCase();
                  return NODE_COLORS[rawType] || NODE_COLORS.default;
                }}
                nodeStrokeWidth={3}
                zoomable
                pannable
                style={{ height: 80, width: 180, backgroundColor: 'white', border: '1px solid #cbd5e1', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              />
            )}
            
            {nodes.length > 0 && (
              <div style={{ position: 'absolute', bottom: '20px', right: '20px', zIndex: 10, backgroundColor: 'white', padding: '12px 16px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', border: '1px solid #cbd5e1' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#1e293b', fontWeight: 'bold' }}>Node Types</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#334155', fontWeight: '500' }}><span style={{ width: '14px', height: '14px', backgroundColor: NODE_COLORS.source, borderRadius: '3px' }}></span> Source / File</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#334155', fontWeight: '500' }}><span style={{ width: '14px', height: '14px', backgroundColor: NODE_COLORS.table, borderRadius: '3px' }}></span> Table / DB</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#334155', fontWeight: '500' }}><span style={{ width: '14px', height: '14px', backgroundColor: NODE_COLORS.intermediate, borderRadius: '3px' }}></span> DataFrame</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#334155', fontWeight: '500' }}><span style={{ width: '14px', height: '14px', backgroundColor: NODE_COLORS.sink, borderRadius: '3px' }}></span> Sink / Output</div>
                </div>
              </div>
            )}
          </ReactFlow>
        </div>

        {/* --- EXPANDED SIDE PANEL --- */}
        {selectedEdge && (
          <div style={{ 
            width: '380px', backgroundColor: 'white', borderLeft: '1px solid #cbd5e1', 
            boxShadow: '-4px 0 15px rgba(0,0,0,0.05)', padding: '20px', overflowY: 'auto',
            display: 'flex', flexDirection: 'column', gap: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#1e293b' }}>Transformation Details</h3>
              <button onClick={() => setSelectedEdge(null)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#64748b' }}>✕</button>
            </div>

            {/* CONDITIONAL HUMAN VERIFICATION UI */}
            {(selectedEdge.data.confidence || 0) >= 0.85 ? (
              <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#334155' }}>✅ Auto-Verified by AI</h4>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  Confidence is high ({((selectedEdge.data.confidence || 0) * 100).toFixed(0)}%). No human review required.
                </span>
              </div>
            ) : (
              <div style={{ 
                backgroundColor: verifiedEdges.has(selectedEdge.id) ? '#d1fae5' : '#fef2f2', 
                padding: '12px', borderRadius: '6px', 
                border: `1px solid ${verifiedEdges.has(selectedEdge.id) ? '#34d399' : '#fca5a5'}`, 
                display: 'flex', justifyContent: 'space-between', alignItems: 'center' 
              }}>
                 <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '13px', color: verifiedEdges.has(selectedEdge.id) ? '#065f46' : '#991b1b' }}>
                      ⚠️ Verification Required
                    </h4>
                    <span style={{ fontSize: '12px', color: verifiedEdges.has(selectedEdge.id) ? '#059669' : '#ef4444' }}>
                      {verifiedEdges.has(selectedEdge.id) ? 'Verified and locked for production.' : 'Low confidence. Please review.'}
                    </span>
                 </div>
                 <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={verifiedEdges.has(selectedEdge.id)}
                        onChange={() => handleVerifyEdge(selectedEdge.id)}
                        style={{ width: '22px', height: '22px', cursor: 'pointer', accentColor: '#10b981' }}
                    />
                 </label>
              </div>
            )}

            {/* SOURCE FILE PATH */}
            {selectedEdge.data.source_file && (
              <div>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Source File</h4>
                <div style={{ backgroundColor: '#f8fafc', padding: '8px 12px', borderRadius: '4px', border: '1px solid #e2e8f0', fontFamily: 'monospace', fontSize: '12px', color: '#334155', wordBreak: 'break-all' }}>
                  📄 {selectedEdge.data.source_file}
                </div>
              </div>
            )}

            <div>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>AI Explanation</h4>
              <p style={{ margin: 0, fontSize: '14px', color: '#334155', lineHeight: '1.5' }}>
                {selectedEdge.data.explanation || "No explanation provided."}
              </p>
            </div>

            {selectedEdge.data.transformation && (
              <div>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Code Snippet</h4>
                <pre style={{ margin: 0, backgroundColor: '#1e293b', color: '#4ade80', padding: '12px', borderRadius: '6px', fontSize: '12px', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>
                  {selectedEdge.data.transformation}
                </pre>
              </div>
            )}

            <div>
               <h4 style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>AI Confidence</h4>
               <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ flexGrow: 1, height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(selectedEdge.data.confidence || 0) * 100}%`, backgroundColor: (selectedEdge.data.confidence || 0) >= 0.85 ? '#10b981' : '#ef4444' }}></div>
                  </div>
                  <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#1e293b' }}>
                    {((selectedEdge.data.confidence || 0) * 100).toFixed(0)}%
                  </span>
               </div>
            </div>
          </div>
        )}

      </main>
      
      <footer style={{ padding: '0.75rem', backgroundColor: '#1e293b', color: '#94a3b8', textAlign: 'center', fontSize: '0.875rem' }}>
        Made with ❤️ by Hardik Ajmani. 2026
      </footer>
    </div>
  );
}