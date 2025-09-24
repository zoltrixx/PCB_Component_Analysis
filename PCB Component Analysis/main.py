#!/usr/bin/env python3
"""
PCB Component Placement Algorithm
- Fulfills hard/soft constraints
- Outputs placement summary + PNG plot
- Corrected to save files reliably on local machines
"""

import os
import math
import random
import time
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict

import matplotlib
matplotlib.use('Agg')  # ensures savefig works without display
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

# Save outputs to current directory
OUTPUT_DIR = os.getcwd()

BOARD_W = BOARD_H = 50
BOARD_CENTER = (BOARD_W/2.0, BOARD_H/2.0)

COMP_SPECS = {
    "USB": (5,5),
    "MCU": (5,5),
    "CRYSTAL": (5,5),
    "MB1": (5,15),
    "MB2": (5,15)
}

@dataclass
class Component:
    name: str
    w: int
    h: int
    x: int = 0
    y: int = 0
    rot: int = 0

    def placed_dims(self) -> Tuple[int,int]:
        return (self.w, self.h) if self.rot == 0 else (self.h, self.w)

    def rect(self) -> Tuple[float,float,float,float]:
        w,h = self.placed_dims()
        return (self.x, self.y, self.x + w, self.y + h)

    def center(self) -> Tuple[float,float]:
        w,h = self.placed_dims()
        return (self.x + w/2.0, self.y + h/2.0)

# ---------- Utility functions ----------
def distance(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

def rect_overlap(r1, r2) -> bool:
    l1,t1,r1x,b1 = r1
    l2,t2,r2x,b2 = r2
    if r1x <= l2 or r2x <= l1: return False
    if b1 <= t2 or b2 <= t1: return False
    return True

def line_segment_intersects_rect(p0, p1, rect) -> bool:
    x0,y0 = p0; x1,y1 = p1
    left, top, right, bottom = rect
    dx = x1 - x0; dy = y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - left, right - x0, y0 - top, bottom - y0]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-12:
            if qi < 0: return False
            continue
        t = qi/pi
        if pi < 0:
            if t > u2: return False
            if t > u1: u1 = t
        else:
            if t < u1: return False
            if t < u2: u2 = t
    return not (u2 < u1)

def inside_board(comp: Component) -> bool:
    l,t,r,b = comp.rect()
    return l >= 0 and t >= 0 and r <= BOARD_W and b <= BOARD_H

def compute_usb_keepout(usb: Component):
    l,t,r,b = usb.rect()
    w,h = usb.placed_dims()
    sides = []
    eps = 1e-6
    if abs(t - 0) < eps: sides.append('top')
    if abs(b - BOARD_H) < eps: sides.append('bottom')
    if abs(l - 0) < eps: sides.append('left')
    if abs(r - BOARD_W) < eps: sides.append('right')
    side = sides[0] if sides else 'top'
    if side == 'top':
        cx = l + w/2.0; cy = t
        left = cx-5; right = cx+5; top = cy; bottom = cy+15
    elif side == 'bottom':
        cx = l + w/2.0; cy = b
        left = cx-5; right = cx+5; bottom = cy; top = cy-15
    elif side == 'left':
        cx = l; cy = t + h/2.0
        top = cy-5; bottom = cy+5; left = cx; right = cx+15
    else:
        cx = r; cy = t + h/2.0
        top = cy-5; bottom = cy+5; right = cx; left = cx-15
    return (max(0,left), max(0,top), min(BOARD_W,right), min(BOARD_H,bottom))

def center_of_mass(comps: List[Component]):
    xs = [c.center()[0] for c in comps]
    ys = [c.center()[1] for c in comps]
    return (sum(xs)/len(xs), sum(ys)/len(ys))

# ---------- Candidate generators ----------
def generate_mb_mirrored_positions(step=1):
    positions=[]
    w,h = COMP_SPECS["MB1"]
    for y in range(0, BOARD_H-h+1, step):
        mb1=(0,y,0); mb2=(BOARD_W-w,y,0)
        positions.append(('vertical',mb1,mb2))
    for x in range(0, BOARD_W-h+1, step):
        mb1=(x,0,90); mb2=(x,BOARD_H-w,90)
        positions.append(('horizontal',mb1,mb2))
    return positions

def generate_usb_edge_positions(step=1):
    w,h=COMP_SPECS["USB"]; pos=[]
    for x in range(0,BOARD_W-w+1,step):
        pos.append((x,0,0)); pos.append((x,BOARD_H-h,0))
    for y in range(0,BOARD_H-h+1,step):
        pos.append((0,y,90)); pos.append((BOARD_W-w,y,90))
    return pos

# ---------- Main search ----------
def find_solution(time_limit=1.9, seed=42) -> Optional[Dict]:
    random.seed(seed); start=time.time()
    mb_positions=generate_mb_mirrored_positions()
    usb_positions=generate_usb_edge_positions()
    crystal_offsets=[(dx,dy) for dx in range(-10,11) for dy in range(-10,11) if dx*dx+dy*dy<=100]
    for orient,mb1p,mb2p in mb_positions:
        if time.time()-start>time_limit: break
        mb1=Component("MB1",*COMP_SPECS["MB1"],x=mb1p[0],y=mb1p[1],rot=mb1p[2])
        mb2=Component("MB2",*COMP_SPECS["MB2"],x=mb2p[0],y=mb2p[1],rot=mb2p[2])
        if not (inside_board(mb1) and inside_board(mb2)): continue
        if rect_overlap(mb1.rect(),mb2.rect()): continue
        for usbp in usb_positions:
            if time.time()-start>time_limit: break
            usb=Component("USB",*COMP_SPECS["USB"],x=usbp[0],y=usbp[1],rot=usbp[2])
            if not inside_board(usb): continue
            if any(rect_overlap(usb.rect(),o.rect()) for o in (mb1,mb2)): continue
            keepout=compute_usb_keepout(usb)
            # MCU near center
            mx,my=int(BOARD_CENTER[0]-2),int(BOARD_CENTER[1]-2)
            mcu=Component("MCU",*COMP_SPECS["MCU"],x=mx,y=my)
            if any(rect_overlap(mcu.rect(),o.rect()) for o in (usb,mb1,mb2)): continue
            for dx,dy in crystal_offsets:
                cx,cy=mcu.center()[0]+dx,mcu.center()[1]+dy
                cryst=Component("CRYSTAL",*COMP_SPECS["CRYSTAL"],x=int(cx-2),y=int(cy-2))
                if not inside_board(cryst): continue
                if any(rect_overlap(cryst.rect(),o.rect()) for o in (usb,mb1,mb2,mcu)): continue
                if distance(cryst.center(),mcu.center())>10: continue
                if line_segment_intersects_rect(cryst.center(),mcu.center(),keepout): continue
                comps=[usb,mb1,mb2,mcu,cryst]
                com=center_of_mass(comps)
                if distance(com,BOARD_CENTER)>2: continue
                return {'USB':usb,'MB1':mb1,'MB2':mb2,'MCU':mcu,'CRYSTAL':cryst,'keepout':keepout,'com':com}
    return None

# ---------- Plotting & Summary ----------
def plot_solution(sol:Dict,fname="pcb_solution.png"):
    fig,ax=plt.subplots(figsize=(6,6))
    ax.add_patch(Rectangle((0,0),BOARD_W,BOARD_H,fill=False,lw=2))
    colors={'USB':'red','MCU':'blue','CRYSTAL':'orange','MB1':'purple','MB2':'green'}
    for name in ('USB','MB1','MB2','MCU','CRYSTAL'):
        c=sol[name]; l,t,r,b=c.rect(); w,h=r-l,b-t
        ax.add_patch(Rectangle((l,t),w,h,facecolor=colors[name],alpha=0.7))
        ax.text(*c.center(),name,ha='center',va='center',color='white',fontsize=8)
    l,t,r,b=sol['keepout']
    ax.add_patch(Rectangle((l,t),r-l,b-t,facecolor='red',alpha=0.2))
    ax.set_xlim(0,BOARD_W); ax.set_ylim(0,BOARD_H); ax.set_aspect('equal')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(fname,dpi=200); plt.close(fig)

def save_summary(sol:Dict,fname="pcb_solution_summary.txt"):
    with open(fname,"w") as f:
        if sol is None: f.write("No solution found\n"); return
        f.write("PCB Placement Solution\n\n")
        for name in ('USB','MB1','MB2','MCU','CRYSTAL'):
            c=sol[name]
            f.write(f"{name}: top-left=({c.x},{c.y}), center={c.center()}, rot={c.rot}\n")
        f.write(f"Center of Mass: {sol['com']}\n")
        f.write(f"Keepout: {sol['keepout']}\n")

# ---------- Entry ----------
def main():
    print(f"Outputs will be saved in {OUTPUT_DIR}")
    sol=find_solution()
    if sol:
        print("Solution found!"); 
        plot_solution(sol,os.path.join(OUTPUT_DIR,"pcb_solution.png"))
        save_summary(sol,os.path.join(OUTPUT_DIR,"pcb_solution_summary.txt"))
        print("Saved pcb_solution.png and pcb_solution_summary.txt")
    else:
        print("No solution found.")

if __name__=="__main__":
    main()
