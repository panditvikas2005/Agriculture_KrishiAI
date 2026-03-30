import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { LANGS } from '../hooks/useLang.js'
import { Aurora, Spinner, Alert } from '../components/UI.jsx'

export default function LoginPage() {
  const { login, register, user } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab]       = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  // Login fields
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [pw,    setPw]    = useState('')

  // Register fields
  const [rName,  setRName]  = useState('')
  const [rEmail, setREmail] = useState('')
  const [rPhone, setRPhone] = useState('')
  const [rPw,    setRPw]    = useState('')
  const [rLoc,   setRLoc]   = useState('')
  const [rLangs, setRLangs] = useState({ hi: true, mr: true })

  if (user) return <Navigate to="/dashboard" replace/>

  const doLogin = async e => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const p = { password: pw }
      if (email.trim()) p.email = email.trim()
      if (phone.trim()) p.phone = phone.trim()
      await login(p)
      navigate('/dashboard')
    } catch(err) { setError(err.message) }
    setLoading(false)
  }

  const doRegister = async e => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const langs = Object.entries(rLangs).filter(([,v]) => v).map(([k]) => k)
      await register({
        name: rName.trim(),
        email: rEmail.trim() || undefined,
        phone: rPhone.trim() || undefined,
        password: rPw,
        location: rLoc.trim() || undefined,
        languages: langs
      })
      sessionStorage.removeItem('welcomed')
      navigate('/dashboard')
    } catch(err) { setError(err.message) }
    setLoading(false)
  }

  return (
    <div style={{minHeight:'100vh',background:'#070b0e',display:'flex',alignItems:'center',justifyContent:'center',padding:20,position:'relative',overflow:'hidden'}}>
      <Aurora/>
      <div style={{width:'100%',maxWidth:440,background:'rgba(13,20,25,.9)',border:'1px solid rgba(255,255,255,.08)',borderRadius:28,padding:40,backdropFilter:'blur(20px)',position:'relative',zIndex:1,boxShadow:'0 32px 80px rgba(0,0,0,.5)',animation:'fadeUp .5s cubic-bezier(.25,.46,.45,.94) both'}}>
        <div style={{textAlign:'center',marginBottom:32}}>
          <div style={{width:72,height:72,borderRadius:22,margin:'0 auto 14px',background:'linear-gradient(135deg,#aaff44,#55aa00)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:36,boxShadow:'0 8px 32px rgba(170,255,68,.35)'}}>🌿</div>
          <div style={{fontFamily:'Syne,sans-serif',fontSize:30,fontWeight:800,color:'#aaff44'}}>KrishiAI</div>
          <div style={{fontSize:13,color:'#4a6070',marginTop:4}}>Smart farming powered by AI</div>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6,background:'rgba(255,255,255,.04)',borderRadius:12,padding:5,marginBottom:28}}>
          {[['login','🔑 Login'],['register','🌱 Register']].map(([t,l]) => (
            <button key={t} onClick={() => { setTab(t); setError('') }}
              style={{padding:'10px 0',borderRadius:9,border:'none',cursor:'pointer',fontSize:13,fontWeight:600,transition:'all .2s',background:tab===t?'linear-gradient(135deg,#aaff44,#66cc00)':'transparent',color:tab===t?'#0a1a00':'#8fa3b1'}}
            >{l}</button>
          ))}
        </div>

        {error && <Alert type="error" onClose={() => setError('')}>{error}</Alert>}

        {tab === 'login' ? (
          <form onSubmit={doLogin} style={{display:'flex',flexDirection:'column',gap:14}}>
            <div><label className="input-label">📧 Email</label><input className="input" type="email" placeholder="your@email.com" value={email} onChange={e => setEmail(e.target.value)}/></div>
            <div><label className="input-label">📱 Phone</label><input className="input" type="tel" placeholder="9876543210" value={phone} onChange={e => setPhone(e.target.value)}/></div>
            <div><label className="input-label">🔒 Password</label><input className="input" type="password" placeholder="••••••••" value={pw} onChange={e => setPw(e.target.value)} required/></div>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{marginTop:8}}>
              {loading ? <Spinner size={18}/> : 'Login →'}
            </button>
          </form>
        ) : (
          <form onSubmit={doRegister} style={{display:'flex',flexDirection:'column',gap:14}}>
            <div><label className="input-label">👤 Full Name *</label><input className="input" placeholder="Ramesh Kumar" value={rName} onChange={e => setRName(e.target.value)} required/></div>
            <div className="grid-2">
              <div><label className="input-label">📧 Email</label><input className="input" type="email" placeholder="email" value={rEmail} onChange={e => setREmail(e.target.value)}/></div>
              <div><label className="input-label">📱 Phone</label><input className="input" type="tel" placeholder="phone" value={rPhone} onChange={e => setRPhone(e.target.value)}/></div>
            </div>
            <div><label className="input-label">🔒 Password *</label><input className="input" type="password" placeholder="min 6 chars" value={rPw} onChange={e => setRPw(e.target.value)} required minLength={6}/></div>
            <div><label className="input-label">📍 Location</label><input className="input" placeholder="Pune, Maharashtra" value={rLoc} onChange={e => setRLoc(e.target.value)}/></div>
            <div>
              <label className="input-label" style={{marginBottom:8}}>🌐 Languages</label>
              <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:6}}>
                {Object.entries(LANGS).map(([code, name]) => {
                  const locked  = code === 'hi' || code === 'mr'
                  const checked = rLangs[code] || locked
                  return (
                    <label key={code} style={{display:'flex',flexDirection:'column',alignItems:'center',padding:'8px 4px',borderRadius:8,cursor:locked?'default':'pointer',background:checked?'rgba(170,255,68,.08)':'rgba(255,255,255,.03)',border:`1px solid ${checked?'rgba(170,255,68,.2)':'rgba(255,255,255,.06)'}`,transition:'all .15s'}}>
                      <input type="checkbox" checked={checked} disabled={locked} onChange={e => setRLangs(p => ({...p,[code]:e.target.checked}))} style={{display:'none'}}/>
                      <span style={{fontSize:14,fontWeight:600,color:checked?'#aaff44':'#4a6070'}}>{code.toUpperCase()}</span>
                      <span style={{fontSize:9,color:'#4a6070',marginTop:2,textAlign:'center',lineHeight:1.2}}>{name}</span>
                    </label>
                  )
                })}
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{marginTop:8}}>
              {loading ? <Spinner size={18}/> : 'Create Account →'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
