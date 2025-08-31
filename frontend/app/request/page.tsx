'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

type Ticket = { id: string; title: string; status: 'new' | 'progress' | 'resolved' | 'closed' };

export default function HomePage() {
  const router = useRouter();

  const [formData, setFormData] = useState({ email: '', requestTitle: '', description: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [tickets] = useState<Ticket[]>([
    { id: 'TKT-2024-001', title: 'Suspicious network activity detected', status: 'new' },
    { id: 'TKT-2024-002', title: 'Malware signature update required', status: 'progress' },
    { id: 'TKT-2024-003', title: 'Firewall configuration review', status: 'resolved' },
    { id: 'TKT-2024-004', title: 'User access audit completed', status: 'closed' },
  ]);

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

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employeeEmail: formData.email,
          title: formData.requestTitle,
          description: formData.description,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setFormData({ email: '', requestTitle: '', description: '' });
    } catch (err: any) {
      alert('Submit failed: ' + err.message);
    } finally { setIsSubmitting(false); }
  }

  const goToTickets = () => router.push('/tickets');
  const viewTicket = (id: string) => router.push(`/tickets/${id}`);
  const pillClass = (s: Ticket['status']) =>
    s === 'new' ? 'pill info' : s === 'progress' ? 'pill warn' : s === 'resolved' ? 'pill success' : 'pill muted';
  const pillText = (s: Ticket['status']) => (s === 'progress' ? 'IN PROGRESS' : s.toUpperCase());

  return (
    <div className="home-page">
      <div id="particles" className="particles" />

      <div className="container">
        <div className="page-header">
          <div className="header-content">
            <h1 className="page-title">Welcome, Have Any IT Probmlem?</h1>
            <p className="page-subtitle">Your IT Support Website</p>
            <p className="page-tagline">Chimera: Cybersecurity that <span className="tag-strong">speaks your language</span></p>
          </div>
        </div>

        <div className="main-grid">
          <section className="panel">
            <h2 className="section-title"><span className="bullet">◆</span> Submit your request</h2>

            {/* FORM */}
            <form onSubmit={handleSubmit} className="form">
              <div className="row">
                <div className="group">
                  <label>Email</label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="you@company.com"
                  />
                </div>
                <div className="group">
                  <label>Title</label>
                  <input
                    id="requestTitle"
                    name="requestTitle"
                    required
                    value={formData.requestTitle}
                    onChange={handleInputChange}
                    placeholder="Brief description"
                  />
                </div>
              </div>

              <div className="group">
                <label>Description</label>
                <textarea
                  id="description"
                  name="description"
                  required
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Describe your issue, steps to reproduce, error messages…"
                />
              </div>

              {/*  Submit button */}
              <button
                type="submit"
                className="primary-btn"
                aria-busy={isSubmitting}
                disabled={
                  isSubmitting ||
                  !formData.email ||
                  !formData.requestTitle ||
                  !formData.description
                }
              >
                {isSubmitting ? 'Submitting…' : 'Submit Security Request'}
              </button>
            </form>
          </section>

          <aside className="panel">
            <div className="tickets-head">
              <h2 className="section-title"><span className="bullet">◆</span> Your Tickets</h2>
              <button className="ghost-btn" onClick={goToTickets}>Open full list</button>
            </div>
            <div className="tickets-list">
              {tickets.map(t => (
                <div key={t.id} className="ticket-card" onClick={() => viewTicket(t.id)}>
                  <div className="ticket-top">
                    <div className="ticket-id">#{t.id}</div>
                    <span className={pillClass(t.status)}>{pillText(t.status)}</span>
                  </div>
                  <div className="ticket-title">{t.title}</div>
                </div>
              ))}
            </div>
          </aside>
        </div>
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

        .main-grid{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:2rem;align-items:start}

        .panel{background:#0b0b0b;border:1px solid var(--cyan);border-radius:15px;padding:1rem;box-shadow:0 8px 28px -18px rgba(0,229,168,.35)}
        .section-title{display:flex;align-items:center;gap:.6rem;color:var(--cyan);margin-bottom:1rem;font-weight:800}
        .bullet{font-size:.75rem}

        .ghost-btn{display:inline-flex;align-items:center;justify-content:center;padding:.55rem .9rem;border-radius:10px;background:#000;color:#fff;border:1px solid var(--cyan)}
        .ghost-btn:hover{box-shadow:0 0 0 2px rgba(0,229,168,.35)}

        .form{display:grid;gap:1rem}
        .row{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
        .group{display:flex;flex-direction:column;gap:.4rem}
        label{color:var(--cyan);font-size:.9rem}
        input,textarea{background:#000;border:1px solid var(--cyan);border-radius:10px;color:#fff;padding:.9rem 1rem}
        textarea{min-height:120px;resize:vertical}
        input:focus,textarea:focus{outline:none;box-shadow:0 0 0 2px rgba(0,229,168,.35)}

.primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  width: 100%;
  height: 48px;
  border-radius: 12px;
  border: 1px solid var(--cyan);
  font-weight: 800;
  cursor: pointer;
  transition: box-shadow .15s ease, transform .15s ease;
  box-shadow: 0 6px 18px -8px rgba(0,229,168,.35);

  /* ✅ default (enabled) look */
  background: #333;
  color: #0ff5d4;
}

.primary-btn:hover:not(:disabled) {
  box-shadow: 0 8px 22px -6px rgba(0,229,168,.45);
  transform: translateY(-1px);
}

/* ✅ disabled style */
.primary-btn:disabled {
  opacity: 1;
  background: #333;
  color: #0ff5d4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

        .tickets-head{display:flex;align-items:center;justify-content:space-between}
        .tickets-list{display:grid;gap:1rem;margin-top:.75rem}
        .ticket-card{background:#0b0b0b;border:1px solid var(--cyan);border-radius:12px;padding:1rem;cursor:pointer;transition:.2s}
        .ticket-card:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(0,229,168,.25)}
        .ticket-top{display:flex;justify-content:space-between;margin-bottom:.4rem}
        .ticket-id{color:var(--cyan);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem}
        .ticket-title{color:#fff;font-weight:600}

        .pill{display:inline-block;padding:.24rem .6rem;border-radius:999px;font-size:.7rem;font-weight:900;text-transform:uppercase}
        .pill.info{background:#00F5D4;color:#00110c}
        .pill.warn{background:#ff9800;color:#00110c}
        .pill.success{background:#4caf50;color:#00110c}
        .pill.muted{background:#777;color:#fff}

        .footer{margin-top:24px;padding:16px 24px;text-align:center;color:var(--cyan);border-top:1px solid var(--cyan);background:#000}

        .particles{position:fixed;inset:0;pointer-events:none;z-index:-1}
        :global(.particle){position:absolute;width:3px;height:3px;background:#00E5A8;border-radius:50%;opacity:.35;animation:float 6s infinite ease-in-out}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-16px)}}
        @media(max-width:1024px){.page-header{flex-direction:column;text-align:center}.main-grid{grid-template-columns:1fr}.row{grid-template-columns:1fr}}
      `}</style>
    </div>
  );
}
