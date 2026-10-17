import pygame, random, math, json, os, struct
from array import array

# COIN RUNNER PRO - self-contained Pygame endless runner
# SPACE/UP/W jump (double jump), DOWN/S slide, P pause, R restart, ESC pause/quit
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512); AUDIO=True
except pygame.error: AUDIO=False
W,H=1000,600; GROUND=485; FPS=60; SAVE='coin_runner_save.json'
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
pygame.display.set_caption("Coin Runner Pro")
clock = pygame.time.Clock()

# Fixed-size canvas for responsive scaling
canvas = pygame.Surface((W, H))
WHITE=(255,255,255); DARK=(28,44,68); GOLD=(255,194,40); BLUE=(55,135,245); PURPLE=(154,95,230); RED=(240,82,83)
FONT=pygame.font.SysFont('arial',22,bold=True); SMALL=pygame.font.SysFont('arial',16,bold=True); BIG=pygame.font.SysFont('arial',48,bold=True); HUGE=pygame.font.SysFont('arial',65,bold=True)
def text(s,t,font,col,pos,center=False):
    im=font.render(str(t),True,col); r=im.get_rect(); r.center=pos if center else r.center
    if center: r.center=pos
    else: r.topleft=pos
    s.blit(im,r)
def sound(freq=600,dur=.08,vol=.2,square=False):
    if not AUDIO:return None
    n=int(22050*dur); a=array('h')
    for i in range(n):
        v=1 if square and math.sin(2*math.pi*freq*i/22050)>=0 else math.sin(2*math.pi*freq*i/22050)
        if square: v=1 if math.sin(2*math.pi*freq*i/22050)>=0 else -1
        a.append(int(32767*vol*(1-i/n)*v))
    return pygame.mixer.Sound(buffer=a.tobytes())
SOUNDS={k:sound(*v) for k,v in {'coin':(950,.07,.17),'jump':(420,.12,.2),'power':(700,.2,.22),'hit':(160,.2,.2,True),'start':(540,.12,.18),'over':(220,.3,.22)}.items()}
def sfx(k):
    if SOUNDS.get(k):
        try:SOUNDS[k].play()
        except pygame.error:pass
def load_best():
    try:return max(0,int(json.load(open(SAVE,encoding='utf8')).get('best_score',0)))
    except (OSError,ValueError,TypeError):return 0
def save_best(n):
    try:
        with open(SAVE,'w',encoding='utf8') as f:json.dump({'best_score':int(n)},f,indent=2)
    except OSError:pass
def panel(s,rect,color=(255,255,255),alpha=225,radius=20):
    p=pygame.Surface((rect[2],rect[3]),pygame.SRCALPHA); pygame.draw.rect(p,(*color,alpha),p.get_rect(),border_radius=radius); pygame.draw.rect(p,(255,255,255,alpha),p.get_rect(),2,border_radius=radius); s.blit(p,rect[:2])
def bg(s,dist):
    for y in range(H):
        t=y/H; pygame.draw.line(s,(int(87*(1-t)+205*t),int(190*(1-t)+239*t),int(255*(1-t)+255*t)),(0,y),(W,y))
    pygame.draw.circle(s,(255,226,110),(835,95),42)
    for i,(cx,cy,sc) in enumerate([(100,100,.8),(360,75,.65),(660,145,.8),(930,65,.7)]):
        x=(cx-int(dist*(.12+i*.02)))%(W+120)-60
        for ox,oy,r in [(0,0,18),(22,-8,24),(48,0,17)]:pygame.draw.circle(s,WHITE,(int(x+ox*sc),int(cy+oy*sc)),int(r*sc))
    shift=int(dist*.18)%260
    for x in range(-300-shift,W+300,260):pygame.draw.ellipse(s,(116,207,164),(x,330,420,180))
    shift=int(dist*.36)%150
    for x in range(-150-shift,W+150,150):
        h=60+((x//150*17)%60); pygame.draw.rect(s,(112,173,204),(x,GROUND-h,90,h))
        for wx in range(x+12,x+80,20):
            for wy in range(GROUND-h+14,GROUND-10,20):pygame.draw.rect(s,(207,235,240),(wx,wy,7,8))
    pygame.draw.rect(s,(72,181,92),(0,GROUND,W,H-GROUND)); pygame.draw.rect(s,(47,151,77),(0,GROUND,W,13)); pygame.draw.rect(s,(225,199,145),(0,GROUND+13,W,H-GROUND-13))
    sh=int(dist*1.2)%80
    for x in range(-80-sh,W+80,80):pygame.draw.line(s,(202,171,119),(x,GROUND+35),(x+35,H),3)
def coin_draw(s,x,y,phase):
    rx=max(3,int(12*abs(math.cos(phase)))); pygame.draw.ellipse(s,(191,123,15),(int(x-rx),int(y-16),rx*2,32)); pygame.draw.ellipse(s,GOLD,(int(x-rx+2),int(y-14),max(2,rx*2-4),28))
    if rx>5:pygame.draw.circle(s,(255,232,115),(int(x),int(y)),3)
def power_draw(s,kind,x,y):
    col={'magnet':PURPLE,'shield':BLUE,'double':(255,145,44)}[kind]; pygame.draw.circle(s,WHITE,(int(x),int(y)),21); pygame.draw.circle(s,col,(int(x),int(y)),18)
    if kind=='double':text(s,'2x',SMALL,WHITE,(x,y),True)
    elif kind=='shield':pygame.draw.polygon(s,WHITE,[(x,y-11),(x+9,y-5),(x+6,y+6),(x,y+12),(x-6,y+6),(x-9,y-5)])
    else:
        pygame.draw.arc(s,WHITE,(x-9,y-10,18,22),math.pi,math.tau,4); pygame.draw.line(s,WHITE,(x-9,y),(x-9,y+7),4); pygame.draw.line(s,WHITE,(x+9,y),(x+9,y+7),4)
def boy(s,x,feet,t,jumping,sliding,shield=False):
    phase=math.sin(t*15); bob=0 if jumping or sliding else int(abs(phase)*3)
    pygame.draw.ellipse(s,(20,50,80),(x-4,feet-7,48,12))
    if sliding:
        pygame.draw.ellipse(s,(35,135,246),(x-3,feet-37,48,25)); pygame.draw.circle(s,(255,202,155),(x+39,feet-31),14); pygame.draw.arc(s,(74,43,29),(x+26,feet-46,27,22),math.pi,math.tau,7); pygame.draw.circle(s,DARK,(x+43,feet-33),2)
    else:
        swing=int(phase*10) if not jumping else -5; by=feet-55+bob
        pygame.draw.line(s,(32,70,135),(x+14,by+30),(x+11+swing,feet-4),8); pygame.draw.line(s,(32,70,135),(x+25,by+30),(x+27-swing,feet-4),8)
        pygame.draw.ellipse(s,(27,40,60),(x+3+swing,feet-7,17,7)); pygame.draw.ellipse(s,(27,40,60),(x+21-swing,feet-7,17,7))
        pygame.draw.ellipse(s,(29,104,213),(x+5,by,31,37)); pygame.draw.rect(s,(35,135,246),(x+8,by+4,25,22),border_radius=8)
        arm=int(phase*7); pygame.draw.line(s,(255,202,155),(x+8,by+12),(x+2-arm,by+24),6); pygame.draw.line(s,(255,202,155),(x+32,by+12),(x+38+arm,by+23),6)
        pygame.draw.rect(s,(235,166,115),(x+17,by-5,10,10),border_radius=3); hy=by-19
        pygame.draw.circle(s,(255,202,155),(x+22,hy),16); pygame.draw.arc(s,(74,43,29),(x+6,hy-17,33,25),math.pi,math.tau,8); pygame.draw.ellipse(s,(74,43,29),(x+7,hy-10,9,11)); pygame.draw.circle(s,DARK,(x+28,hy-1),2); pygame.draw.arc(s,(164,74,60),(x+22,hy+3,9,6),0,math.pi,2); pygame.draw.circle(s,(255,223,87),(x+23,by+12),4)
    if shield:pygame.draw.circle(s,(93,203,255),(x+22,feet-40),44,3)
class Thing:
    def __init__(self,x,y,kind='coin'):
        self.x=float(x);self.y=float(y);self.kind=kind;self.phase=random.random()*math.tau
        if kind=='coin':self.rect=pygame.Rect(0,0,22,30)
        elif kind=='power':self.rect=pygame.Rect(0,0,36,36)
        else:
            self.w,self.h={'crate':(43,48),'spikes':(55,30),'barrier':(52,35)}[kind];self.rect=pygame.Rect(int(x),GROUND-self.h,self.w,self.h)
    def update(self,speed):
        self.x-=speed;self.phase+=.16
        if self.kind in ('coin','power'):self.rect.center=(int(self.x),int(self.y+ (math.sin(self.phase)*4 if self.kind=='power' else 0)))
        else:self.rect.x=int(self.x)
    def draw(self,s):
        if self.kind=='coin':coin_draw(s,self.x,self.y,self.phase)
        elif self.kind=='power':power_draw(s,self.power_kind,self.x,self.y+math.sin(self.phase)*4)
        elif self.kind=='crate':
            pygame.draw.rect(s,(156,92,48),self.rect,border_radius=6);pygame.draw.rect(s,(203,139,75),self.rect.inflate(-10,-10),border_radius=4);pygame.draw.line(s,(127,69,39),self.rect.topleft,self.rect.bottomright,5);pygame.draw.line(s,(127,69,39),self.rect.topright,self.rect.bottomleft,5)
        elif self.kind=='spikes':
            pygame.draw.rect(s,(100,106,122),(self.rect.x,self.rect.bottom-8,self.rect.w,8),border_radius=3)
            for i in range(3):
                x=self.rect.x+i*self.rect.w/3;pygame.draw.polygon(s,(225,66,74),[(x,self.rect.bottom-5),(x+self.rect.w/6,self.rect.y),(x+self.rect.w/3,self.rect.bottom-5)])
        else:
            pygame.draw.rect(s,(75,87,107),self.rect,border_radius=7);pygame.draw.rect(s,(120,140,163),self.rect.inflate(-8,-8),border_radius=5);pygame.draw.circle(s,(255,209,91),self.rect.center,5)
    def off(self):return self.x < -100
class Particle:
    def __init__(self,x,y,col):self.x=x;self.y=y;self.vx=random.uniform(-3,3);self.vy=random.uniform(-4,-1);self.life=random.randint(18,34);self.col=col;self.size=random.randint(2,5)
    def update(self):self.x+=self.vx;self.y+=self.vy;self.vy+=.18;self.life-=1
    def draw(self,s):
        if self.life>0:pygame.draw.circle(s,self.col,(int(self.x),int(self.y)),max(1,self.size*self.life//34))
class Game:
    def __init__(self):self.best=load_best();self.menu_time=0;self.reset();self.state='menu'
    def reset(self):
        self.feet=float(GROUND);self.vy=0;self.jumps=0;self.slide_to=0;self.shield_to=0;self.magnet_to=0;self.double_to=0;self.dist=0;self.score=0;self.coins=0;self.coin_points=0;self.speed=5;self.spawn=65;self.ct=25;self.pt=350;self.obstacles=[];self.items=[];self.particles=[];self.elapsed=0
    def start(self):self.reset();self.state='playing';sfx('start')
    def burst(self,x,y,col,n=9):self.particles += [Particle(x,y,col) for _ in range(n)]
    def jump(self):
        if self.state=='playing' and self.jumps<2 and pygame.time.get_ticks()>self.slide_to:self.vy=-14 if self.jumps==0 else -12;self.jumps+=1;sfx('jump');self.burst(150,self.feet-4,WHITE,5)
    def update(self,dt):
        self.menu_time+=dt;now=pygame.time.get_ticks()
        if self.state=='playing':
            self.elapsed+=dt;self.dist+=self.speed;self.speed=min(12,5+self.elapsed*.055);self.score=int(self.dist/12)+self.coin_points
            if now>self.slide_to:self.vy+=.72;self.feet+=self.vy
            else:self.feet=GROUND
            if self.feet>=GROUND:self.feet=GROUND;self.vy=0;self.jumps=0
            self.spawn-=1
            if self.spawn<=0:
                self.obstacles.append(Thing(W+40,GROUND,random.choices(['crate','spikes','barrier'],[4,3,2])[0]));self.spawn=max(45,random.randint(75,115)-int((self.speed-5)*3))
            self.ct-=1
            if self.ct<=0:
                y=random.choice([GROUND-65,GROUND-105,GROUND-145])
                for i in range(random.randint(4,7)):
                    ob=Thing(W+20+i*34,y);self.items.append(ob)
                self.ct=random.randint(75,120)
            self.pt-=1
            if self.pt<=0:
                p=Thing(W+40,random.choice([GROUND-95,GROUND-135]),'power');p.power_kind=random.choice(['magnet','shield','double']);self.items.append(p);self.pt=random.randint(430,600)
            pr=pygame.Rect(126,int(self.feet)-58,32,54)
            if now<self.slide_to:pr=pygame.Rect(126,GROUND-39,48,32)
            for it in self.items:
                it.update(self.speed)
                if it.kind=='coin' and now<self.magnet_to and abs(it.x-150)<210:it.x-=1.5;it.y+=(self.feet-40-it.y)*.045;it.rect.center=(int(it.x),int(it.y))
                if pr.colliderect(it.rect):
                    if it.kind=='coin':self.coins+=1;self.coin_points+=10*(2 if now<self.double_to else 1);self.burst(it.x,it.y,GOLD,7);it.x=-1000;sfx('coin')
                    elif it.kind=='power':
                        if it.power_kind=='magnet':self.magnet_to=now+7000
                        elif it.power_kind=='shield':self.shield_to=now+8000
                        else:self.double_to=now+8000
                        self.burst(it.x,it.y,{'magnet':PURPLE,'shield':BLUE,'double':(255,145,44)}[it.power_kind],15);it.x=-1000;sfx('power')
            self.items=[i for i in self.items if not i.off()]
            for ob in self.obstacles:
                ob.update(self.speed)
                if pr.colliderect(ob.rect):
                    if now<self.shield_to:self.shield_to=0;ob.x=-1000;self.burst(ob.rect.centerx,ob.rect.centery,BLUE,15);sfx('hit')
                    else:self.state='gameover';sfx('over');self.best=max(self.best,self.score);save_best(self.best);break
            self.obstacles=[o for o in self.obstacles if not o.off()]
        for p in self.particles:p.update()
        self.particles=[p for p in self.particles if p.life>0]
        self.best=max(self.best,self.score)
    def hud(self,s):
        now=pygame.time.get_ticks();panel(s,(18,16,240,74));text(s,'SCORE',SMALL,(87,103,124),(34,25));text(s,self.score,BIG,DARK,(32,42))
        panel(s,(275,16,185,58));text(s,'COINS',SMALL,(87,103,124),(293,23));text(s,self.coins,FONT,DARK,(293,43))
        panel(s,(W-220,16,202,58));text(s,'BEST',SMALL,(87,103,124),(W-202,23));text(s,self.best,FONT,DARK,(W-202,43))
        active=[]
        if now<self.magnet_to:active.append(('MAGNET',self.magnet_to-now,PURPLE))
        if now<self.shield_to:active.append(('SHIELD',self.shield_to-now,BLUE))
        if now<self.double_to:active.append(('2X COINS',self.double_to-now,(255,145,44)))
        for i,(label,rem,col) in enumerate(active):pygame.draw.rect(s,col,(18+i*165,101,150,29),border_radius=12);text(s,f'{label} {math.ceil(rem/1000)}s',SMALL,WHITE,(93+i*165,115),True)
        text(s,'SPACE/UP: jump & double jump    DOWN: slide    P: pause',SMALL,(41,75,94),(W//2,H-26),True)
    def draw(self,s):
        bg(s,self.dist)
        for i in range(7):pygame.draw.circle(s,WHITE,((i*173-int(self.dist*.5))%W,235+int(math.sin(self.menu_time*2+i)*13)),2)
        for it in self.items:it.draw(s)
        for ob in self.obstacles:ob.draw(s)
        for p in self.particles:p.draw(s)
        if self.state in ('playing','paused','gameover'):
            boy(s,130,int(self.feet),self.menu_time,self.feet<GROUND,pygame.time.get_ticks()<self.slide_to and self.state=='playing',pygame.time.get_ticks()<self.shield_to);self.hud(s)
        if self.state=='menu':
            panel(s,(205,105,590,350));text(s,'COIN RUNNER',HUGE,(35,104,204),(W//2,165),True);text(s,'PRO EDITION',FONT,(255,151,36),(W//2,215),True);text(s,'Run  •  Jump  •  Collect  •  Power up!',FONT,DARK,(W//2,265),True);text(s,'SPACE / ENTER to start',FONT,(39,133,78),(W//2,315),True);text(s,'SPACE/UP: double jump  |  DOWN: slide',SMALL,(72,91,110),(W//2,352),True);text(s,'Magnet • Shield • Double coins',SMALL,(72,91,110),(W//2,378),True);text(s,f'PERSONAL BEST  {self.best}',SMALL,(35,104,204),(W//2,417),True);boy(s,135,GROUND,self.menu_time,False,False)
        elif self.state=='paused':
            panel(s,(300,205,400,170),(24,42,64),235);text(s,'PAUSED',BIG,WHITE,(W//2,250),True);text(s,'Press P or SPACE to continue',FONT,(220,236,250),(W//2,315),True)
        elif self.state=='gameover':
            panel(s,(270,145,460,310));text(s,'GAME OVER',BIG,RED,(W//2,195),True);text(s,f'Score: {self.score}',FONT,DARK,(W//2,255),True);text(s,f'Coins collected: {self.coins}',FONT,DARK,(W//2,292),True);text(s,f'Best score: {self.best}',FONT,(35,104,204),(W//2,329),True);text(s,'ENTER / SPACE / R to play again',FONT,(39,133,78),(W//2,385),True);text(s,'ESC to quit',SMALL,(95,108,120),(W//2,420),True)
def main():
    global screen

    g = Game()
    running = True
    g=Game();running=True
    while running:
        dt=clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (max(640, e.w), max(400, e.h)),
                    pygame.RESIZABLE
                )
            if e.type==pygame.QUIT:running=False
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    if g.state=='playing':g.state='paused'
                    elif g.state=='paused':g.state='playing'
                    else:running=False
                elif g.state=='menu' and e.key in (pygame.K_SPACE,pygame.K_RETURN,pygame.K_UP,pygame.K_w):g.start()
                elif g.state=='gameover' and e.key in (pygame.K_SPACE,pygame.K_RETURN,pygame.K_r):g.start()
                elif g.state=='paused' and e.key in (pygame.K_p,pygame.K_SPACE,pygame.K_RETURN):g.state='playing'
                elif g.state=='playing':
                    if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w):g.jump()
                    elif e.key in (pygame.K_DOWN,pygame.K_s):g.slide_to=pygame.time.get_ticks()+650
                    elif e.key==pygame.K_p:g.state='paused'
                    elif e.key==pygame.K_r:g.start()
        g.update(dt)
        g.draw(canvas)

        # Current window size
        sw, sh = screen.get_size()

        # Maintain game proportions
        scale = min(sw / W, sh / H)
        new_w = int(W * scale)
        new_h = int(H * scale)

        # Resize the rendered game
        scaled_game = pygame.transform.smoothscale(
            canvas, (new_w, new_h)
        )

        # Draw centered in the window
        screen.fill((20, 30, 45))
        screen.blit(
            scaled_game,
            ((sw - new_w) // 2, (sh - new_h) // 2)
        )

        pygame.display.flip()
    save_best(max(g.best,g.score));pygame.quit()
if __name__=='__main__':main()
