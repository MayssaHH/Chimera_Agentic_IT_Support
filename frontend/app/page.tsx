'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();

    // accept anything (demo)
    const displayName = name.trim() || email.split('@')[0] || 'User';

    // save & cookie
    localStorage.setItem('chimera_name', displayName);
    document.cookie = `chimera_user=${encodeURIComponent(displayName)}; path=/; max-age=31536000`;

    // 🔥 trigger listeners (NavBar) to update immediately
    window.dispatchEvent(new Event('storage'));

    // go to the form page
    router.replace('/request');
  }

  return (
    <div className="auth">
      <div className="box">
        <h1 className="title">Chimera IT Supporter</h1>

        <form onSubmit={handleLogin} className="form">
          <label>Display name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Your name"
            required
          />

          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Your password"
            required
          />

          <button type="submit" className="primary-btn">Log in</button>
        </form>
      </div>

      <style jsx global>{`html,body{background:#000!important;color:#fff}`}</style>
      <style jsx>{`
        :root { --cyan:#00E5A8; --cyan2:#5EF1FF; }
        .auth{min-height:100vh;display:grid;place-items:center}
        .box{
          width:100%;max-width:420px;background:#0b0b0b;border:1px solid var(--cyan);
          border-radius:14px;padding:1.25rem;box-shadow:0 8px 28px -18px rgba(0,229,168,.35)
        }
        .title{color:var(--cyan);text-align:center;margin:0 0 1rem}
        .form{display:grid;gap:.7rem}
        label{color:#7beed8;font-size:.85rem}
        input{
          background:#000;border:1px solid var(--cyan);border-radius:10px;color:#fff;padding:.8rem 1rem
        }
        input:focus{outline:none;box-shadow:0 0 0 2px rgba(0,229,168,.35)}
        .primary-btn{
          margin-top:.8rem;display:inline-flex;align-items:center;justify-content:center;height:46px;width:100%;
          border-radius:12px;background:linear-gradient(90deg,var(--cyan),var(--cyan2));
          color:#0ff5d4;border:1px solid var(--cyan);font-weight:800;cursor:pointer
        }
      `}</style>
    </div>
  );
}
