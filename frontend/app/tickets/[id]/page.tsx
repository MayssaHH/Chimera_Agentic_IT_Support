'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

type Severity = 'debug' | 'info' | 'warn' | 'error' | 'critical';
type Log = { id: string; ts: string; source: string; message: string; severity: Severity };

const SEVERITIES: Severity[] = ['debug', 'info', 'warn', 'error', 'critical'];

function nowIso() { return new Date().toISOString(); }

function generateMockLogs(n = 120): Log[] {
  const sources = ['gateway', 'ids', 'firewall', 'endpoint-17', 'proxy', 'scanner', 'auth'];
  const msgs = [
    'Connection accepted','JWT token expired','Port scan detected on WAN','Policy matched: BLOCK outbound SMTP',
    'Malware hash flagged by YARA rule','Anomalous DNS query pattern','User login failed 3 times',
    'TLS handshake error','Signature updated successfully','Process terminated by EDR',
  ];
  const weights: Record<Severity, number> = { debug: 32, info: 38, warn: 16, error: 9, critical: 5 };
  const pick = () => {
    const total = Object.values(weights).reduce((a,b)=>a+b,0);
    let r = Math.random()*total;
    for (const s of SEVERITIES){ r -= weights[s]; if (r<=0) return s; }
    return 'info';
  };
  const arr: Log[] = [];
  for (let i=0; i<n; i++){
    const d = new Date(Date.now() - Math.random()*86_400_000);
    arr.push({
      id: `LOG-${(100000 + Math.floor(Math.random()*900000)).toString()}`,
      ts: d.toISOString(),
      source: sources[Math.floor(Math.random()*sources.length)],
      message: msgs[Math.floor(Math.random()*msgs.length)],
      severity: pick(),
    });
  }
  return arr.sort((a,b)=>(a.ts<b.ts?1:-1));
}

export default function LogsPage() {
  const router = useRouter();

  const [logs, setLogs] = useState<Log[]>(() => generateMockLogs());
  const [search, setSearch] = useState('');
  const [sev, setSev] = useState<Severity | 'all'>('all');
  const [range, setRange] = useState<'15m' | '1h' | '24h' | 'all'>('1h');
  const [live, setLive] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  useEffect(() => {
    if (!live) return;
    const iv = setInterval(() => {
      const sources = ['gateway','ids','firewall','endpoint-17','proxy','scanner','auth'];
      const msgs = [
        'Flow anomaly detected','Suspicious URL blocked','Privilege escalation attempt',
        'EDR quarantine success','DNS over HTTPS fallback','Lateral movement blocked','Brute-force throttled',
      ];
      const sevPick: Severity[] = ['debug','info','warn','error','critical'];
      const item: Log = {
        id: `LOG-${(100000 + Math.floor(Math.random()*900000)).toString()}`,
        ts: nowIso(),
        source: sources[Math.floor(Math.random()*sources.length)],
        message: msgs[Math.floor(Math.random()*msgs.length)],
        severity: sevPick[Math.floor(Math.random()*sevPick.length)],
      };
      setLogs(prev => [item, ...prev].slice(0, 1000));
    }, 2500);
    return () => clearInterval(iv);
  }, [live]);

  const filtered = useMemo(() => {
    const end = new Date();
    const start =
      range === '15m' ? new Date(end.getTime() - 15*60*1000) :
      range === '1h'  ? new Date(end.getTime() - 60*60*1000) :
      range === '24h' ? new Date(end.getTime() - 24*60*60*1000) :
      new Date(0);
    const q = search.trim().toLowerCase();
    return logs.filter(l => {
      const t = new Date(l.ts);
      if (t < start || t > end) return false;
      if (sev !== 'all' && l.severity !== sev) return false;
      if (!q) return true;
      return l.id.toLowerCase().includes(q)
          || l.source.toLowerCase().includes(q)
          || l.message.toLowerCase().includes(q)
          || l.severity.toLowerCase().includes(q);
    });
  }, [logs, search, sev, range]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  useEffect(() => setPage(1), [search, sev, range]);
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);

  function exportCsv() {
    const rows = [['id','timestamp','source','severity','message']]
      .concat(filtered.map(l => [l.id, l.ts, l.source, l.severity, l.message.replace(/\n/g,' ')]));
    const csv = rows.map(r => r.map(x => `"${String(x).replace(/"/g,'""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url;
    a.download = `chimera_logs_${new Date().toISOString().replace(/[:.]/g,'-')}.csv`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  return (
    <div className="logs-page">
      <div id="particles" className="particles" />

      <div className="container">
        <div className="page-header">
          <div className="header-content">
            <h1 className="page-title">Ticket's Logs</h1>
            <p className="page-subtitle">Unified view of events across gateways, IDS/IPS, EDR, and apps</p>
            <p className="page-tagline">Real-time telemetry with <span className="tag-strong">precision filtering</span></p>
          </div>
          <div className="header-actions">
            <button className="ghost-btn" onClick={() => router.push('/tickets')}>Open Tickets →</button>
            <button className="ghost-btn" onClick={() => router.push('/request')}>Back to Request</button>
          </div>
        </div>

        <section className="panel controls">
          <div className="controls-grid">
            <input className="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search id, source, message, severity…" />
            <select className="select" value={sev} onChange={(e) => setSev(e.target.value as any)}>
              <option value="all">All severities</option>
              {SEVERITIES.map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
            </select>
            <select className="select" value={range} onChange={(e) => setRange(e.target.value as any)}>
              <option value="15m">Last 15m</option><option value="1h">Last 1h</option>
              <option value="24h">Last 24h</option><option value="all">All time</option>
            </select>
            <button className="ghost-btn" onClick={() => { setSearch(''); setSev('all'); setRange('1h'); }}>Reset</button>
            <button className="ghost-btn" onClick={exportCsv}>Export CSV</button>
            <label className="live-toggle">
              <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
              <span className={`dot ${live ? 'on' : 'off'}`} /> Live tail
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="table-head">
            <div className="count">{filtered.length.toLocaleString()} events</div>
            <div className="pages">
              <button className="ghost-btn" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</button>
              <span className="page-indicator">Page {page} / {totalPages}</span>
              <button className="ghost-btn" disabled={page === totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>Next</button>
            </div>
          </div>

          <div className="table-wrap">
            <table className="log-table">
              <thead><tr><th>Timestamp</th><th>ID</th><th>Source</th><th>Severity</th><th>Message</th></tr></thead>
              <tbody>
                {pageItems.map(row => (
                  <tr key={row.id} className={`sev-${row.severity}`}>
                    <td className="mono">{new Date(row.ts).toLocaleString()}</td>
                    <td className="mono">{row.id}</td>
                    <td>{row.source}</td>
                    <td><span className={`pill ${row.severity}`}>{row.severity.toUpperCase()}</span></td>
                    <td className="msg">{row.message}</td>
                  </tr>
                ))}
                {pageItems.length === 0 && <tr><td colSpan={5} className="empty">No events match your filters.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <footer className="footer">© 2025 Chimera Security, Inc. All rights reserved.</footer>

      <style jsx global>{`html,body{background:#000!important;color:#fff}`}</style>
      <style jsx>{`
        :root { --cyan:#00E5A8; --cyan2:#5EF1FF; }

        .container{max-width:1400px;margin:0 auto;padding:2rem}
        .page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;gap:1rem;flex-wrap:wrap}
        .page-title{font-size:2.2rem;margin-bottom:.3rem;color:var(--cyan)}
        .page-subtitle{color:#7beed8;font-size:1.05rem;opacity:.7}
        .page-tagline{color:var(--cyan);margin-top:.2rem}
        .tag-strong{font-weight:800}

        .panel{background:#0b0b0b;border:1px solid var(--cyan);border-radius:15px;padding:1rem;box-shadow:0 8px 28px -18px rgba(0,229,168,.35)}
        .ghost-btn{display:inline-flex;align-items:center;justify-content:center;padding:.55rem .9rem;border-radius:10px;background:#000;color:#fff;border:1px solid var(--cyan)}
        .ghost-btn:hover{box-shadow:0 0 0 2px rgba(0,229,168,.35)}

        .controls-grid{display:grid;grid-template-columns:1.5fr .8fr .8fr auto auto auto;gap:.8rem}
        .search,.select{background:#000;border:1px solid var(--cyan);border-radius:10px;color:#fff;padding:.8rem 1rem}
        .live-toggle{display:flex;align-items:center;gap:.6rem;font-weight:600}
        .dot{width:10px;height:10px;border-radius:999px;display:inline-block;border:1px solid var(--cyan)}
        .dot.on{background:#00e5a8}.dot.off{background:#222}

        .table-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:.6rem}
        .count{color:#7beed8}.page-indicator{margin:0 .6rem;opacity:.85}

        .table-wrap{border:1px solid var(--cyan);border-radius:12px;overflow:hidden}
        .log-table{width:100%;border-collapse:separate;border-spacing:0}
        thead th{position:sticky;top:0;background:#001311;border-bottom:1px solid var(--cyan);padding:.7rem .8rem;text-align:left;font-weight:800;color:var(--cyan)}
        tbody td{padding:.6rem .8rem;border-bottom:1px solid rgba(0,229,168,.15)}
        tbody tr:hover{background:#061a16}
        .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.92rem;color:#b8fff0}
        .msg{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:0}
        .empty{text-align:center;padding:2rem;color:#7beed8}

        .pill{display:inline-block;padding:.24rem .6rem;border-radius:999px;font-size:.7rem;font-weight:900;text-transform:uppercase}
        .pill.debug{background:#6b7280;color:#fff}
        .pill.info{background:#00F5D4;color:#00110c}
        .pill.warn{background:#ff9800;color:#00110c}
        .pill.error{background:#ef4444;color:#fff}
        .pill.critical{background:#c026d3;color:#fff}

        .footer{margin-top:24px;padding:16px 24px;text-align:center;color:var(--cyan);border-top:1px solid var(--cyan);background:#000}

        .particles{position:fixed;inset:0;pointer-events:none;z-index:-1}
        :global(.particle){position:absolute;width:3px;height:3px;background:#00E5A8;border-radius:50%;opacity:.35;animation:float 6s infinite ease-in-out}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-16px)}}

        @media(max-width:1024px){
          .controls-grid{grid-template-columns:1fr 1fr 1fr 1fr;gap:.6rem}
          .header-actions{width:100%;justify-content:center}
        }
      `}</style>
    </div>
  );
}
