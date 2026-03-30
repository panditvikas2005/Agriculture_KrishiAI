import { useState } from 'react'

const TAG_COLORS = {
  Fertilizer: 'chip-lime',
  Monitor:    'chip-sky',
  Pest:       'chip-rose',
  Irrigation: 'chip-teal',
  Market:     'chip-amber',
}

const INITIAL_TASKS = [
  { id:1, date:'Mar 10', name:'Apply DAP fertilizer',  field:'Field A – Wheat', tag:'Fertilizer', done:false },
  { id:2, date:'Mar 10', name:'Soil moisture check',   field:'All fields',      tag:'Monitor',    done:true  },
  { id:3, date:'Mar 12', name:'Pesticide spray',       field:'Field B – Onion', tag:'Pest',       done:false },
  { id:4, date:'Mar 14', name:'Irrigation schedule',   field:'Field C',         tag:'Irrigation', done:false },
  { id:5, date:'Mar 18', name:'Market visit Nashik',   field:'Tomato ready',    tag:'Market',     done:false },
]

export default function FarmCalendar() {
  const [tasks,   setTasks]   = useState(INITIAL_TASKS)
  const [newTask, setNewTask] = useState('')

  const toggle = id => setTasks(ts => ts.map(t => t.id === id ? { ...t, done: !t.done } : t))

  const add = () => {
    if (!newTask.trim()) return
    setTasks(ts => [...ts, { id: Date.now(), date:'New', name: newTask.trim(), field:'—', tag:'Monitor', done:false }])
    setNewTask('')
  }

  return (
    <div className="page">
      <h1 className="page-head">📅 Farm Calendar</h1>
      <p className="page-sub">Farming tasks track karo</p>

      <div style={{maxWidth:700}}>
        {tasks.map(t => (
          <div key={t.id} style={{display:'flex',alignItems:'flex-start',gap:14,padding:'14px 0',borderBottom:'1px solid rgba(255,255,255,.05)'}}>
            <button
              onClick={() => toggle(t.id)}
              style={{width:22,height:22,borderRadius:6,marginTop:2,flexShrink:0,background:t.done?'var(--lime)':'rgba(255,255,255,.06)',border:`2px solid ${t.done?'var(--lime)':'rgba(255,255,255,.2)'}`,cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',transition:'all .15s'}}
            >
              {t.done && <span style={{fontSize:12,color:'#0a1a00',fontWeight:700}}>✓</span>}
            </button>

            <div style={{flex:1,opacity:t.done ? 0.5 : 1}}>
              <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
                <span style={{fontWeight:600,fontSize:14,textDecoration:t.done?'line-through':'none'}}>{t.name}</span>
                <span className={`chip ${TAG_COLORS[t.tag] || 'chip-sky'}`}>{t.tag}</span>
              </div>
              <div style={{fontSize:12,color:'var(--text3)',marginTop:4}}>📍 {t.field} · 📅 {t.date}</div>
            </div>
          </div>
        ))}

        <div style={{display:'flex',gap:10,marginTop:20}}>
          <input
            className="input"
            style={{flex:1}}
            placeholder="Nayi task… (Enter)"
            value={newTask}
            onChange={e => setNewTask(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && add()}
          />
          <button onClick={add} className="btn btn-primary">+ Add</button>
        </div>
      </div>
    </div>
  )
}
