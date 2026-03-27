import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

/**
 * Force-directed network graph using D3.js
 * Nodes sized by trust score, links colored by connection strength,
 * jobs shown as animated particles flowing between nodes.
 */
const NetworkGraph = ({ agentState }) => {
  const svgRef = useRef(null);
  const simulationRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  useEffect(() => {
    const handleResize = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: Math.max(500, container.clientHeight),
        });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !agentState) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Build graph data
    const selfNode = {
      id: agentState.node_id || 'self',
      name: agentState.node_name || agentState.node_id?.substring(0, 8) || 'Self',
      trust: agentState.trust_score || 0.5,
      isSelf: true,
      capabilities: agentState.capabilities || [],
      balance: agentState.wallet?.balance || 0,
      jobsCompleted: agentState.jobs_completed || 0,
      quarantined: agentState.quarantined || false,
    };

    const peers = (agentState.peer_list || []).map((p) => ({
      id: p.node_id || `peer-${Math.random().toString(36).slice(2, 8)}`,
      name: p.node_id?.substring(0, 10) || 'Unknown',
      trust: p.trust_score ?? 0.5,
      isSelf: false,
      capabilities: p.capabilities || [],
      connected: p.connected !== false,
      quarantined: p.quarantined || false,
      rtt: p.rtt || null,
      ip: p.ip || '',
    }));

    const nodes = [selfNode, ...peers];
    const links = peers.map((p) => ({
      source: selfNode.id,
      target: p.id,
      connected: p.connected,
      rtt: p.rtt,
    }));

    // Defs for gradients and filters
    const defs = svg.append('defs');

    // Glow filter
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const merge = filter.append('feMerge');
    merge.append('feMergeNode').attr('in', 'coloredBlur');
    merge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Background
    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', '#0a0a0a')
      .attr('rx', 8);

    // Grid pattern
    const gridSize = 40;
    for (let x = 0; x < width; x += gridSize) {
      svg.append('line')
        .attr('x1', x).attr('y1', 0).attr('x2', x).attr('y2', height)
        .attr('stroke', '#111').attr('stroke-width', 0.5);
    }
    for (let y = 0; y < height; y += gridSize) {
      svg.append('line')
        .attr('x1', 0).attr('y1', y).attr('x2', width).attr('y2', y)
        .attr('stroke', '#111').attr('stroke-width', 0.5);
    }

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d) => d.id).distance(150).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d) => nodeRadius(d) + 10))
      .force('x', d3.forceX(width / 2).strength(0.05))
      .force('y', d3.forceY(height / 2).strength(0.05));

    simulationRef.current = simulation;

    // Links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', (d) => d.connected ? '#2ecc71' : '#e74c3c')
      .attr('stroke-width', (d) => d.connected ? 2 : 1)
      .attr('stroke-opacity', (d) => d.connected ? 0.6 : 0.2)
      .attr('stroke-dasharray', (d) => d.connected ? 'none' : '5,5');

    // Animated particles on links (representing data flow)
    const particles = svg.append('g');
    links.forEach((l, i) => {
      if (!l.connected) return;
      const particle = particles.append('circle')
        .attr('r', 3)
        .attr('fill', '#3498db')
        .attr('opacity', 0.8)
        .attr('filter', 'url(#glow)');

      function animateParticle() {
        particle
          .attr('cx', () => {
            const s = typeof l.source === 'object' ? l.source : nodes.find(n => n.id === l.source);
            return s?.x || 0;
          })
          .attr('cy', () => {
            const s = typeof l.source === 'object' ? l.source : nodes.find(n => n.id === l.source);
            return s?.y || 0;
          })
          .transition()
          .duration(2000 + Math.random() * 2000)
          .delay(Math.random() * 3000)
          .attr('cx', () => {
            const t = typeof l.target === 'object' ? l.target : nodes.find(n => n.id === l.target);
            return t?.x || 0;
          })
          .attr('cy', () => {
            const t = typeof l.target === 'object' ? l.target : nodes.find(n => n.id === l.target);
            return t?.y || 0;
          })
          .on('end', animateParticle);
      }
      animateParticle();
    });

    // Node groups
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Node circles
    node.append('circle')
      .attr('r', (d) => nodeRadius(d))
      .attr('fill', (d) => {
        if (d.quarantined) return '#e74c3c';
        if (d.isSelf) return '#1a1a2e';
        if (!d.connected) return '#1a1a1a';
        return '#0d1117';
      })
      .attr('stroke', (d) => {
        if (d.quarantined) return '#ff6b6b';
        if (d.isSelf) return '#3498db';
        if (!d.connected) return '#555';
        return trustColor(d.trust);
      })
      .attr('stroke-width', (d) => d.isSelf ? 3 : 2)
      .attr('filter', (d) => d.isSelf ? 'url(#glow)' : 'none');

    // Trust ring (arc showing trust level)
    node.each(function(d) {
      const g = d3.select(this);
      const r = nodeRadius(d) + 4;
      const arc = d3.arc()
        .innerRadius(r)
        .outerRadius(r + 3)
        .startAngle(0)
        .endAngle(d.trust * 2 * Math.PI);
      g.append('path')
        .attr('d', arc)
        .attr('fill', trustColor(d.trust))
        .attr('opacity', 0.8);
    });

    // Node labels
    node.append('text')
      .text((d) => d.isSelf ? 'YOU' : d.name?.substring(0, 8))
      .attr('text-anchor', 'middle')
      .attr('dy', -2)
      .attr('fill', (d) => d.isSelf ? '#3498db' : '#ccc')
      .attr('font-size', (d) => d.isSelf ? '11px' : '9px')
      .attr('font-weight', (d) => d.isSelf ? 'bold' : 'normal')
      .attr('font-family', 'monospace');

    // Trust score label
    node.append('text')
      .text((d) => `${(d.trust * 100).toFixed(0)}%`)
      .attr('text-anchor', 'middle')
      .attr('dy', 12)
      .attr('fill', (d) => trustColor(d.trust))
      .attr('font-size', '10px')
      .attr('font-family', 'monospace');

    // Capability icons
    node.append('text')
      .text((d) => {
        const caps = d.capabilities || [];
        if (caps.length === 0) return '';
        if (caps.length <= 3) return caps.length + ' caps';
        return caps.length + ' caps';
      })
      .attr('text-anchor', 'middle')
      .attr('dy', 24)
      .attr('fill', '#666')
      .attr('font-size', '8px')
      .attr('font-family', 'monospace');

    // Tooltips
    node.append('title')
      .text((d) => {
        let t = `${d.name || d.id}\nTrust: ${(d.trust * 100).toFixed(1)}%`;
        if (d.isSelf) t += `\nBalance: ${d.balance?.toFixed(1)} AC\nJobs: ${d.jobsCompleted}`;
        if (d.capabilities?.length) t += `\nCaps: ${d.capabilities.join(', ')}`;
        if (d.rtt) t += `\nRTT: ${d.rtt.toFixed(0)}ms`;
        if (d.quarantined) t += '\n⚠ QUARANTINED';
        return t;
      });

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('transform', (d) => {
        d.x = Math.max(40, Math.min(width - 40, d.x));
        d.y = Math.max(40, Math.min(height - 40, d.y));
        return `translate(${d.x},${d.y})`;
      });
    });

    return () => {
      simulation.stop();
    };
  }, [agentState, dimensions]);

  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  const peers = agentState.peer_list || [];
  const connectedPeers = peers.filter((p) => p.connected !== false);

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Network Topology</h2>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Total Peers</div>
          <div className="text-2xl font-bold text-white">{agentState.peers || 0}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Connected</div>
          <div className="text-2xl font-bold text-green-400">{connectedPeers.length}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Trust Score</div>
          <div className="text-2xl font-bold text-blue-400">
            {((agentState.trust_score || 0) * 100).toFixed(0)}%
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Capabilities</div>
          <div className="text-2xl font-bold text-purple-400">
            {(agentState.capabilities || []).length}
          </div>
        </div>
      </div>

      {/* D3 Force Graph */}
      <div className="bg-black border border-gray-800 rounded overflow-hidden" style={{ minHeight: '500px' }}>
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          style={{ display: 'block' }}
        />
      </div>

      {/* Legend */}
      <div className="flex gap-6 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full border-2 border-blue-400 bg-blue-900"></div>
          <span>This Node</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full border-2 border-green-400 bg-green-900"></div>
          <span>Connected Peer</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full border-2 border-red-400 bg-red-900"></div>
          <span>Quarantined</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-400"></div>
          <span>Data Flow</span>
        </div>
        <div className="flex items-center gap-2">
          <span>Ring = Trust Level</span>
        </div>
      </div>
    </div>
  );
};

// Helper: node radius based on trust
function nodeRadius(d) {
  if (d.isSelf) return 30;
  const base = 18;
  const trustBonus = (d.trust || 0.5) * 12;
  return base + trustBonus;
}

// Helper: color from trust score
function trustColor(trust) {
  if (trust >= 0.8) return '#2ecc71';
  if (trust >= 0.6) return '#27ae60';
  if (trust >= 0.4) return '#f39c12';
  if (trust >= 0.2) return '#e67e22';
  return '#e74c3c';
}

export default NetworkGraph;
