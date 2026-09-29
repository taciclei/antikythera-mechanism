import math
from data import G, rp, polar
ST = {"S": "st-s", "R": "st-r", "H": "st-h"}
S = 3.6  # px per mm

def f(v): return f"{v:.1f}"

class Plan:
    def __init__(s, xmin, xmax, ymin, ymax, pad=26):
        s.x0, s.x1, s.y0, s.y1, s.pad = xmin, xmax, ymin, ymax, pad
        s.shapes, s.lines, s.labels = [], [], []
    def X(s, x): return (x - s.x0)*S + s.pad
    def Y(s, y): return (s.y1 - y)*S + s.pad
    def circle(s, c, r, cls, extra=""):
        s.shapes.append(f'<circle cx="{f(s.X(c[0]))}" cy="{f(s.Y(c[1]))}" r="{f(r*S)}" class="{cls}" {extra}/>')
    def gear(s, name, c):
        s.circle(c, rp(name), "gear " + ST[G[name]['st']])
    def dot(s, c):
        s.shapes.append(f'<circle cx="{f(s.X(c[0]))}" cy="{f(s.Y(c[1]))}" r="2.2" class="axis-dot"/>')
    def mesh(s, a, b, d=None):
        x1, y1, x2, y2 = s.X(a[0]), s.Y(a[1]), s.X(b[0]), s.Y(b[1])
        s.lines.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="mesh-line"/>')
        if d is not None:
            s.labels.append(f'<text x="{f((x1+x2)/2+4)}" y="{f((y1+y2)/2-4)}" class="dist">{d:.2f}</text>')
    def label(s, c, text, dx=6, dy=-6, anchor="start", cls="lbl"):
        s.labels.append(f'<text x="{f(s.X(c[0])+dx)}" y="{f(s.Y(c[1])+dy)}" text-anchor="{anchor}" class="{cls}">{text}</text>')
    def raw(s, t): s.shapes.append(t)
    def svg(s, aria):
        w = (s.x1-s.x0)*S + 2*s.pad; h = (s.y1-s.y0)*S + 2*s.pad
        return (f'<svg viewBox="0 0 {f(w)} {f(h)}" role="img" aria-label="{aria}" class="plan">'
                + "".join(s.shapes) + "".join(s.lines) + "".join(s.labels) + "</svg>")

def rear():
    p = Plan(-52, 82, -124, 96)
    A = dict(B=(0,0), C=(-7.89,-23.17), D=(-13.07,-38.42), E=(14.11,-11.02), L=(19.87,14.29),
             M=(0,45.5), N=(0,63.0), G=(0,-82.5), F=(19.73,-73.47), O=(-24.4,63.0), cal=(24.4,63.0),
             P=(12.8,76.7), H=(11.6,-96.1), I=(0,-107.5))
    ang = math.radians(-38)
    A['K'] = (A['E'][0]+25.6*math.cos(ang), A['E'][1]+25.6*math.sin(ang))
    A['Kp'] = (A['E'][0]+26.7*math.cos(ang), A['E'][1]+26.7*math.sin(ang))
    # b1 as a faint reference (it sits in front of the plate)
    p.circle(A['B'], rp('b1'), "ref-ring")
    bl = polar(rp('b1'), 222); p.label(bl, "b1 (côté avant)", dx=-6, dy=8, anchor="end", cls="lbl muted")
    # a1 contrate, seen edge-on at the right of b1
    x0, x1, yy = p.X(64.4), p.X(78.0), 13.86
    p.raw(f'<rect x="{f(x0)}" y="{f(p.Y(yy))}" width="{f(x1-x0)}" height="{f(2*yy*S)}" class="gear st-s" rx="3"/>')
    p.label((71.2, -13.86), "a1", dx=0, dy=16, anchor="middle")
    big = ['e3','e4','d2','m1']
    order = ['e3','e4','d2','m1','b2','c2','c1','d1','e1','e2','e5','e6','l1','l2','m2','m3','n1','n2','n3','o1','p1','p2','cal1','f1','f2','g1','g2','h1','h2','i1','b3']
    where = dict(b2='B',b3='B',c1='C',c2='C',d1='D',d2='D',e1='E',e2='E',e3='E',e4='E',e5='E',e6='E',
                 l1='L',l2='L',m1='M',m2='M',m3='M',n1='N',n2='N',n3='N',o1='O',p1='P',p2='P',cal1='cal',
                 f1='F',f2='F',g1='G',g2='G',h1='H',h2='H',i1='I')
    for n in order: p.gear(n, A[where[n]])
    p.gear('k1', A['K']); p.gear('k2', A['Kp'])
    meshes = [('B','C',24.48),('C','D',16.10),('D','E',38.60),('E','B',17.90),('B','L',24.48),('L','M',37.00),
              ('M','E',58.25),('E','F',62.70),('F','G',21.70),('G','H',17.90),('H','I',16.30),('M','N',17.48),
              ('N','O',24.40),('N','P',18.75),('P','cal',18.00),('E','K',25.60)]
    for a,b,d in meshes: p.mesh(A[a], A[b], d)
    for k in A: p.dot(A[k])
    L = {'B':"B · b2 b3",'C':"C · c1 c2",'D':"D · d1 d2",'E':"E · e1–e6",'L':"L · l1 l2",'M':"M · m1 m2 m3",
         'N':"N · n1 n2 n3",'O':"O · o1",'P':"P · p1 p2",'cal':"cal1",'F':"F · f1 f2",'G':"G · g1 g2",
         'H':"H · h1 h2",'I':"I · i1",'K':"K K′ · k1 k2"}
    off = {'B':(-8,-8,'end'),'C':(-8,4,'end'),'D':(-8,14,'end'),'E':(8,-6,'start'),'L':(8,-6,'start'),'M':(8,-6,'start'),
           'N':(8,15,'start'),'O':(-8,-8,'end'),'P':(8,-6,'start'),'cal':(8,12,'start'),'F':(8,-6,'start'),
           'G':(-8,-6,'end'),'H':(8,-6,'start'),'I':(-8,14,'end'),'K':(8,14,'start')}
    for k,t in L.items():
        dx,dy,an = off[k]; p.label(A[k], t, dx, dy, an)
    p.label((-50, 92), "Nord : cadran Métonique", dx=0, dy=0, cls="lbl muted")
    p.label((-50, -120), "Sud : cadran du Saros", dx=0, dy=0, cls="lbl muted")
    return p.svg("Plan à l'échelle des axes de la plaque principale, vus de face par transparence")

def front_b1():
    p = Plan(-72, 72, -72, 72)
    p.circle((0,0), rp('b1'), "gear st-s")
    for i,(a,lab) in enumerate([(60,'A'),(-30,'B'),(240,'C'),(150,'D')]):
        e = polar(62, a)
        p.raw(f'<line x1="{f(p.X(0))}" y1="{f(p.Y(0))}" x2="{f(p.X(e[0]))}" y2="{f(p.Y(e[1]))}" class="spoke"/>')
        t = polar(55, a+7); p.label(t, f"rayon {lab}", 0, 4, "middle", "lbl muted")
    C = (0,0)
    for n in ['fx51','fx49','nd48']: p.gear(n, C)
    spA, spB, spC = polar(33.15,60), polar(27.0,-30), polar(25.6,240)
    me40, me20 = (27.97,-1.32), (32.36,-15.78)
    vn26, r1 = (-11.15,-6.68), (-25.2,11.75)
    for n,c in [('me72',spA),('me89',spA),('nd62',spB),('nd64',spB),('vn44',spC),('vn34',spC),('me40',me40),('me20',me20),('vn26',vn26),('r1',r1)]:
        p.gear(n, c)
    for a,b,d in [(C,spA,33.15),(C,spB,27.00),(C,spC,25.60),(spA,me40,32.25),(me40,me20,15.00),(spC,vn26,15.63),(vn26,r1,23.18)]:
        p.mesh(a,b,d)
    for c in [C,spA,spB,spC,me40,me20,vn26,r1]: p.dot(c)
    p.label(C, "fixes : fx51 fx49 · nœuds nd48", 8, 16)
    p.label(spA, "me72 · me89", 8, -6); p.label(spB, "nd62 · nd64", 8, 14)
    p.label(spC, "vn44 · vn34", -8, 16, "end"); p.label(me40, "me40", 8, -4); p.label(me20, "me20 (épicycle Mercure)", 8, 14)
    p.label(vn26, "vn26", -8, -6, "end"); p.label(r1, "r1 63 (épicycle Vénus)", -8, -8, "end")
    return p.svg("Trains épicycloïdaux portés par b1 : nœuds, Mercure, Vénus")

def front_cp():
    p = Plan(-72, 72, -72, 72)
    p.circle((0,0), 65.0, "ref-ring")
    C=(0,0)
    cp52, su56, cp64 = polar(25.92,110), polar(39.71,150), polar(28.80,-85)
    sa40, sa68, sa86s = (-1.1,47.3), (22.1,35.7), (20.6,35.7)
    ju40, ju43, ju65s = (22.1,-34.4), (28.6,-15.6), (27.0,-15.6)
    ma40, ma71, ma80s = (-3.9,-46.3), (-24.9,-30.0), (-19.2,-33.3)
    p.gear('fx56', C)
    for n,c in [('cp52',cp52),('sa61',cp52),('su56',su56),('cp64',cp64),('ma38',cp64),('ju45',cp64),
                ('sa40',sa40),('sa68',sa68),('sa86s',sa86s),('ju40',ju40),('ju43',ju43),('ju65s',ju65s),
                ('ma40',ma40),('ma71',ma71),('ma80s',ma80s)]:
        p.gear(n, c)
    for a,b,d in [(C,cp52,25.92),(cp52,su56,25.92),(C,cp64,28.80),(cp52,sa40,24.24),(sa40,sa68,25.92),(sa86s,C,41.28),
                  (cp64,ju40,20.40),(ju40,ju43,19.92),(ju65s,C,31.20),(cp64,ma40,18.72),(ma40,ma71,26.64),(ma80s,C,38.40)]:
        p.mesh(a,b,d)
    for c in [C,cp52,su56,cp64,sa40,sa68,ju40,ju43,ma40,ma71]: p.dot(c)
    p.label(C, "fx56 fixe · sorties sa86o ju65o ma80o", 8, 16)
    p.label(cp52, "cp52 · sa61", -8, -8, "end"); p.label(su56, "su56 Soleil vrai", -8, -8, "end")
    p.label(cp64, "cp64 · ma38 · ju45", 8, 16); p.label(sa40, "sa40", -8, -6, "end")
    p.label(sa68, "sa68 ⇢ sa86s", 8, -8); p.label(ju40, "ju40", 8, 14); p.label(ju43, "ju43 ⇢ ju65s", 8, -8)
    p.label(ma40, "ma40", 8, 14); p.label(ma71, "ma71 ⇢ ma80s", -8, -8, "end")
    p.label((0,65), "bord de la plaque CP (r 65)", 0, -6, "middle", "lbl muted")
    return p.svg("Trains du Soleil vrai et des planètes supérieures sur la plaque CP")

# ---------- train tree ----------
def tree():
    cx = [46, 160, 280, 410, 540, 670, 800, 930, 1060]
    OX = 1192
    ry = [40, 108, 176, 244, 312, 380, 448]
    N = {}
    def node(k, col, row, t1, t2, st="S"):
        N[k] = dict(x=cx[col], y=ry[row], t1=t1, t2=t2, st=st, w=max(len(t1), len(t2))*6.9+20)
    node('a1',0,1,"a1","48"); node('b1',1,1,"b1","223"); node('b2',2,1,"b2","64")
    node('c',3,0,"c1 · c2","38 · 48"); node('d',4,0,"d1 · d2","24 · 127"); node('ep',5,0,"e2 · e5","32 · 50")
    node('k',6,0,"k1 ⇢ k2","50 · 50"); node('ei',7,0,"e6 · e1","50 · 32"); node('b3',8,0,"b3","32")
    node('l',3,2,"l1 · l2","38 · 53"); node('m',4,2,"m1 · m3 · m2","96 · 27 · 15","R")
    node('e3',5,1,"e3 · e4","223 · 188"); node('f',6,2,"f1 · f2","53 · 30"); node('g',7,2,"g1 · g2","54 · 20")
    node('h',7,3,"h1 · h2","60 · 15"); node('i',8,3,"i1","60")
    node('n',5,4,"n1 · n3 · n2","53 · 57 · 15","R"); node('o',6,5,"o1","60"); node('p',6,6,"p1 · p2","60 · 12","R"); node('cal',7,6,"cal1","60","R")
    OUT = [(0,"Lune","+254/19","S",'b3'),(1,"Apsides","−477/4237","R",'e3'),(2,"Saros","−940/4237","R",'g'),
           (3,"Exeligmos","−235/12711","R",'i'),(4,"Métonique","−5/19","R",'n'),(5,"Olympiade","+1/4","R",'o'),
           (6,"Callippique","−1/76","R",'cal')]
    E = [('a1','b1',"48:223"),('b1','b2',"même axe"),('b2','c',"64:38"),('c','d',"48:24"),('d','ep',"127:32"),
         ('ep','k',"50:50"),('k','ei',"50:50"),('ei','b3',"32:32"),('b2','l',"64:38"),('l','m',"53:96"),
         ('m','e3',"27:223"),('e3','f',"188:53"),('f','g',"30:54"),('g','h',"20:60"),('h','i',"15:60"),
         ('m','n',"15:53"),('n','o',"57:60"),('n','p',"15:60"),('p','cal',"12:60")]
    out = ['<defs><marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z" class="arrowhead"/></marker></defs>']
    for a,b,lab in E:
        A, B = N[a], N[b]
        if abs(A['x']-B['x']) < 1:
            x1, y1, x2, y2 = A['x'], A['y']+18, B['x'], B['y']-18
            out.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2-2)}" class="edge" marker-end="url(#arr)"/>')
            out.append(f'<text x="{f(x1+8)}" y="{f((y1+y2)/2+4)}" class="elbl">{lab}</text>')
        else:
            x1, y1, x2, y2 = A['x']+A['w']/2, A['y'], B['x']-B['w']/2, B['y']
            out.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2-2)}" y2="{f(y2)}" class="edge" marker-end="url(#arr)"/>')
            out.append(f'<text x="{f((x1+x2)/2)}" y="{f((y1+y2)/2-6)}" text-anchor="middle" class="elbl">{lab}</text>')
    A, B = N['e3'], N['k']
    out.append(f'<path d="M{f(A["x"]+20)},{f(A["y"]-18)} C{f(A["x"]+50)},{f(A["y"]-44)} {f(B["x"]-40)},{f(B["y"]+44)} {f(B["x"]-8)},{f(B["y"]+20)}" class="edge carrier" marker-end="url(#arr)"/>')
    out.append(f'<text x="{f(A["x"]+64)}" y="{f(A["y"]-22)}" class="elbl strong">porte k1, k2</text>')
    for k,v in N.items():
        cls = {"S":"st-s","R":"st-r","H":"st-h"}[v['st']]
        out.append(f'<rect x="{f(v["x"]-v["w"]/2)}" y="{f(v["y"]-18)}" width="{f(v["w"])}" height="36" rx="4" class="tnode {cls}"/>')
        out.append(f'<text x="{f(v["x"])}" y="{f(v["y"]-3)}" text-anchor="middle" class="tlbl">{v["t1"]}</text>')
        out.append(f'<text x="{f(v["x"])}" y="{f(v["y"]+12)}" text-anchor="middle" class="tteeth">{v["t2"]}</text>')
    for row,name,rate,st,src in OUT:
        y = ry[row]; s = N[src]
        out.append(f'<line x1="{f(s["x"]+s["w"]/2)}" y1="{f(y)}" x2="{f(OX-72)}" y2="{f(y)}" class="edge lead" marker-end="url(#arr)"/>')
        cls = {"S":"st-s","R":"st-r","H":"st-h"}[st]
        out.append(f'<rect x="{f(OX-68)}" y="{f(y-18)}" width="150" height="36" rx="4" class="tout {cls}"/>')
        out.append(f'<text x="{f(OX-58)}" y="{f(y-3)}" class="olbl">{name}</text>')
        out.append(f'<text x="{f(OX-58)}" y="{f(y+12)}" class="orate">{rate} tr/an</text>')
    out.append(f'<text x="{f(cx[0])}" y="{f(ry[1]+34)}" text-anchor="middle" class="elbl">manivelle</text>')
    out.append(f'<text x="{f(cx[1])}" y="{f(ry[1]+34)}" text-anchor="middle" class="elbl">1 tour = 1 an</text>')
    return f'<svg viewBox="0 0 1290 476" role="img" aria-label="Arbre des trains arrière, de la manivelle aux sept cadrans, avec la jonction différentielle sur le plateau e3" class="tree">' + "".join(out) + "</svg>"
