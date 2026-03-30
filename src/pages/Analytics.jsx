import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { Metric } from '../components/UI.jsx'

const yieldData = [
  {m:'Aug',Wheat:28,Onion:0, Tomato:12},
  {m:'Sep',Wheat:31,Onion:8, Tomato:18},
  {m:'Oct',Wheat:35,Onion:22,Tomato:24},
  {m:'Nov',Wheat:40,Onion:30,Tomato:20},
  {m:'Dec',Wheat:38,Onion:35,Tomato:16},
  {m:'Jan',Wheat:44,Onion:40,Tomato:22},
  {m:'Feb',Wheat:48,Onion:42,Tomato:28},
]

const revenueData = [
  {m:'Aug',Revenue:42,Cost:18},
  {m:'Sep',Revenue:55,Cost:20},
  {m:'Oct',Revenue:68,Cost:25},
  {m:'Nov',Revenue:75,Cost:22},
  {m:'Dec',Revenue:70,Cost:24},
  {m:'Jan',Revenue:82,Cost:26},
  {m:'Feb',Revenue:90,Cost:28},
]

const tooltipStyle = { background:'#0d1419', border:'1px solid rgba(255,255,255,.1)', borderRadius:10, color:'#e4edf4' }
const axisProps    = { tick:{fill:'#4a6070',fontSize:11}, axisLine:false, tickLine:false }

export default function Analytics() {
  return (
    <div className="page">
      <h1 className="page-head">📊 Analytics</h1>
      <p className="page-sub">Farm performance overview</p>

      <div className="grid-4" style={{marginBottom:28}}>
        <Metric label="Total Revenue" value="₹6.2L" delta="18%"  deltaType="up"/>
        <Metric label="Total Cost"    value="₹1.4L"/>
        <Metric label="Net Profit"    value="₹4.8L" delta="24%"  deltaType="up"/>
        <Metric label="ROI"           value="342%"  delta="19%"  deltaType="up"/>
      </div>

      <div className="grid-2">
        <div className="card">
          <div style={{fontWeight:600,fontSize:14,marginBottom:16}}>📈 Yield Trends (q/acre)</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={yieldData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)"/>
              <XAxis dataKey="m" {...axisProps}/>
              <YAxis {...axisProps}/>
              <Tooltip contentStyle={tooltipStyle}/>
              <Line type="monotone" dataKey="Wheat"  stroke="#aaff44" strokeWidth={2} dot={false}/>
              <Line type="monotone" dataKey="Onion"  stroke="#ffb547" strokeWidth={2} dot={false}/>
              <Line type="monotone" dataKey="Tomato" stroke="#ff6b6b" strokeWidth={2} dot={false}/>
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div style={{fontWeight:600,fontSize:14,marginBottom:16}}>💸 Revenue vs Cost (₹K)</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revenueData}>
              <defs>
                <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#aaff44" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#aaff44" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ff6b6b" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#ff6b6b" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)"/>
              <XAxis dataKey="m" {...axisProps}/>
              <YAxis {...axisProps}/>
              <Tooltip contentStyle={tooltipStyle}/>
              <Area type="monotone" dataKey="Revenue" stroke="#aaff44" strokeWidth={2} fill="url(#rg)"/>
              <Area type="monotone" dataKey="Cost"    stroke="#ff6b6b" strokeWidth={2} fill="url(#cg)"/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
