"""Stable, versioned depth-first maze plans stored in personal.json."""
import random, hashlib, math

def plan(config, room, entries):
    layouts=config.setdefault('layouts',{})
    ids=sorted(entries)
    prior=layouts.get(room)
    if prior and prior.get('entries')==ids and prior.get('version')==1:
        return prior
    seed=hashlib.sha256((room+'|'+ '|'.join(ids)).encode()).hexdigest()[:16]
    rng=random.Random(seed)
    n=max(3,math.ceil(math.sqrt(len(ids)*2+1)))
    walls=[[True]*4 for _ in range(n*n)]
    seen={0}; stack=[0]
    while stack:
        cell=stack[-1]; x,y=cell%n,cell//n
        choices=[(d,ny*n+nx) for d,(nx,ny) in enumerate([(x,y-1),(x+1,y),(x,y+1),(x-1,y)]) if 0<=nx<n and 0<=ny<n and ny*n+nx not in seen]
        if not choices: stack.pop(); continue
        d,other=rng.choice(choices); walls[cell][d]=False; walls[other][(d+2)%4]=False; seen.add(other); stack.append(other)
    cells=list(range(1,n*n)); rng.shuffle(cells)
    result={'version':1,'seed':seed,'entries':ids,'size':n,'walls':walls,'placements':dict(zip(ids,cells))}
    layouts[room]=result
    return result
