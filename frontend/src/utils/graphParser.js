import dagre from 'dagre';

export const getLayoutedElements = (lineageData, direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 250;
  const nodeHeight = 80;

  // Force Left-to-Right and spacing
  dagreGraph.setGraph({ 
    rankdir: direction, 
    ranksep: 200,       
    nodesep: 50,        
  });

  const initialNodes = lineageData.nodes.map((node) => {
    dagreGraph.setNode(node.node_id, { width: nodeWidth, height: nodeHeight });
    return {
      id: node.node_id,
      type: 'customNode',
      data: { 
        label: node.node_id,
        node_type: node.node_type,
        description: node.description,
      },
      position: { x: 0, y: 0 },
    };
  });

  const initialEdges = lineageData.edges.map((edge) => {
    // THIS IS THE MAGIC LINE WE MISSED! Tell Dagre the edge exists:
    dagreGraph.setEdge(edge.source, edge.target);

    return {
      id: edge.edge_id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep', 
      animated: edge.status === 'AI_SUGGESTED',
      style: { stroke: '#64748b', strokeWidth: 2 },
      data: { explanation: edge.explanation }
    };
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = initialNodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };
    return node;
  });

  return { nodes: layoutedNodes, edges: initialEdges };
};