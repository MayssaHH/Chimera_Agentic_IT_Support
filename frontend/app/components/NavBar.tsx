'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

type Props = {
  role?: string;
  titleText?: string;
  disableHomeNav?: boolean;
};

export default function NavBar({
  role = 'Administrator',
  titleText = 'Chimera Cybersecurity',
  disableHomeNav = false,
}: Props) {
  const router = useRouter();
  const [username, setUsername] = useState('Administrator');

  useEffect(() => {
    const saved = localStorage.getItem('chimera_name');
    if (saved) setUsername(saved);
  }, []);
  useEffect(() => {
    localStorage.setItem('chimera_name', username);
  }, [username]);

  const goHome = () => { if (!disableHomeNav) router.push('/'); };

  return (
    <nav className="soc-nav">
      <div className={`soc-logo ${disableHomeNav ? 'soc-logo--disabled' : ''}`} onClick={goHome}>
        <Image src="/chimera.png" alt="Chimera Logo" width={40} height={40} className="soc-logo-img" />
        {titleText}
      </div>
      <div className="soc-spacer" />
      <div className="soc-right">
        <span className="soc-welcome">Welcome back, <strong>{username}</strong></span>
        {role && <span className="soc-role">{role}</span>}
      </div>

      <style jsx>{`
        :root { --cyan:#00E5A8; }
        .soc-nav{background:#000;border-bottom:1px solid var(--cyan);padding:1rem 2rem;display:flex;align-items:center;gap:1rem;position:sticky;top:0;z-index:100}
        .soc-logo{display:flex;align-items:center;gap:.5rem;font-size:1.5rem;font-weight:800;color:var(--cyan);cursor:pointer}
        .soc-logo--disabled{cursor:default}
        .soc-logo-img{filter:none}
        .soc-spacer{flex:1}
        .soc-right{display:flex;align-items:center;gap:.7rem}
        .soc-welcome{font-size:.95rem;color:#fff;opacity:.9}
        .soc-role{display:inline-block;padding:.24rem .6rem;border-radius:999px;font-size:.72rem;font-weight:900;text-transform:uppercase;background:#061a16;border:1px solid var(--cyan);color:#7beed8}
      `}</style>
    </nav>
  );
}
