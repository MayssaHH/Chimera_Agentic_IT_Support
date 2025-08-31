'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import NavBar from '@/app/components/NavBar';

export default function AuthPage() {
  const router = useRouter();
  const [name, setName] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('chimera_name');
    if (saved) setName(saved);
  }, []);

  function save(e: React.FormEvent) {
    e.preventDefault();
    const n = name.trim() || 'Administrator';
    localStorage.setItem('chimera_name', n);
    router.push('/'); // go back to SOC
  }

  return (
    <div className="auth-page">
      <NavBar disableHomeNav />

      <div className="wrap">
        <div className="card">
          <h1 className="title">Sign in / Set your display name</h1>
          <p className="sub">This name appears in the navbar (replacing “Administrator”).</p>

          <form onSubmit={save} className="form">
            <label htmlFor="name">Display name</label>
            <input
              id="name"
              value={name}
              onChange={(e)=>setName(e.target.value)}
              placeholder="e.g., Zeinab, Mariam, Bazzi…"
              autoFocus
            />
            <button className="primary-btn">Save & Go to SOC</button>
            <button className="ghost-btn" type="button" onClick={()=>router.push('/')}>Cancel</button>
          </form>
        </div>
      </div>

      <style jsx global>{`html,body{background:#000!important;color:#fff}`}</style>
      <style jsx>{`
        :root { --cyan:#00E5A8; --cyan2:#5EF1FF; }

        .auth-page{min-height:100vh;display:flex;flex-direction:column}
        .wrap{flex:1;display:flex;align-items:center;justify-content:center;padding:2rem}
        .card{width:100%;max-width:520px;background:#0b0b0b;border:1px solid var(--cyan);border-radius:16px;padding:1.5rem;box-shadow:0 8px 28px -18px rgba(0,229,168,.35)}
        .title{color:var(--cyan);margin:0 0 .5rem 0}
        .sub{opacity:.8;margin:0 0 1rem 0}
        .form{display:grid;gap:.8rem}
        label{color:var(--cyan)}
        input{background:#000;border:1px solid var(--cyan);border-radius:10px;color:#fff;padding:.9rem 1rem}
        input:focus{outline:none;box-shadow:0 0 0 2px rgba(0,229,168,.35)}
        .primary-btn{display:inline-flex;align-items:center;justify-content:center;width:100%;height:44px;border-radius:12px;background:linear-gradient(90deg,var(--cyan),var(--cyan2));color:#00110c;border:1px solid var(--cyan);font-weight:800;cursor:pointer;transition:box-shadow .15s ease,transform .15s ease}
        .primary-btn:hover{box-shadow:0 8px 22px -6px rgba(0,229,168,.45);transform:translateY(-1px)}
        .ghost-btn{margin-top:.4rem;display:inline-flex;align-items:center;justify-content:center;width:100%;height:44px;border-radius:12px;background:#000;color:#fff;border:1px solid var(--cyan)}
        .ghost-btn:hover{box-shadow:0 0 0 2px rgba(0,229,168,.35)}
      `}</style>
    </div>
  );
}
