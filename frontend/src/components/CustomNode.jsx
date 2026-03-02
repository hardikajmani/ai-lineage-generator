import { Handle, Position } from '@xyflow/react';
import { useState } from 'react';

export default function CustomNode({ data }) {
  // State to track if the mouse is hovering over the node
  const [isHovered, setIsHovered] = useState(false);

  // Determine border color based on risk or node type
  const getBorderColor = () => {
    if (data.is_high_risk) return 'border-color: #ef4444;'; // Red for high risk
    return 'border-color: #cbd5e1;'; // Default gray
  };

  return (
    <div 
      style={{ position: 'relative' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* --- FLOATING TOOLTIP --- */}
      {isHovered && (
        <div style={{
          position: 'absolute',
          bottom: '100%', // Position exactly above the node
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: '10px', // Space between tooltip and node
          backgroundColor: '#1e293b',
          color: 'white',
          padding: '10px',
          borderRadius: '6px',
          fontSize: '12px',
          width: 'max-content',
          maxWidth: '280px', // Prevent it from getting too wide
          zIndex: 1000,
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
          pointerEvents: 'none', // Prevents mouse flickering
          textAlign: 'left'
        }}>
          {data.is_high_risk && (
            <div style={{ color: '#ef4444', fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              ⚠️ HIGH RISK TARGET
            </div>
          )}
          <div style={{ lineHeight: '1.4', color: '#cbd5e1' }}>
            {data.description || "No AI description provided for this node."}
          </div>
          
          {/* Little downward pointing triangle for the tooltip tail */}
          <div style={{
            position: 'absolute',
            bottom: '-4px',
            left: '50%',
            transform: 'translateX(-50%) rotate(45deg)',
            width: '8px',
            height: '8px',
            backgroundColor: '#1e293b'
          }} />
        </div>
      )}

      {/* --- MAIN NODE BOX --- */}
      <div style={{ 
        padding: '10px 15px', 
        borderRadius: '8px', 
        backgroundColor: 'white', 
        border: `2px solid ${data.is_high_risk ? '#ef4444' : '#cbd5e1'}`,
        boxShadow: data.is_high_risk ? '0 0 10px rgba(239, 68, 68, 0.4)' : '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        width: '200px',
        transition: 'all 0.2s ease',
        cursor: 'default'
      }}>
        <Handle type="target" position={Position.Left} style={{ background: '#555' }} />
        
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
             <span style={{ fontWeight: 'bold', fontSize: '12px', color: '#1e293b', wordBreak: 'break-all' }}>
              {data.label}
            </span>
            {data.is_high_risk && <span style={{ fontSize: '12px' }}>⚠️</span>}
          </div>
         
          <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginTop: '4px' }}>
            {data.node_type}
          </span>
        </div>

        <Handle type="source" position={Position.Right} style={{ background: '#555' }} />
      </div>
    </div>
  );
}