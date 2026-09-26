import { StrictMode, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'

const BASE = import.meta.env.BASE_URL
const to = (path = '') => `${BASE}${path}`

const genderRows = [
  ['ha-na', 'female', 'Asia', 'korea', 'female', 'unisex', '0.040', '0.340', '0.620', '0.430', 'incorrect'],
  ['teade', 'male', 'Europe', 'the_netherlands', 'male', 'unisex', '0.300', '0.080', '0.620', '0.430', 'incorrect'],
  ['maialen', 'female', 'Europe', 'spain', 'female', 'female', '0.140', '0.490', '0.370', '0.240', 'correct'],
  ['germain', 'male', 'Europe', 'france, belgium, swiss', 'male', 'male', '0.910', '0.000', '0.090', '0.860', 'correct'],
  ['brayden', 'male', 'North America', 'usa', 'male', 'male', '0.660', '0.000', '0.340', '0.480', 'correct'],
  ['dacian', 'male', 'Europe', 'romania', 'male', 'male', '0.620', '0.010', '0.370', '0.420', 'correct'],
  ['moon-ho', 'male', 'Asia', 'korea', 'male', 'unisex', '0.430', '0.030', '0.540', '0.310', 'incorrect'],
  ['sanjulata', 'female', 'Asia', 'india', 'female', 'female', '0.160', '0.450', '0.390', '0.170', 'correct'],
  ['lide', 'female', 'Europe', 'spain, macedonia', 'female', 'unisex', '0.220', '0.050', '0.730', '0.590', 'incorrect'],
  ['chrissie', 'female', 'Mixed/ambiguous', 'great_britain, usa, the_netherlands', 'female', 'unisex', '0.010', '0.430', '0.560', '0.340', 'incorrect'],
  ['ashley', 'mostly_female', 'Mixed/ambiguous', 'great_britain, ireland, usa', 'female', 'unisex', '0.020', '0.120', '0.860', '0.780', 'incorrect'],
  ['jamie', 'mostly_female', 'Mixed/ambiguous', 'great_britain, ireland, usa, belgium, the_netherlands', 'female', 'unisex', '0.430', '0.030', '0.540', '0.310', 'incorrect'],
]

const regions = [
  ['Europe', '615', '69.6%', '62.1%', '46.7%', '428'],
  ['North America', '400', '59.8%', '65.9%', '39.9%', '239'],
  ['Middle East', '400', '73.0%', '64.7%', '48.4%', '292'],
  ['Asia', '400', '46.5%', '65.4%', '30.5%', '186'],
  ['Mixed / ambiguous', '400', '73.0%', '66.2%', '48.8%', '292'],
]

const routes = [
  { label: 'Camembert → Apollo 13', hops: 4, mode: 'cache-assisted', time: '2.39 seconds', calls: '0 new JEV calls', nodes: ['Camembert', 'France', 'Cold War', 'Apollo program', 'Apollo 13'], images: ['https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dd/Camembert_de_Normandie_%28AOP%29_11.jpg/330px-Camembert_de_Normandie_%28AOP%29_11.jpg', 'https://thumb.wikimedia.org/wikipedia/en/thumb/c/c3/Flag_of_France.svg/330px-Flag_of_France.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dc/NATO_vs._Warsaw_Pact_%281949-1990%29.svg/330px-NATO_vs._Warsaw_Pact_%281949-1990%29.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/0/00/Apollo_program.svg/330px-Apollo_program.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ac/Apollo_13-insignia.png/330px-Apollo_13-insignia.png'] },
  { label: 'Adolf Hitler → Apollo 13', hops: 2, mode: 'JEV-guided', time: '24.25 seconds', calls: '4 JEV calls', nodes: ['Adolf Hitler', 'Apollo 8', 'Apollo 13'], images: ['https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0c/Hitler_portrait_crop_%28cropped%29%282%29.jpg/330px-Hitler_portrait_crop_%28cropped%29%282%29.jpg', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/NASA-Apollo8-Dec24-Earthrise.jpg/330px-NASA-Apollo8-Dec24-Earthrise.jpg', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ac/Apollo_13-insignia.png/330px-Apollo_13-insignia.png'] },
  { label: 'France → Antarctica', hops: 2, mode: 'JEV-guided', time: '2.18 seconds', calls: '4 JEV calls', nodes: ['France', 'Adélie Land', 'Antarctica'], images: ['https://thumb.wikimedia.org/wikipedia/en/thumb/c/c3/Flag_of_France.svg/330px-Flag_of_France.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a7/Flag_of_the_French_Southern_and_Antarctic_Lands.svg/330px-Flag_of_the_French_Southern_and_Antarctic_Lands.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Antarctica_%28orthographic_projection%29.svg/330px-Antarctica_%28orthographic_projection%29.svg.png'] },
  { label: 'Jacques Chirac → Bonnie Blue', hops: 10, mode: 'JEV-guided', time: '88.09 seconds', calls: '17 JEV calls', nodes: ['Jacques Chirac', 'J. Grant Albrecht', 'Grant Albrecht', 'Luge', 'Olympic Games', 'Bermuda', 'American Civil War', 'Flags of the Confederate States of America', 'Bonnie Blue Flag', 'Bonnie Blue (disambiguation)', 'Bonnie Blue'], images: ['https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7b/Jacques_Chirac_%281997%29_%28cropped%29.jpg/330px-Jacques_Chirac_%281997%29_%28cropped%29.jpg', null, null, 'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5a/Mortensen_and_Griffall.jpg/330px-Mortensen_and_Griffall.jpg', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5c/Olympic_rings_without_rims.svg/330px-Olympic_rings_without_rims.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bf/Flag_of_Bermuda.svg/330px-Flag_of_Bermuda.svg.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/69/Battle_of_Gettysburg%2C_by_Currier_and_Ives.png/330px-Battle_of_Gettysburg%2C_by_Currier_and_Ives.png', 'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Flag_of_the_Confederate_States_%281861%E2%80%931863%29.svg/330px-Flag_of_the_Confederate_States_%281861%E2%80%931863%29.svg.png', null, null, 'https://thumb.wikimedia.org/wikipedia/commons/thumb/5/58/Bonnie_Blue%2C_July_2025_%28cropped%29.jpg/330px-Bonnie_Blue%2C_July_2025_%28cropped%29.jpg'] },
  { label: 'Philippe Etchebest → Penile subincision', hops: 4, mode: 'JEV-guided', time: '5.06 seconds', calls: '11 JEV calls', nodes: ['Philippe Etchebest', 'Gordon Ramsay', 'Castration', 'Male genital mutilation', 'Penile subincision'], images: [] },
]

function Mark({ compact = false }) {
  return <img className={compact ? 'h-8 w-8' : 'h-10 w-10'} src={to('logo.svg')} alt="" />
}

function ArrowUpRight() {
  return <span aria-hidden="true" className="text-lg leading-none">↗</span>
}

function Nav() {
  const links = [
    ['Experiments', 'experiments/gender'],
    ['About', 'about'],
  ]
  return (
    <header className="border-b border-white/10 bg-ink/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <a href={to()} className="flex items-center gap-3" aria-label="JEV field notes home">
          <Mark compact />
          <span className="font-display text-sm font-semibold tracking-[0.18em] text-white">JEV / FIELD NOTES</span>
        </a>
        <nav className="flex items-center gap-5 text-sm text-slate-300 sm:gap-8" aria-label="Primary navigation">
          {links.map(([label, path]) => <a key={path} href={to(path)} className="transition hover:text-acid">{label}</a>)}
          <a href="https://docs.typesafe.ai/" target="_blank" rel="noreferrer" className="hidden items-center gap-1 text-acid sm:flex">TypeSafe docs <ArrowUpRight /></a>
        </nav>
      </div>
    </header>
  )
}

function Footer() {
  return <footer className="mt-auto border-t border-white/10 bg-ink px-5 py-6 text-xs text-slate-500 lg:px-8">
    <div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <span>JEV field notes · a small TypeSafe playground</span>
    <span>Built for inspection and curiosity.</span>
    </div>
  </footer>
}

function Shell({ children }) {
  return <div className="flex min-h-screen flex-col bg-ink text-slate-100"><Nav /><main className="flex-1">{children}</main><Footer /></div>
}

function Kicker({ children }) {
  return <p className="mb-4 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-acid">{children}</p>
}

function Stat({ value, label, accent = 'acid' }) {
  return <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5">
    <div className={`font-display text-3xl font-bold ${accent === 'coral' ? 'text-coral' : accent === 'teal' ? 'text-teal' : 'text-acid'}`}>{value}</div>
    <div className="mt-2 text-sm leading-5 text-slate-400">{label}</div>
  </div>
}

function ExperimentCard({ number, title, summary, href, metrics, accent = 'acid' }) {
  return <a href={to(href)} className="group block rounded-3xl border border-white/10 bg-panel p-6 transition duration-300 hover:-translate-y-1 hover:border-acid/50 hover:bg-panel-light sm:p-8">
    <div className="flex items-start justify-between gap-6">
      <span className={`font-mono text-xs font-semibold uppercase tracking-[0.2em] ${accent === 'coral' ? 'text-coral' : 'text-acid'}`}>0{number} / experiment</span>
      <span className="text-xl text-slate-500 transition group-hover:translate-x-1 group-hover:-translate-y-1 group-hover:text-acid">↗</span>
    </div>
    <h2 className="mt-10 max-w-md font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h2>
    <p className="mt-4 max-w-xl text-base leading-7 text-slate-400">{summary}</p>
    <div className="mt-8 grid grid-cols-2 gap-3 border-t border-white/10 pt-5">
      {metrics.map(([value, label]) => <div key={label}><div className="font-display text-lg font-semibold text-white">{value}</div><div className="mt-1 text-xs uppercase tracking-widest text-slate-500">{label}</div></div>)}
    </div>
  </a>
}

function HomePage() {
  return <Shell>
    <section className="grid-paper relative overflow-hidden border-b border-white/10">
      <div className="mx-auto grid max-w-7xl gap-14 px-5 py-20 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:px-8 lg:py-28">
        <div className="relative z-10">
          <Kicker>TypeSafe / JEV / field notes</Kicker>
          <h1 className="max-w-4xl font-display text-5xl font-bold leading-[0.98] tracking-[-0.04em] text-white sm:text-7xl">Small experiments.<br /><span className="text-acid">Inspectable</span> judgment.</h1>
          <p className="mt-8 max-w-2xl text-lg leading-8 text-slate-300">A compact visual record of testing JEV where ordinary code needs a little semantic sense: reading a name, or choosing the next link in a maze of Wikipedia articles.</p>
          <div className="mt-10 flex flex-wrap gap-3">
            <a href={to('experiments/gender')} className="rounded-full bg-acid px-5 py-3 text-sm font-bold text-ink transition hover:bg-white">Explore the benchmarks <span className="ml-2">→</span></a>
            <a href="https://docs.typesafe.ai/" target="_blank" rel="noreferrer" className="rounded-full border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:border-teal hover:text-teal">Read TypeSafe docs <ArrowUpRight /></a>
          </div>
        </div>
        <div className="relative z-10 rounded-3xl border border-white/10 bg-ink/60 p-6 shadow-2xl shadow-black/20 backdrop-blur sm:p-8">
          <div className="flex items-center justify-between border-b border-white/10 pb-5"><span className="font-mono text-xs uppercase tracking-widest text-slate-500">test surface</span><span className="flex items-center gap-2 text-xs text-teal"><span className="h-2 w-2 rounded-full bg-teal shadow-[0_0_12px_#5eead4]" /> live report</span></div>
          <div className="pt-6"><div className="font-mono text-xs text-slate-500">state → judgment → signal</div><div className="mt-5 space-y-3 font-mono text-sm"><div className="rounded-xl bg-white/[0.05] px-4 py-3 text-coral">surname: <span className="text-white">&quot;maialen&quot;</span></div><div className="pl-7 text-slate-600">↓ <span className="text-slate-400">JEV Choice</span></div><div className="rounded-xl bg-acid/10 px-4 py-3 text-acid">selected: <span className="text-white">female</span></div><div className="pl-7 text-slate-600">↓ <span className="text-slate-400">probability distribution</span></div><div className="grid grid-cols-3 gap-2 text-center text-xs"><div className="rounded-lg border border-white/10 p-3 text-slate-400">male<br /><span className="text-white">0.14</span></div><div className="rounded-lg border border-teal/30 bg-teal/10 p-3 text-teal">female<br /><span className="text-white">0.49</span></div><div className="rounded-lg border border-white/10 p-3 text-slate-400">unisex<br /><span className="text-white">0.37</span></div></div></div></div>
        </div>
      </div>
    </section>

    <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <div className="mb-10 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><Kicker>Two lenses on JEV</Kicker><h2 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-4xl">From labels to paths.</h2></div><p className="max-w-sm text-sm leading-6 text-slate-400">Each report keeps the input, the judgment, and the observable result close together.</p></div>
      <div className="grid gap-5 lg:grid-cols-2">
        <ExperimentCard number="1" title="Can a semantic model read a surname signal?" summary="2,239 names run through JEV Choice and checked against gender-guesser labels, with region slices kept visible instead of folded into one score." href="experiments/gender" metrics={[["2,215", "evaluated rows"], ["94.5%", "male precision"]]} />
        <ExperimentCard number="2" accent="coral" title="Can a model choose a route through Wikipedia?" summary="A beam search asks JEV to rank the next useful article link, then records the successful branches that reached their target." href="experiments/wikipedia" metrics={[["5", "successful races"], ["36", "uncached calls"]]} />
      </div>
    </section>

    <section className="border-y border-white/10 bg-panel/60"><div className="mx-auto grid max-w-7xl gap-10 px-5 py-16 lg:grid-cols-[0.8fr_1.2fr] lg:px-8"><div><Kicker>How we use JEV</Kicker><h2 className="max-w-md font-display text-3xl font-semibold tracking-tight text-white">The model supplies a judgment. The program owns the workflow.</h2></div><div className="grid gap-4 sm:grid-cols-3"><div className="border-l border-acid/60 pl-4"><div className="font-mono text-xs uppercase tracking-widest text-acid">01 / state</div><p className="mt-3 text-sm leading-6 text-slate-400">Give JEV the words and relationships it needs to make one narrow decision.</p></div><div className="border-l border-teal/60 pl-4"><div className="font-mono text-xs uppercase tracking-widest text-teal">02 / signal</div><p className="mt-3 text-sm leading-6 text-slate-400">Keep probabilities and alternatives alongside the winning label.</p></div><div className="border-l border-coral/60 pl-4"><div className="font-mono text-xs uppercase tracking-widest text-coral">03 / code</div><p className="mt-3 text-sm leading-6 text-slate-400">Use the judgment inside a bounded, inspectable workflow.</p></div></div></div></section>
  </Shell>
}

function ReportHeader({ eyebrow, title, description, children }) {
  return <section className="border-b border-white/10 bg-panel/50"><div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-24"><Kicker>{eyebrow}</Kicker><div className="grid gap-8 lg:grid-cols-[1fr_0.75fr] lg:items-end"><div><h1 className="max-w-4xl font-display text-5xl font-bold leading-[0.98] tracking-[-0.04em] text-white sm:text-6xl">{title}</h1><p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">{description}</p></div>{children}</div></div></section>
}

function SectionTitle({ kicker, title, note }) {
  return <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><Kicker>{kicker}</Kicker><h2 className="font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h2></div>{note && <p className="max-w-sm text-sm leading-6 text-slate-500 sm:text-right">{note}</p>}</div>
}

function DataTable({ headers, rows, renderRow }) {
  return <div className="overflow-hidden rounded-2xl border border-white/10 bg-panel"><div className="overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead className="border-b border-white/10 bg-white/[0.035] text-xs uppercase tracking-widest text-slate-500"><tr>{headers.map((header) => <th key={header} className="px-4 py-4 font-medium">{header}</th>)}</tr></thead><tbody className="divide-y divide-white/10">{rows.map((row, index) => renderRow(row, index))}</tbody></table></div></div>
}

function GenderPage() {
  const [filter, setFilter] = useState('all')
  const filteredRows = useMemo(() => genderRows.filter((row) => filter === 'all' || row[10] === filter), [filter])
  return <Shell>
    <ReportHeader eyebrow="Experiment 01 / TypeSafe · JEV Choice" title="Surname signals make a useful JEV test." description="This report runs 2,215 of 2,239 JEV classifications from the gender-guesser Python library, then leaves the slices and failure modes visible." >
      <div className="rounded-2xl border border-acid/20 bg-acid/5 p-5"><div className="font-mono text-xs uppercase tracking-widest text-acid">benchmark frame</div><div className="mt-3 font-display text-2xl font-semibold text-white">2,215 reportable rows</div><div className="mt-2 text-sm leading-6 text-slate-400">Five geo slices have enough support to compare. Seed 20260925 · report regenerated from the existing CSV.</div></div>
    </ReportHeader>
    <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8"><div className="grid grid-cols-2 gap-3 lg:grid-cols-4"><Stat value="64.9%" label="overall accuracy · 1,437 / 2,215" /><Stat value="724" label="unisex predictions · 32.7% of output" accent="teal" /><Stat value="0.63 vs 0.44" label="average confidence · correct vs incorrect" accent="coral" /><Stat value="46.5–73.0%" label="accuracy across five geo slices" /></div></section>
    <section className="mx-auto max-w-7xl px-5 pb-16 lg:px-8"><SectionTitle kicker="01 / outcome" title="What the benchmark actually says" note="JEV got 1,437 of 2,215 reportable rows right. Class-level precision and recall explain the shape of those errors below." /><DataTable headers={['Gender', 'Support', 'Precision', 'Recall', 'True positives', 'False positives', 'False negatives']} rows={[['Male', '1,103', '94.5%', '74.3%', '820', '48', '283'], ['Female', '1,112', '99.0%', '55.5%', '617', '6', '495'], ['Unisex', '0', '0.0%', '0.0%', '0', '724', '0']]} renderRow={(row, index) => <tr key={row[0]} className="text-slate-300"><td className="px-4 py-4 font-semibold text-white">{row[0]}</td>{row.slice(1).map((cell, i) => <td key={i} className={`px-4 py-4 ${i === 1 ? 'text-teal' : ''}`}>{cell}</td>)}</tr>} /></section>
    <section className="mx-auto max-w-7xl px-5 pb-16 lg:px-8"><SectionTitle kicker="02 / slices" title="Performance changes by geo slice" note="Asia is the low point at 46.5%; Middle East and mixed/ambiguous are highest at 73.0%. These dataset segments describe library coverage." /><DataTable headers={['Region', 'Support', 'Accuracy', 'Macro precision', 'Macro recall', 'Correct']} rows={regions} renderRow={(row) => <tr key={row[0]} className="text-slate-300"><td className="px-4 py-4 font-semibold text-white">{row[0]}</td>{row.slice(1).map((cell, i) => <td key={i} className={`px-4 py-4 ${i === 1 ? 'text-acid' : ''}`}>{cell}</td>)}</tr>} /></section>
    <section className="mx-auto max-w-7xl px-5 pb-20 lg:px-8"><div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><SectionTitle kicker="03 / sample rows" title="The judgment at row level" note="A small window into the regenerated report." /><div className="flex rounded-full border border-white/10 bg-panel p-1 text-xs font-semibold"><button onClick={() => setFilter('all')} className={`rounded-full px-3 py-2 transition ${filter === 'all' ? 'bg-acid text-ink' : 'text-slate-400 hover:text-white'}`}>All</button><button onClick={() => setFilter('correct')} className={`rounded-full px-3 py-2 transition ${filter === 'correct' ? 'bg-teal text-ink' : 'text-slate-400 hover:text-white'}`}>Correct</button><button onClick={() => setFilter('incorrect')} className={`rounded-full px-3 py-2 transition ${filter === 'incorrect' ? 'bg-coral text-ink' : 'text-slate-400 hover:text-white'}`}>Incorrect</button></div></div><DataTable headers={['Name', 'Library result', 'Region', 'Expected', 'JEV guess', 'P male', 'P female', 'P unisex', 'Confidence', 'Status']} rows={filteredRows} renderRow={(row) => <tr key={row[0]} className="text-slate-300"><td className="px-4 py-4 font-mono font-semibold text-white">{row[0]}</td><td className="px-4 py-4">{row[1]}</td><td className="px-4 py-4">{row[2]}</td><td className="px-4 py-4">{row[4]}</td><td className="px-4 py-4 font-semibold text-acid">{row[5]}</td><td className="px-4 py-4 font-mono text-xs">{row[6]}</td><td className="px-4 py-4 font-mono text-xs">{row[7]}</td><td className="px-4 py-4 font-mono text-xs">{row[8]}</td><td className="px-4 py-4 font-mono text-xs">{row[9]}</td><td className="px-4 py-4"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${row[10] === 'correct' ? 'bg-teal/15 text-teal' : 'bg-coral/15 text-coral'}`}>{row[10]}</span></td></tr>} /></section>
    <section className="border-y border-white/10 bg-panel/50"><div className="mx-auto grid max-w-7xl gap-8 px-5 py-12 lg:grid-cols-[1fr_1fr] lg:px-8"><div><Kicker>Read the result carefully</Kicker><p className="max-w-xl text-base leading-7 text-slate-300">The most interesting behavior is the role of <span className="text-teal">unisex</span>: 724 predictions land there, while this benchmark has zero unisex ground-truth rows. The confidence gap suggests that the model is at least somewhat more certain when it is correct.</p></div><p className="text-sm leading-7 text-slate-500">The source report notes that male/female include gender-guesser’s mostly_male/mostly_female labels. Country signals describe library coverage and geographic signal strength.</p></div></section>
  </Shell>
}

function RouteCard({ route, index }) {
  return <article className="rounded-3xl border border-white/10 bg-panel p-5 sm:p-7"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><div className="font-mono text-xs uppercase tracking-[0.18em] text-coral">Race 0{index + 1}</div><h3 className="mt-2 font-display text-xl font-semibold text-white">{route.label}</h3></div><span className="w-fit rounded-full bg-white/10 px-3 py-1.5 font-mono text-xs text-slate-300">{route.hops} hops</span></div><ol className="mt-8 flex overflow-x-auto pb-2 pt-2"><>{route.nodes.map((node, nodeIndex) => <li key={node} className="relative flex min-w-[125px] flex-1 items-start after:absolute after:left-[calc(50%+18px)] after:top-5 after:h-px after:w-[calc(100%-36px)] after:bg-white/15 last:after:hidden"><div className="relative z-10 flex w-full flex-col items-center px-2 text-center"><div className="mb-3 flex h-12 w-12 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-ink">{route.images[nodeIndex] ? <img src={route.images[nodeIndex]} alt="" className="h-full w-full object-cover" loading="lazy" referrerPolicy="no-referrer" /> : <span className="font-mono text-xs text-coral">{node.slice(0, 2).toUpperCase()}</span>}</div><span className="max-w-[130px] text-sm font-semibold leading-5 text-white">{node}</span><span className="mt-1 text-[11px] uppercase tracking-widest text-slate-500">{nodeIndex === 0 ? 'start' : nodeIndex === route.nodes.length - 1 ? 'target' : `hop ${nodeIndex}`}</span></div></li>)}</></ol><div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 border-t border-white/10 pt-4 font-mono text-xs uppercase tracking-wider text-slate-500"><span className={route.mode === 'cache-assisted' ? 'text-acid' : 'text-teal'}>{route.mode}</span><span>{route.time}</span><span>{route.calls}</span></div></article>
}

function WikipediaPage() {
  return <Shell>
    <ReportHeader eyebrow="Experiment 02 / TypeSafe · JEV Choice" title="Paths through the encyclopedia." description="Five successful JEV-guided searches, reconstructed from the previous run logs. Each route shows the branch that reached its target article first."><div className="rounded-2xl border border-coral/20 bg-coral/5 p-5"><div className="font-mono text-xs uppercase tracking-widest text-coral">source</div><div className="mt-3 font-display text-2xl font-semibold text-white">.wikipedia_jev.log</div><div className="mt-2 text-sm leading-6 text-slate-400">Five completed runs · thumbnails via Wikimedia Commons · targets normalized by the Wikipedia API.</div></div></ReportHeader>
    <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8"><div className="grid grid-cols-2 gap-3 lg:grid-cols-4"><Stat value="5" label="successful races" accent="coral" /><Stat value="2–10" label="hops per route" accent="teal" /><Stat value="4" label="unique targets" /><Stat value="36" label="uncached JEV calls" accent="coral" /></div></section>
    <section className="mx-auto max-w-7xl px-5 pb-20 lg:px-8"><SectionTitle kicker="01 / found routes" title="Start at the left. Target at the right." note="The route is the successful branch among the candidates explored by the beam search." /><div className="space-y-4">{routes.map((route, index) => <RouteCard key={route.label} route={route} index={index} />)}</div></section>
    <section className="border-y border-white/10 bg-panel/50"><div className="mx-auto grid max-w-7xl gap-5 px-5 py-14 lg:grid-cols-2 lg:px-8"><div className="rounded-2xl border border-white/10 bg-ink/40 p-6"><Kicker>How to read this</Kicker><p className="text-base leading-7 text-slate-300">The search kept a three-path beam at each hop. When a target appeared in the current article’s links, the race stopped and returned that route.</p></div><div className="rounded-2xl border border-coral/15 bg-coral/5 p-6"><Kicker>What the log keeps</Kicker><p className="text-base leading-7 text-slate-300">The logs record fetched articles and completion lines, while cached JEV rankings reveal which retained branch led to the target. The visible paths are the successful branches.</p></div></div></section>
  </Shell>
}

function AboutPage() {
  return <Shell><section className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28"><Kicker>About this playground</Kicker><div className="grid gap-14 lg:grid-cols-[1fr_0.8fr]"><div><h1 className="max-w-3xl font-display text-5xl font-bold leading-[0.98] tracking-[-0.04em] text-white sm:text-6xl">A quick test of <span className="text-acid">JEV</span>, made legible.</h1><p className="mt-8 max-w-2xl text-lg leading-8 text-slate-300">This is a small, deliberately practical playground for TypeSafe’s JEV model. The experiments form an exploratory benchmark for seeing what happens when a typed judgment becomes one part of a normal program.</p><div className="mt-10 flex flex-wrap gap-3"><a href="https://github.com/louispaulet/jev-playground" target="_blank" rel="noreferrer" className="rounded-full bg-acid px-5 py-3 text-sm font-bold text-ink">View the GitHub repo <ArrowUpRight /></a><a href="https://louispaulet.github.io/" target="_blank" rel="noreferrer" className="rounded-full border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:border-teal hover:text-teal">Louis Paulet’s website <ArrowUpRight /></a></div></div><div className="rounded-3xl border border-white/10 bg-panel p-7"><div className="font-mono text-xs uppercase tracking-widest text-slate-500">the short version</div><div className="mt-7 space-y-6"><div className="flex gap-4"><span className="font-mono text-sm text-acid">01</span><p className="text-sm leading-6 text-slate-300">JEV returns a typed choice and its probabilities.</p></div><div className="flex gap-4"><span className="font-mono text-sm text-teal">02</span><p className="text-sm leading-6 text-slate-300">Python keeps control of sampling, search, and evaluation.</p></div><div className="flex gap-4"><span className="font-mono text-sm text-coral">03</span><p className="text-sm leading-6 text-slate-300">The report keeps enough evidence around to inspect the result.</p></div></div></div></div></section><section className="border-y border-white/10 bg-panel/50"><div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 lg:grid-cols-3 lg:px-8"><div><Kicker>Resources</Kicker><h2 className="font-display text-3xl font-semibold text-white">Keep going.</h2></div><a href="https://docs.typesafe.ai/" target="_blank" rel="noreferrer" className="group rounded-2xl border border-white/10 bg-ink/50 p-5 transition hover:border-acid/50"><div className="font-mono text-xs uppercase tracking-widest text-acid">TypeSafe docs</div><p className="mt-3 text-sm leading-6 text-slate-400">Read the current System One and JEV documentation.</p><div className="mt-5 text-white transition group-hover:text-acid">Open docs ↗</div></a><a href="https://github.com/louispaulet/jev-playground" target="_blank" rel="noreferrer" className="group rounded-2xl border border-white/10 bg-ink/50 p-5 transition hover:border-teal/50"><div className="font-mono text-xs uppercase tracking-widest text-teal">Source code</div><p className="mt-3 text-sm leading-6 text-slate-400">See the small Python scripts that produce the experiments.</p><div className="mt-5 text-white transition group-hover:text-teal">Open repository ↗</div></a></div></section></Shell>
}

function App() {
  const path = window.location.pathname.replace(/\/+$/, '')
  if (path.endsWith('/experiments/gender')) return <GenderPage />
  if (path.endsWith('/experiments/wikipedia')) return <WikipediaPage />
  if (path.endsWith('/about')) return <AboutPage />
  return <HomePage />
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
