import { Handle, Position } from '@xyflow/react';

export default function CustomNode({ data }) {
  return (
    <div style={{ 
      padding: '10px 15px', 
      borderRadius: '8px', 
      backgroundColor: 'white', 
      border: '2px solid #cbd5e1',
      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      width: '200px'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#555' }} />
      
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontWeight: 'bold', fontSize: '12px', color: '#1e293b', wordBreak: 'break-all' }}>
          {data.label}
        </span>
        <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginTop: '4px' }}>
          {data.node_type}
        </span>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: '#555' }} />
    </div>
  );
}