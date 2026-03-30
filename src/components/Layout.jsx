import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useLang, LANGS } from '../hooks/useLang.js'
import { Aurora, WelcomeBanner } from './UI.jsx'
import Sidebar from './Sidebar.jsx'

import Dashboard    from '../pages/Dashboard.jsx'
import Chat         from '../pages/Chat.jsx'
import Disease      from '../pages/Disease.jsx'
import VoicePage    from '../pages/VoicePage.jsx'
import Market       from '../pages/Market.jsx'
import Schemes      from '../pages/Schemes.jsx'
import Soil         from '../pages/Soil.jsx'
import Irrigation   from '../pages/Irrigation.jsx'
import Planner      from '../pages/Planner.jsx'
import Predict      from '../pages/Predict.jsx'
import Profit       from '../pages/Profit.jsx'
import Analytics    from '../pages/Analytics.jsx'
import FarmCalendar from '../pages/FarmCalendar.jsx'

export default function Layout() {
  const { user } = useAuth()
  const [sideOpen, setSideOpen]   = useState(false)
  const [showWelcome, setWelcome] = useState(() => !sessionStorage.getItem('welcomed'))
  const [lang, changeLang]        = useLang()

  useEffect(() => {
    if (showWelcome) sessionStorage.setItem('welcomed', '1')
  }, [showWelcome])

  if (!user) return <Navigate to="/login" replace />

  return (
    <>
      <Aurora/>
      {showWelcome && <WelcomeBanner name={user.name} onDone={() => setWelcome(false)}/>}
      <Sidebar open={sideOpen} onClose={() => setSideOpen(false)}/>

      <div style={{marginLeft:240,minHeight:'100vh',position:'relative',zIndex:1}} className="main-content">
        {/* Topbar */}
        <div style={{position:'sticky',top:0,zIndex:30,background:'rgba(7,11,14,.85)',backdropFilter:'blur(16px)',borderBottom:'1px solid rgba(255,255,255,.05)',padding:'12px 24px',display:'flex',alignItems:'center',gap:12}}>
          <button onClick={() => setSideOpen(true)} className="btn btn-ghost btn-sm" style={{padding:8}}>
            <Menu size={18}/>
          </button>
          <div style={{flex:1}}/>
          <select
            value={lang}
            onChange={e => changeLang(e.target.value)}
            className="input"
            style={{width:'auto',fontSize:13,padding:'6px 32px 6px 12px'}}
          >
            {Object.entries(LANGS).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </div>

        {/* Page content */}
        <div style={{padding:'28px',maxWidth:1280,margin:'0 auto'}}>
          <Routes>
            <Route path="/dashboard"  element={<Dashboard    lang={lang}/>}/>
            <Route path="/chat"       element={<Chat         lang={lang}/>}/>
            <Route path="/disease"    element={<Disease      lang={lang}/>}/>
            <Route path="/voice"      element={<VoicePage    lang={lang}/>}/>
            <Route path="/market"     element={<Market/>}/>
            <Route path="/schemes"    element={<Schemes      lang={lang}/>}/>
            <Route path="/soil"       element={<Soil         lang={lang}/>}/>
            <Route path="/irrigation" element={<Irrigation   lang={lang}/>}/>
            <Route path="/planner"    element={<Planner      lang={lang}/>}/>
            <Route path="/predict"    element={<Predict      lang={lang}/>}/>
            <Route path="/profit"     element={<Profit       lang={lang}/>}/>
            <Route path="/analytics"  element={<Analytics/>}/>
            <Route path="/calendar"   element={<FarmCalendar/>}/>
            <Route path="*"           element={<Navigate to="/dashboard"/>}/>
          </Routes>
        </div>
      </div>
    </>
  )
}
