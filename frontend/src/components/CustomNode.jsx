import { Handle, Position } from '@xyflow/react';
import { useState } from 'react';

// Define our standard border/text palette
export const NODE_COLORS = {
  source: '#10b981', // Emerald Green
  file: '#10b981',
  table: '#3b82f6', // Blue
  database: '#3b82f6',
  intermediate: '#8b5cf6', // Purple
  dataframe: '#8b5cf6',
  sink: '#f97316', // Orange
  output: '#f97316',
  default: '#64748b' // Slate Gray
};

// Define light backgrounds specifically for endpoints
export const NODE_BGS = {
  source: 'rgba(16, 185, 129, 0.1)', // 10% opacity Green
  file: 'rgba(16, 185, 129, 0.1)',
  sink: 'rgba(249, 115, 22, 0.1)',   // 10% opacity Orange
  output: 'rgba(249, 115, 22, 0.1)',
  // Middle nodes stay white so the graph isn't overwhelming
  table: '#ffffff',
  database: '#ffffff',
  intermediate: '#ffffff',
  dataframe: '#ffffff',
  default: '#ffffff'
};

export default function CustomNode({ data }) {
  const [isHovered, setIsHovered] = useState(false);
  
  const rawType = (data.node_type || 'default').toLowerCase();
  const themeColor = NODE_COLORS[rawType] || NODE_COLORS.default;
  const bgColor = NODE_BGS[rawType] || '#ffffff';
  const borderColor = data.is_high_risk ? '#ef4444' : themeColor;

  return (
    <div 
      style={{ position: 'relative' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Hover Tooltip */}
      {isHovered && (
        <div style={{
          position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)',
          marginBottom: '10px', backgroundColor: '#1e293b', color: 'white', padding: '10px',
          borderRadius: '6px', fontSize: '12px', width: 'max-content', maxWidth: '280px',
          zIndex: 1000, boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)', pointerEvents: 'none'
        }}>
          {data.is_high_risk && (
            <div style={{ color: '#ef4444', fontWeight: 'bold', marginBottom: '4px' }}>⚠️ HIGH RISK TARGET</div>
          )}
          <div style={{ color: '#cbd5e1' }}>{data.description || "No description provided."}</div>
        </div>
      )}

      {/* Main Node Box */}
      <div style={{ 
        padding: '10px 15px', 
        borderRadius: '8px', 
        backgroundColor: bgColor, // <-- Applies the tinted background!
        border: `2px solid ${borderColor}`, 
        boxShadow: data.is_high_risk ? '0 0 10px rgba(239, 68, 68, 0.4)' : '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        width: '200px',
        cursor: 'default'
      }}>
        <Handle type="target" position={Position.Left} style={{ background: themeColor, width: '8px', height: '8px' }} />
        
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
             <span style={{ fontWeight: 'bold', fontSize: '12px', color: '#1e293b', wordBreak: 'break-all' }}>
              {data.label}
            </span>
            {data.is_high_risk && <span style={{ fontSize: '12px' }}>⚠️</span>}
          </div>
          <span style={{ fontSize: '10px', color: themeColor, fontWeight: 'bold', textTransform: 'uppercase', marginTop: '4px' }}>
            {data.node_type}
          </span>
        </div>

        <Handle type="source" position={Position.Right} style={{ background: themeColor, width: '8px', height: '8px' }} />
      </div>
    </div>
  );
}