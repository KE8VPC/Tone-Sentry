"""Advisory discovery of stable tone runs, independent of agency definitions."""
import copy
import json
import uuid
import numpy as np


DEFAULTS = dict(enabled=False, min_seconds=.5, long_seconds=2., max_seconds=15.,
                gap_seconds=.5, stability_hz=8., min_purity=.85, dropout_seconds=.08,min_hz=100.,max_hz=3500.)


class Discovery:
    def __init__(self, settings, dt):
        self.settings = dict(DEFAULTS, **settings)
        self.dt = dt
        self.reset()

    def reset(self):
        self.current = None
        self.runs = []
        self.ready = []
        self.frequency = None
        self.quality = 0.
        self.stats = dict(low_purity_frames=0, short_runs=0, overlong_runs=0, bridged_frames=0, candidates=0)

    def step(self, frequency, quality, now):
        c = self.settings
        self.frequency, self.quality = frequency, quality
        if not c['enabled']: return
        if frequency is not None and quality < c['min_purity']:
            self.stats['low_purity_frames']+=1
        if frequency is None or quality < c['min_purity'] or not c['min_hz'] <= frequency <= c['max_hz']:
            frequency = None
        run = self.current
        # Bridge only missing/low-purity frames, never a different stable frequency.
        # End time remains the last actual tone frame until the same tone returns.
        if run and frequency is None and now-run['end'] < c['dropout_seconds']-self.dt/2:
            self.stats['bridged_frames']+=1
            return
        if run and frequency is not None and abs(frequency - run['mean']) <= c['stability_hz']:
            run['end'] = now+self.dt
            run['count'] += 1
            run['mean'] += (frequency-run['mean'])/run['count']
            run['quality_sum'] += quality
            return
        if run:
            self._end_run()
        if self.runs and now-self.runs[-1]['end'] > c['gap_seconds']+self.dt/2:
            self._emit()
        if frequency is not None:
            self.current = dict(start=now,end=now+self.dt,mean=frequency,count=1,quality_sum=quality)

    def _end_run(self):
        run, self.current = self.current, None
        seconds = run['end']-run['start']
        if self.settings['min_seconds']-self.dt/2 <= seconds <= self.settings['max_seconds']+self.dt/2:
            run.update(hz=round(run['mean'],2),seconds=round(seconds,3),quality=run['quality_sum']/run['count'])
            self.runs.append(run)
            if len(self.runs)>=16: self._emit(ambiguous=True)
        else:
            self.stats['short_runs' if seconds < self.settings['min_seconds'] else 'overlong_runs']+=1
            # A short chirp or an overlong carrier breaks a plausible sequence.
            self._emit()

    def _emit(self, ambiguous=False, truncated=False):
        runs,self.runs = self.runs,[]
        if not runs: return
        sequence=[dict(hz=r['hz'],seconds=r['seconds'],offset_seconds=round(r['start']-runs[0]['start'],3),
                       gap_before=round(max(0,r['start']-runs[i-1]['end']),3) if i else 0,
                       quality=round(r['quality'],3)) for i,r in enumerate(runs)]
        pairs=[]
        if len(runs)==1 and runs[0]['seconds'] >= self.settings['long_seconds']-self.dt/2:
            pairs=[(runs[0],None)]
        elif len(runs)>=2:
            pairs=list(zip(runs,runs[1:]))
        for a,b in pairs:
            if b and (abs(a['hz']-b['hz']) <= 2 or b['start']-a['end'] > self.settings['gap_seconds']+self.dt/2):
                continue
            self.ready.append(dict(kind='two' if b else 'long',a_hz=a['hz'],b_hz=b['hz'] if b else None,
                a_seconds=a['seconds'],b_seconds=b['seconds'] if b else None,
                gap_seconds=round(max(0,b['start']-a['end']),3) if b else 0,
                start=a['start'],end=(b or a)['end'],quality=round(min(a['quality'],(b or a)['quality']),3),
                ambiguous=ambiguous or len(runs)>2,truncated=truncated,sequence=sequence,
                sequence_start=runs[0]['start'],sequence_end=runs[-1]['end']))
            self.stats['candidates']+=1

    def finish(self):
        truncated=self.current is not None
        if self.current: self._end_run()
        self._emit(truncated=truncated)

    def drain(self):
        result,self.ready=self.ready,[]
        return result


class Candidates:
    def __init__(self, store):
        self.store=store
        with store.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS tone_candidates(
                id TEXT PRIMARY KEY,kind TEXT NOT NULL,a REAL NOT NULL,b REAL NOT NULL,
                source TEXT NOT NULL,first_seen REAL NOT NULL,last_seen REAL NOT NULL,
                count INTEGER NOT NULL,data TEXT NOT NULL)''')

    def observe(self, item, source, offset):
        data=copy.deepcopy(item)
        data.update(start=item['start']+offset,end=item['end']+offset,source=source)
        if 'sequence_start' in data:
            data['sequence_start']+=offset;data['sequence_end']+=offset
        observation = dict(at=data['start'], end=data['end'], a_seconds=data['a_seconds'],
                           b_seconds=data['b_seconds'], quality=data['quality'], recording_id=data.get('recording_id'),
                           sequence=data.get('sequence',[]),sequence_start=data.get('sequence_start'),
                           ambiguous=data.get('ambiguous',False),truncated=data.get('truncated',False))
        b=data['b_hz'] or 0
        # Absolute matching against the original observation avoids cumulative drift.
        with self.store.transaction() as db:
            row=db.execute('SELECT * FROM tone_candidates WHERE kind=? AND source=? AND ABS(a-?)<=8 AND ABS(b-?)<=8 ORDER BY ABS(a-?)+ABS(b-?) LIMIT 1',
                           (data['kind'],source,data['a_hz'],b,data['a_hz'],b)).fetchone()
            if row:
                cid = row['id']
                old=json.loads(row['data'])
                data['recent']= (old.get('recent',[])+[observation])[-20:]
                db.execute('UPDATE tone_candidates SET last_seen=?,count=count+1,data=? WHERE id=?',(data['start'],json.dumps(data),row['id']))
            else:
                cid = str(uuid.uuid4())
                data['recent'] = [observation]
                db.execute('INSERT INTO tone_candidates VALUES(?,?,?,?,?,?,?,?,?)',
                           (cid,data['kind'],data['a_hz'],b,source,data['start'],data['start'],1,json.dumps(data)))
            db.execute('DELETE FROM tone_candidates WHERE id NOT IN (SELECT id FROM tone_candidates ORDER BY last_seen DESC LIMIT 1000)')
            db.execute("DELETE FROM hidden_history WHERE table_name='tone_candidates' AND (id=? OR id NOT IN (SELECT id FROM tone_candidates))", (cid,))
        return cid

    def rows(self):
        return self.store.rows('SELECT * FROM tone_candidates ORDER BY last_seen DESC LIMIT 1000')


def configured_matches(candidate, tones):
    matches=[]
    for t in tones:
        if t['kind']!=candidate['kind']: continue
        keys=['a_hz','b_hz'] if t['kind']=='two' else ['a_hz']
        if all(abs(candidate[k]-t[k])<=max(3,t[k]*t['tolerance_percent'] if t.get('tolerance_percent') else t['tolerance_hz']) for k in keys):
            matches.append(t['agency'])
    return matches


def draft(candidate):
    t=dict(id='discovered-'+uuid.uuid4().hex[:12],agency='Unidentified agency',enabled=False,
           kind=candidate['kind'],a_hz=candidate['a_hz'],gap_max=min(5,max(.3,candidate['gap_seconds']+.12)),
           tolerance_hz=8.,duplicate_seconds=120.,tests=[],allow_cloud=False)
    for prefix in (['a','b'] if t['kind']=='two' else ['a']):
        seconds=candidate[prefix+'_seconds']
        t[prefix+'_hz']=candidate[prefix+'_hz']
        t[prefix+'_min']=round(max(.12,seconds*.8),2)
        t[prefix+'_max']=round(min(60,seconds*1.25+.12),2)
    if t['kind']=='two': t['tolerance_hz']=min(8.,abs(t['a_hz']-t['b_hz'])/3)
    return t
