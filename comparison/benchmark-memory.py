"""Observe a sibling API cgroup while issuing the saved comparison requests.

Run in a separate container with --pid=container:TARGET --cgroupns=host.
Only reads the target cgroup. The observer/client has its own cgroup, so its
Python interpreter, threads and HTTP buffers are excluded from target memory.
"""
import argparse
import collections
import concurrent.futures
import json
import statistics
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

parser=argparse.ArgumentParser()
parser.add_argument('--server',choices=['python','rust'],required=True)
parser.add_argument('--samples-root',default='/reports/scenarios')
parser.add_argument('--output',default='/reports/memory')
parser.add_argument('--repeats',type=int,default=10)
parser.add_argument('--readiness-path',default='/health/ready')
args=parser.parse_args()
out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
source=Path(args.samples_root)
base='http://memory-'+args.server+'-api:8000'
cgroup_line=next(line for line in Path('/proc/1/cgroup').read_text().splitlines() if line.startswith('0::'))
cgroup=Path('/sys/fs/cgroup')/cgroup_line.split(':',2)[2].lstrip('/')
own=Path('/proc/self/cgroup').read_text()
assert cgroup_line not in own.splitlines(), 'Observer must have its own cgroup'

def snapshot():
    stat={k:int(v) for k,v in (line.split() for line in (cgroup/'memory.stat').read_text().splitlines())}
    status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/1/status').read_text().splitlines() if ':' in line}
    current=int((cgroup/'memory.current').read_text())
    return dict(t=time.perf_counter(),current=current,working_set=max(0,current-stat.get('inactive_file',0)),
                kernel_peak=int((cgroup/'memory.peak').read_text()),anon=stat['anon'],file=stat['file'],
                rss=int(status['VmRSS'].split()[0])*1024,hwm=int(status['VmHWM'].split()[0])*1024,
                swap=int((cgroup/'memory.swap.current').read_text()))

def call(case,index=0):
    payload=json.dumps(case['body']).encode() if 'body' in case else None
    req=Request(base+case['path'],data=payload,method=case['method'],headers={'Content-Type':'application/json','X-Forwarded-For':f'203.0.113.{index+1}'})
    start=time.perf_counter()
    try:
        with urlopen(req,timeout=120) as response:
            size=len(response.read());status=response.status
    except HTTPError as error:
        size=len(error.read());status=error.code
    return dict(status=status,bytes=size,ms=(time.perf_counter()-start)*1000)

def observe(name,case,concurrency=1):
    samples=[];stop=threading.Event()
    def watch():
        while not stop.is_set():
            samples.append(snapshot());stop.wait(.001)
        samples.append(snapshot())
    thread=threading.Thread(target=watch)
    before=snapshot();thread.start()
    try:
        if concurrency==1:
            responses=[call(case) for _ in range(args.repeats)]
        else:
            barrier=threading.Barrier(concurrency)
            def work(index):
                barrier.wait();return call(case,index)
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                responses=list(executor.map(work,range(concurrency)))
    finally:
        stop.set();thread.join()
    # A short fixed settle window is not a garbage-collection or leak test.
    time.sleep(.25)
    after=snapshot()
    peak={k:max(s[k] for s in samples) for k in ['current','working_set','rss','anon','swap']}
    intervals=[(b['t']-a['t'])*1000 for a,b in zip(samples,samples[1:])]
    row=dict(name=name,concurrency=concurrency,before=before,observed_peak=peak,after=after,
             additional_observed_peak=max(0,peak['current']-before['current']),sample_count=len(samples),
             interval_median_ms=statistics.median(intervals) if intervals else None,interval_max_ms=max(intervals,default=None),
             statuses=dict(collections.Counter(r['status'] for r in responses)),responses=responses)
    (out/(args.server+'-'+name+'-samples.json')).write_text(json.dumps(samples))
    print(json.dumps(dict(server=args.server,name=name,before_mib=before['current']/2**20,peak_mib=peak['current']/2**20,after_mib=after['current']/2**20,statuses=row['statuses'])),flush=True)
    return row

for attempt in range(90):
    try:
        with urlopen(base+args.readiness_path,timeout=2) as response:
            if response.status==200:break
    except Exception:time.sleep(1)
else:raise RuntimeError('API did not become ready')
time.sleep(1)
report=dict(server=args.server,started=datetime.now(timezone.utc).isoformat(),
            method=f'Fresh API process; saved scenarios in original order, {args.repeats} sequential requests each. Observer in separate cgroup. 1 ms requested sampling interval; per-case peaks are observed lower bounds, kernel_peak is exact container lifetime peak.',
            idle=snapshot(),cases=[])
path=out/(args.server+'.json')
def save():path.write_text(json.dumps(report,indent=2))
save()
order=json.loads((source/'normal.json').read_text())
report['case_count']=len(order)
if (source/'manifest.json').exists():report['input_manifest']=json.loads((source/'manifest.json').read_text())
for row in order:
    case=json.loads((source/'normal'/row['name']/'input.json').read_text())
    report['cases'].append(observe(row['name'],case));save()
heavy=json.loads((source/'normal/usd_five_8years/input.json').read_text())
for count in [2,8,16]:
    report['cases'].append(observe('concurrent_'+str(count),heavy,count));save()
time.sleep(1)
report['end']=snapshot()
report['memory_events']=(cgroup/'memory.events').read_text()
save()
