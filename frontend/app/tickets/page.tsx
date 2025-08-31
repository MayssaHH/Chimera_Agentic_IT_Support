'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

type Ticket = {
  id: string; title: string; description: string;
  status: 'new' | 'progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string; updatedAt: string; assignee: string; category: string;
};

export default function TicketsPage() {
  const router = useRouter();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [filteredTickets, setFilteredTickets] = useState<Ticket[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | Ticket['status']>('all');

  useEffect(() => {
    const mock: Ticket[] = [
      { id: 'TKT-2024-001', title: 'Suspicious network activity detected', description: 'Multiple failed login attempts from IP 192.168.1.100', status: 'new', priority: 'high', createdAt: '2024-08-30T10:30:00Z', updatedAt: '2024-08-30T10:30:00Z', assignee: 'John Smith', category: 'Security Incident' },
      { id: 'TKT-2024-002', title: 'Malware signature update required', description: 'Antivirus definitions need updating across all endpoints', status: 'progress', priority: 'medium', createdAt: '2024-08-29T14:15:00Z', updatedAt: '2024-08-30T09:00:00Z', assignee: 'Sarah Johnson', category: 'Maintenance' },
      { id: 'TKT-2024-003', title: 'Firewall configuration review', description: 'Quarterly review of firewall rules and access policies', status: 'resolved', priority: 'low', createdAt: '2024-08-28T08:00:00Z', updatedAt: '2024-08-29T16:30:00Z', assignee: 'Mike Wilson', category: 'Review' },
      { id: 'TKT-2024-004', title: 'User access audit completed', description: 'Monthly user access rights audit and cleanup', status: 'closed', priority: 'medium', createdAt: '2024-08-27T11:20:00Z', updatedAt: '2024-08-28T17:45:00Z', assignee: 'Lisa Chen', category: 'Audit' },
      { id: 'TKT-2024-005', title: 'DDoS attack mitigation', description: 'Large scale DDoS attack targeting main servers', status: 'new', priority: 'critical', createdAt: '2024-08-30T15:45:00Z', updatedAt: '2024-08-30T15:45:00Z', assignee: 'David Brown', category: 'Security Incident' },
      { id: 'TKT-2024-006', title: 'SSL certificate renewal', description: 'SSL certificates expiring next month for main domain', status: 'progress', priority: 'medium', createdAt: '2024-08-26T13:10:00Z', updatedAt: '2024-08-30T08:30:00Z', assignee: 'Emma Davis', category: 'Maintenance' },
    ];
    setTickets(mock); setFilteredTickets(mock);
  }, []);

  useEffect(() => {
    let filtered = [...tickets];
    if (statusFilter !== 'all') filtered = filtered.filter(t => t.status === statusFilter);
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      filtered = filtered.filter(t =>
        t.id.toLowerCase().includes(q) ||
        t.title.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
      );
    }
    setFilteredTickets(filtered);
  }, [tickets, statusFilter, searchTerm]);

  const getStatusClass = (s: Ticket['status']) =>
    s === 'new' ? 'pill info' : s === 'progress' ? 'pill warn' : s === 'resolved' ? 'pill success' : 'pill muted';
  const getStatusText = (s: Ticket['status']) => (s === 'progress' ? 'IN PROGRESS' : s.toUpperCase());
  const getPriorityClass = (p: Ticket['priority']) =>
    p === 'low' ? 'prio low' : p === 'medium' ? 'prio med' : p === 'high' ? 'prio high' : 'prio critical';
  const formatDate = (d: string) => new Date(d).toLocaleString();
  const viewTicket = (id: string) => router.push(`/tickets/${id}`);
  const goHome = () => router.push('/');

  useEffect(() => {
    const el = document.getElementById('particles'); if (!el) return;
    el.innerHTML = '';
    for (let i = 0; i < 16; i++) {
      const p = document.createElement('div');
      p.className = 'particle';
      p.style.left = Math.random()*100 + '%';
      p.style.top = Math.random()*100 + '%';
      p.style.animationDelay = Math.random()*6 + 's';
      p.style.animationDuration = 4 + Math.random()*3 + 's';
      el.appendChild(p);
    }
  }, []);

  return (
    <div className="tickets-page">
      <div id="particles" className="particles" />

      <div className="container">
        <div className="page-header">
          <div className="header-content">
            <h1 className="page-title">Support Tickets</h1>
            <p className="page-subtitle">Manage and track all security incidents and requests</p>
            <p className="page-tagline">Fast triage with <span className="tag-strong">clear signals</span></p>
          </div>
          <div className="header-actions">
            <button className="ghost-btn" onClick={goHome}>← Back to SOC</button>
          </div>
        </div>

        <section className="panel controls">
          <div className="controls-grid">
            <input
              type="text"
              className="search"
              placeholder="Search by ID, title, or description…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
            >
              <option value="all">All ({tickets.length})</option>
              <option value="new">New ({tickets.filter(t => t.status === 'new').length})</option>
              <option value="progress">In Progress ({tickets.filter(t => t.status === 'progress').length})</option>
              <option value="resolved">Resolved ({tickets.filter(t => t.status === 'resolved').length})</option>
              <option value="closed">Closed ({tickets.filter(t => t.status === 'closed').length})</option>
            </select>
            <button className="ghost-btn" onClick={() => { setSearchTerm(''); setStatusFilter('all'); }}>Reset</button>
          </div>
        </section>

        <section className="grid">
          {filteredTickets.length === 0 ? (
            <div className="panel empty-state">
              <div className="no-tickets-icon">🔍</div>
              <h3>No tickets found</h3>
              <p>Try adjusting your search or filters</p>
            </div>
          ) : (
            filteredTickets.map(ticket => (
              <div key={ticket.id} className="panel ticket-card" onClick={() => viewTicket(ticket.id)}>
                <div className="ticket-top">
                  <div className="ticket-id mono">#{ticket.id}</div>
                  <div className="badges">
                    <span className={getStatusClass(ticket.status)}>{getStatusText(ticket.status)}</span>
                    <span className={getPriorityClass(ticket.priority)}>{ticket.priority.toUpperCase()}</span>
                  </div>
                </div>

                <div className="ticket-title">{ticket.title}</div>
                <p className="ticket-desc">{ticket.description}</p>

                <div className="meta">
                  <div><span className="label">Category:</span> {ticket.category}</div>
                  <div><span className="label">Assignee:</span> {ticket.assignee}</div>
                  <div><span className="label">Created:</span> {formatDate(ticket.createdAt)}</div>
                  <div><span className="label">Updated:</span> {formatDate(ticket.updatedAt)}</div>
                </div>

                <button className="primary-btn">View Details & Logs</button>
              </div>
            ))
          )}
        </section>
      </div>

      <footer className="footer">© 2025 Chimera Security, Inc. All rights reserved.</footer>

      <style jsx global>{`html,body{background:#000!important;color:#fff}`}</style>
      <style jsx>{`
        :root { --cyan:#00E5A8; --cyan2:#5EF1FF; }

        .tickets-page{min-height:100vh;display:flex;flex-direction:column}
        .container{max-width:1400px;margin:0 auto;padding:2rem;flex:1}

        .page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem;gap:1rem;flex-wrap:wrap}
        .page-title{font-size:2.2rem;margin-bottom:.3rem;color:var(--cyan)}
        .page-subtitle{color:#7beed8;font-size:1.05rem;opacity:.7}
        .page-tagline{color:var(--cyan);margin-top:.2rem}
        .tag-strong{font-weight:800}
        .header-actions{display:flex;gap:.6rem}
        .ghost-btn{display:inline-flex;align-items:center;justify-content:center;padding:.55rem .9rem;border-radius:10px;background:#000;color:#fff;border:1px solid var(--cyan)}
        .ghost-btn:hover{box-shadow:0 0 0 2px rgba(0,229,168,.35)}

        .panel{background:#0b0b0b;border:1px solid var(--cyan);border-radius:15px;padding:1rem;box-shadow:0 8px 28px -18px rgba(0,229,168,.35)}
        .controls .controls-grid{display:grid;grid-template-columns:1.5fr .8fr auto;gap:.8rem}
        .search,.select{background:#000;border:1px solid var(--cyan);border-radius:10px;color:#fff;padding:.8rem 1rem}

        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:1.2rem}
        .ticket-card{cursor:pointer;transition:.2s}
        .ticket-card:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(0,229,168,.25)}
        .ticket-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.6rem}
        .ticket-id{color:var(--cyan);font-size:.9rem}
        .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
        .badges{display:flex;gap:.5rem;flex-wrap:wrap}
        .ticket-title{color:#fff;font-weight:700;margin-bottom:.35rem}
        .ticket-desc{color:#cfeee6;margin-bottom:.8rem;opacity:.9}

        .meta{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:.9rem}
        .label{color:#7beed8;font-size:.78rem;margin-right:.3rem}

        .primary-btn{display:inline-flex;align-items:center;justify-content:center;width:100%;height:44px;border-radius:12px;background:linear-gradient(90deg,var(--cyan),var(--cyan2));color:#00110c;border:1px solid var(--cyan);font-weight:800;cursor:pointer;transition:box-shadow .15s ease,transform .15s ease}
        .primary-btn:hover{box-shadow:0 8px 22px -6px rgba(0,229,168,.45);transform:translateY(-1px)}

        .pill{display:inline-block;padding:.24rem .6rem;border-radius:999px;font-size:.7rem;font-weight:900;text-transform:uppercase}
        .pill.info{background:#00F5D4;color:#00110c}
        .pill.warn{background:#ff9800;color:#00110c}
        .pill.success{background:#4caf50;color:#00110c}
        .pill.muted{background:#777;color:#fff}

        .prio{display:inline-block;padding:.24rem .6rem;border-radius:999px;font-size:.7rem;font-weight:900;border:1px solid transparent}
        .prio.low{background:rgba(50,205,50,.15);color:#32cd32;border-color:#32cd32}
        .prio.med{background:rgba(255,165,0,.15);color:#ffa500;border-color:#ffa500}
        .prio.high{background:rgba(255,69,0,.15);color:#ff4500;border-color:#ff4500}
        .prio.critical{background:rgba(255,0,0,.15);color:#ff0000;border-color:#ff0000;animation:pulse 2s infinite}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.7}}

        .footer{margin-top:auto;padding:16px 24px;text-align:center;color:var(--cyan);border-top:1px solid var(--cyan);background:#000}

        .particles{position:fixed;inset:0;pointer-events:none;z-index:-1}
        :global(.particle){position:absolute;width:3px;height:3px;background:#00E5A8;border-radius:50%;opacity:.35;animation:float 6s infinite ease-in-out}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-16px)}}

        @media(max-width:1024px){
          .controls .controls-grid{grid-template-columns:1fr 1fr auto}
          .meta{grid-template-columns:1fr}
          .page-header{flex-direction:column;text-align:center}
          .header-actions{width:100%;justify-content:center}
        }
      `}</style>
    </div>
  );
}
